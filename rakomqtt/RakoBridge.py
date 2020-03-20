import logging
import socket
import requests


_LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 10


class RakoBridge:
    # for devices http://192.168.0.10/rako.xml
    port = 9761
    _timeout = DEFAULT_TIMEOUT
    scene_to_scene_command = {
        1: 3, 2: 4, 3: 5, 4: 6, 0: 0
    }
    scene_command_to_scene = {v: k for k, v in scene_to_scene_command.items()}

    def __init__(self):
        self._host = self.find_bridge()
        self._url = 'http://{}/rako.cgi'.format(self._host)

    @classmethod
    def find_bridge(cls):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # bind to the default ip address using a system provided ephemeral port
        sock.bind(('', 0))
        _LOGGER.debug("Broadcasting to try and find rako bridge...")
        sock.sendto(b'D', ('255.255.255.255', cls.port))
        resp = sock.recvfrom(256)
        _LOGGER.debug(resp)
        if resp:
            _, (host, _) = resp
            _LOGGER.debug(f'found rako bridge at {host}')
            return host
        else:
            _LOGGER.error('Cannot find a rakobrige')

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
            _LOGGER.debug('payload {}'.format(payload))
            requests.post(self._url, params=payload, timeout=self._timeout)
        except Exception as ex:
            _LOGGER.error("Can't turn on %s. Is resource/endpoint offline?", self._url)

    @property
    def found_bridge(self):
        return bool(self._url)

    @classmethod
    def process_udp_bytes(cls, byte_list):
        """
        see accessing-the-rako-bridge.pdf for decoding
        :param byte_list: List(Int)
        :return (topic: str, mqtt_payload: dict)
        """
        _LOGGER.debug(f'received byte_list: {byte_list}')
        if byte_list[0] != 83:
            _LOGGER.debug('not a status update - ignore')
            return

        if byte_list[1] == 7:
            if byte_list[5] != 49:
                _LOGGER.debug('not a SET_SCENE command - ignore')
                return
            topic, payload = cls.process_set_scene_bytes(byte_list)
        elif byte_list[1] == 5:
            if not (3 <= byte_list[5] <= 6) and byte_list[5] != 0:
                _LOGGER.debug('not a SET_SCENE number command - ignore')
                return
            topic, payload = cls.process_set_scene_number_bytes(byte_list)
        else:
            _LOGGER.debug('unhandled bytestring length - ignore')
            return

        return topic, payload

    @classmethod
    def process_set_scene_number_bytes(cls, byte_list):
        room_id = byte_list[3]
        scene_command = byte_list[5]
        scene_id = cls.scene_command_to_scene[scene_command]
        brightness = cls._rako_brightness(scene_id)
        return cls.create_topic(room_id), cls.create_payload(brightness)

    @classmethod
    def process_set_scene_bytes(cls, byte_list):
        room_id = byte_list[3]
        scene_id = byte_list[7]
        brightness = cls._rako_brightness(scene_id)
        return cls.create_topic(room_id), cls.create_payload(brightness)

    @staticmethod
    def create_topic(room_id):
        return f"rako/room/{room_id}"

    @staticmethod
    def create_payload(brightness):
        return dict(state=('ON' if brightness else 'OFF'), brightness=brightness)
