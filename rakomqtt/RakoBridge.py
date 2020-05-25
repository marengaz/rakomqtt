import logging
import re
import socket
import requests
from enum import Enum
from dataclasses import dataclass
from urllib3.exceptions import HTTPError

from rakomqtt.model import mqtt_payload_schema


_LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 5


class RakoCommandType(Enum):
    OFF = 0
    SC1_LEGACY = 3
    SC2_LEGACY = 4
    SC3_LEGACY = 5
    SC4_LEGACY = 6
    LEVEL_SET_LEGACY = 12
    SET_SCENE = 49
    SET_LEVEL = 52


SCENE_NUMBER_TO_COMMAND = {
    1: RakoCommandType.SC1_LEGACY,
    2: RakoCommandType.SC2_LEGACY,
    3: RakoCommandType.SC3_LEGACY,
    4: RakoCommandType.SC4_LEGACY,
    0: RakoCommandType.OFF
}
SCENE_COMMAND_TO_NUMBER = {v: k for k, v in SCENE_NUMBER_TO_COMMAND.items()}


class RakoDeserialisationException(Exception):
    pass


@dataclass
class RakoStatusMessage:
    room: int
    channel: int
    command: RakoCommandType
    scene: int = None
    brightness: int = None

    @classmethod
    def from_byte_list(cls, byte_list):
        if chr(byte_list[0]) != 'S':
            raise RakoDeserialisationException(f'Unsupported UDP message type: {chr(byte_list[0])}')

        data_length = byte_list[1] - 5
        room = byte_list[3]
        channel = byte_list[4]
        command = RakoCommandType(byte_list[5])
        data = byte_list[6:6 + data_length]

        if command in (RakoCommandType.LEVEL_SET_LEGACY, RakoCommandType.SET_LEVEL):
            return cls(
                room=room,
                channel=channel,
                command=RakoCommandType.SET_LEVEL,
                brightness=data[1],
            )
        else:
            if command == RakoCommandType.SET_SCENE:
                scene = data[1]
            else:
                scene = SCENE_COMMAND_TO_NUMBER[command]

            return cls(
                room=room,
                channel=channel,
                command=RakoCommandType.SET_SCENE,
                scene=scene,
                brightness=cls._scene_brightness(scene),
            )

    @staticmethod
    def _scene_brightness(rako_scene_number):
        scene_brightness = {
            # rako_scene_number: brightness
            1: 255,
            2: 192,
            3: 128,
            4: 64,
            0: 0,
        }

        return scene_brightness[rako_scene_number]


@dataclass
class RakoCommand:
    room: int
    channel: int
    scene: int = None
    brightness: int = None

    @classmethod
    def from_mqtt(cls, topic, payload_str):
        m_scene = re.match('^rako/room/([0-9]+)/set$', topic)
        m_level = re.match('^rako/room/([0-9]+)/channel/([0-9]+)/set$', topic)
        if m_scene:
            room_id = int(m_scene.group(1))
            payload = mqtt_payload_schema.loads(payload_str)

            return cls(
                room=room_id,
                channel=0,
                scene=cls._rako_command(payload['brightness']),
            )
        elif m_level:
            room_id = int(m_level.group(1))
            channel = int(m_level.group(2))
            payload = mqtt_payload_schema.loads(payload_str)

            return cls(
                room=room_id,
                channel=channel,
                brightness=payload['brightness'],
            )
        else:
            _LOGGER.debug(f"Topic unrecognised ${topic}")
            return

    @staticmethod
    def _rako_command(brightness):
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


class RakoBridge:
    # for devices http://192.168.0.10/rako.xml
    port = 9761

    def __init__(self, host=None):
        self.host = host if host else self.find_bridge()
        self._url = 'http://{}/rako.cgi'.format(self.host)

    @classmethod
    def find_bridge(cls):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(DEFAULT_TIMEOUT)

        resp = cls.poll_for_bridge_response(sock)
        if resp:
            _, (host, _) = resp
            _LOGGER.debug(f'found rako bridge at {host}')
            return host
        else:
            _LOGGER.error('Cannot find a rakobrige')
            exit(1)

    @classmethod
    def poll_for_bridge_response(cls, sock):
        # bind to the default ip address using a system provided ephemeral port
        sock.bind(('', 0))
        i = 1
        while i <= 3:
            _LOGGER.debug("Broadcasting to try and find rako bridge...")
            sock.sendto(b'D', ('255.255.255.255', cls.port))
            try:
                resp = sock.recvfrom(256)
                _LOGGER.debug(resp)
                return resp
            except socket.timeout:
                _LOGGER.debug(f"No rako bridge found on try #{i}")
                i = i + 1

    def post_command(self, rako_command: RakoCommand):
        if rako_command.scene:
            payload = {
                'room': rako_command.room,
                'ch': rako_command.channel,
                'sc': rako_command.scene,
            }
        else:
            payload = {
                'room': rako_command.room,
                'ch': rako_command.channel,
                'lev': rako_command.brightness,
            }

        try:
            _LOGGER.debug('payload {}'.format(payload))
            requests.post(self._url, params=payload, timeout=DEFAULT_TIMEOUT)
        except HTTPError:
            _LOGGER.error(f"Can't turn on {self._url}. Is resource/endpoint offline?")

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

        try:
            rako_status_message = RakoStatusMessage.from_byte_list(byte_list)
        except (RakoDeserialisationException, ValueError, IndexError) as ex:
            _LOGGER.debug(f'unhandled bytestring: {ex}')
            return

        topic = cls.create_topic(rako_status_message)
        payload = cls.create_payload(rako_status_message)

        return topic, payload

    @staticmethod
    def create_topic(rako_status_message: RakoStatusMessage):
        if rako_status_message.command == RakoCommandType.SET_LEVEL:
            return f"rako/room/{rako_status_message.room}/channel/{rako_status_message.channel}"
        else:
            return f"rako/room/{rako_status_message.room}"

    @staticmethod
    def create_payload(rako_status_message: RakoStatusMessage):
        return dict(state=('ON' if rako_status_message.brightness else 'OFF'), brightness=rako_status_message.brightness)


if __name__ == '__main__':
    print(RakoBridge().host)
