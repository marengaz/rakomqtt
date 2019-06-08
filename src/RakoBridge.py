import json
import socket
import requests

from src.MQTTClient import MQTTClient
from src.logger import logger


DEFAULT_TIMEOUT = 10


class RakoBridge(object):
    # for devices http://192.168.0.10/rako.xml
    _port = 9761
    _timeout = DEFAULT_TIMEOUT

    def __init__(self):
        super(RakoBridge, self).__init__()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # bind to the default ip address using a system provided ephemeral port
        sock.bind(('', 0))

        logger.debug("Broadcasting to find rako bridge")
        sock.sendto(b'D', ('255.255.255.255', self._port))
        resp = sock.recvfrom(256)
        logger.debug(resp)
        if resp:
            _, (self._host, _) = resp
            self._url = 'http://{}/rako.cgi'.format(self._host)
            logger.debug(f'found rako bridge at {self._host}')
        else:
            logger.error('Cannot find a rakobrige')

    scene_to_scene_command = {
        1: 3, 2: 4, 3: 5, 4: 6, 0: 0
    }
    scene_command_to_scene = {v: k for k, v in scene_to_scene_command.items()}

    @staticmethod
    def _rako_scene(brightness):
        """Return the rako scene of the light. This directly corresponds
        to the value of the button on the app and is accessed through the
        brightness

        :param brightness: int representing brightness 0-255
        """

        scene_windows = {
            # rako_scene: (brightness_high, brightness_low)
            1: dict(low=224, high=256),  # expect 255 (100%)
            2: dict(low=160, high=224),  # expect 192 (75%)
            3: dict(low=96, high=160),  # expect 128 (50%)
            4: dict(low=1, high=96),  # expect 64 (25%)
            0: dict(low=0, high=1),  # expect 0 (0%)
        }

        scene = [k for k, v in scene_windows.items() if v['low'] <= brightness < v['high']]
        return scene[0]

    @staticmethod
    def _rako_brightness(scene):

        scene_brightness = {
            # rako_scene: brightness
            1: 255,
            2: 192,
            3: 128,
            4: 64,
            0: 0,
        }

        return scene_brightness[scene]

    def post_scene(self, room_id, brightness):
        scene = self._rako_scene(brightness)
        payload = {
            'room': room_id,
            'ch': 0,
            'com': self.scene_to_scene_command[scene]
        }

        try:
            logger.debug('payload {}'.format(payload))
            requests.post(self._url, params=payload, timeout=self._timeout)
        except Exception as ex:
            logger.error("Can't turn on %s. Is resource/endpoint offline?", self._url)

    @property
    def found_bridge(self):
        return bool(self._url)

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        logger.info("Listening on udp %s:%s" % (self._host, self._port))
        s.bind(("", self._port))

        mqttc = MQTTClient()
        mqttc.connect()
        mqttc.mqttc.loop_start()

        while True:
            resp = s.recvfrom(256)
            if resp:
                byte_list = list(resp[0])
                processed_bytes = self.process_udp_bytes(byte_list)
                if not processed_bytes:
                    continue
                topic, mqtt_payload = processed_bytes
                mqttc.publish(topic, json.dumps(mqtt_payload))

    def process_udp_bytes(self, byte_list):
        """
        see accessing-the-rako-bridge.pdf for decoding
        :param byte_list: List(Int)
        :return (topic: str, mqtt_payload: dict)
        """
        logger.debug(f'received byte_list: {byte_list}')
        if byte_list[0] != 83:
            logger.debug('not a status update - ignore')
            return

        if byte_list[1] == 7:
            if byte_list[5] != 49:
                logger.debug('not a SET_SCENE command - ignore')
                return
            topic, payload = self.process_set_scene_bytes(byte_list)
        elif byte_list[1] == 5:
            if not (3 <= byte_list[5] <= 6) and byte_list[5] != 0:
                logger.debug('not a SET_SCENE number command - ignore')
                return
            topic, payload = self.process_set_scene_number_bytes(byte_list)
        else:
            logger.debug('unhandled bytestring length - ignore')
            return

        return topic, payload

    def process_set_scene_number_bytes(self, byte_list):
        room_id = byte_list[3]
        scene_command = byte_list[5]
        scene_id = self.scene_command_to_scene[scene_command]
        brightness = self._rako_brightness(scene_id)
        return self.create_topic(room_id), self.create_payload(brightness)

    def process_set_scene_bytes(self, byte_list):
        room_id = byte_list[3]
        scene_id = byte_list[7]
        brightness = self._rako_brightness(scene_id)
        return self.create_topic(room_id), self.create_payload(brightness)

    @staticmethod
    def create_topic(room_id):
        return f"rako/room/{room_id}"

    @staticmethod
    def create_payload(brightness):
        return dict(state=('ON' if brightness else 'OFF'), brightness=brightness)
