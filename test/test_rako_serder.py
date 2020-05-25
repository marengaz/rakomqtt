import unittest

from rakomqtt.RakoBridge import RakoStatusMessage, RakoCommandType, RakoBridge
from rakomqtt.model import mqtt_payload_schema


class TestRakoWatching(unittest.TestCase):
    """
    Testing Status updates from the Rako Bridge
    """

    deserialise_bytelist_cases = [
        # name, in, expected
        ("base level", [83, 7, 0, 13, 1, 12, 42, 42, 136], RakoStatusMessage(13,1,RakoCommandType.LEVEL_SET_LEGACY,None,42)),
        ("diff brightness", [83, 7, 0, 13, 1, 12, 16, 16, 136], RakoStatusMessage(13,1,RakoCommandType.LEVEL_SET_LEGACY,None,16)),
        ("diff room channel", [83, 7, 0, 10, 2, 12, 16, 16, 136], RakoStatusMessage(10,2,RakoCommandType.LEVEL_SET_LEGACY,None,16)),
        ("set scene base", [83, 5, 0, 13, 0, 6, 237], RakoStatusMessage(13,0,RakoCommandType.SC4_LEGACY,4,64)),
        ("diff scene", [83, 5, 0, 13, 0, 4, 239], RakoStatusMessage(13,0,RakoCommandType.SC2_LEGACY,2,192)),
        ("diff room", [83, 5, 0, 21, 0, 6, 229], RakoStatusMessage(21,0,RakoCommandType.SC4_LEGACY,4,64)),
        ("room off", [83, 5, 0, 21, 0, 0, 235], RakoStatusMessage(21,0,RakoCommandType.OFF,0,0)),
    ]

    def test_deserialise_status_msg(self):
        for test_name, in_bytes, exp_obj in self.deserialise_bytelist_cases:
            with self.subTest(test_name):
                payload_result = RakoStatusMessage.from_byte_list(in_bytes)
                self.assertEqual(payload_result, exp_obj)


    create_topic_payload_cases = [
        # name, in, exp_topic, exp_payload
        ("base level", RakoStatusMessage(13,1,RakoCommandType.LEVEL_SET_LEGACY,None,42), 'rako/room/13/channel/1', dict(state='ON', brightness=42)),
        ("diff brightness", RakoStatusMessage(13,1,RakoCommandType.LEVEL_SET_LEGACY,None,16), 'rako/room/13/channel/1', dict(state='ON', brightness=16)),
        ("diff room channel", RakoStatusMessage(10,2,RakoCommandType.LEVEL_SET_LEGACY,None,16), 'rako/room/10/channel/2', dict(state='ON', brightness=16)),
        ("level off", RakoStatusMessage(10,2,RakoCommandType.LEVEL_SET_LEGACY,None,0), 'rako/room/10/channel/2', dict(state='OFF', brightness=0)),
        ("set scene base", RakoStatusMessage(13,0,RakoCommandType.SC4_LEGACY,4,64), 'rako/room/13', dict(state='ON', brightness=64)),
        ("diff scene", RakoStatusMessage(13,0,RakoCommandType.SC2_LEGACY,2,192), 'rako/room/13', dict(state='ON', brightness=192)),
        ("diff room", RakoStatusMessage(21,0,RakoCommandType.SC4_LEGACY,4,64), 'rako/room/21', dict(state='ON', brightness=64)),
        ("room off", RakoStatusMessage(21,0,RakoCommandType.OFF,0,0), 'rako/room/21', dict(state='OFF', brightness=0)),
    ]

    def test_create_topic_payload(self):
        for test_name, in_msg, exp_topic, exp_payload in self.create_topic_payload_cases:
            with self.subTest(test_name):
                topic_result = RakoBridge.create_topic(in_msg)
                self.assertEqual(topic_result, exp_topic)
                payload_result = RakoBridge.create_payload(in_msg)
                self.assertEqual(payload_result, exp_payload)




