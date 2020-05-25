# flake8: noqa
import json
import unittest

from rakomqtt.RakoBridge import RakoStatusMessage, RakoCommandType, RakoBridge, RakoCommand


class TestRakoWatching(unittest.TestCase):
    """
    Testing Status updates from the Rako Bridge
    """

    deserialise_bytelist_cases = [
        # name, in, expected
        ("base level legacy", [83, 7, 0, 13, 1, 12, 42, 42, 136], RakoStatusMessage(13, 1, RakoCommandType.SET_LEVEL, None, 42)),
        ("base level", [83, 7, 0, 5, 1, 52, 1, 255, 198], RakoStatusMessage(5, 1, RakoCommandType.SET_LEVEL, None, 255)),
        ("diff brightness legacy", [83, 7, 0, 13, 1, 12, 16, 16, 136], RakoStatusMessage(13, 1, RakoCommandType.SET_LEVEL, None, 16)),
        ("diff room channel legacy", [83, 7, 0, 10, 2, 12, 16, 16, 136], RakoStatusMessage(10, 2, RakoCommandType.SET_LEVEL, None, 16)),
        ("scene base legacy", [83, 5, 0, 13, 0, 6, 237], RakoStatusMessage(13, 0, RakoCommandType.SET_SCENE, 4, 64)),
        ("base scene", [83, 7, 0, 17, 0, 49, 0, 2, 188], RakoStatusMessage(17, 0, RakoCommandType.SET_SCENE, 2, 192)),
        ("diff scene legacy", [83, 5, 0, 13, 0, 4, 239], RakoStatusMessage(13, 0, RakoCommandType.SET_SCENE, 2, 192)),
        ("diff room legacy", [83, 5, 0, 21, 0, 6, 229], RakoStatusMessage(21, 0, RakoCommandType.SET_SCENE, 4, 64)),
        ("room off", [83, 5, 0, 21, 0, 0, 235], RakoStatusMessage(21, 0, RakoCommandType.SET_SCENE, 0, 0)),
    ]

    def test_deserialise_status_msg(self):
        for test_name, in_bytes, exp_obj in self.deserialise_bytelist_cases:
            with self.subTest(test_name):
                payload_result = RakoStatusMessage.from_byte_list(in_bytes)
                self.assertEqual(payload_result, exp_obj)

    create_topic_payload_cases = [
        # name, in, exp_topic, exp_payload
        ("base level", RakoStatusMessage(13, 1, RakoCommandType.SET_LEVEL, None, 42), 'rako/room/13/channel/1', dict(state='ON', brightness=42)),
        ("diff brightness", RakoStatusMessage(13, 1, RakoCommandType.SET_LEVEL, None, 16), 'rako/room/13/channel/1', dict(state='ON', brightness=16)),
        ("diff room channel", RakoStatusMessage(10, 2, RakoCommandType.SET_LEVEL, None, 16), 'rako/room/10/channel/2', dict(state='ON', brightness=16)),
        ("level off", RakoStatusMessage(10, 2, RakoCommandType.SET_LEVEL, None, 0), 'rako/room/10/channel/2', dict(state='OFF', brightness=0)),
        ("set scene base", RakoStatusMessage(13, 0, RakoCommandType.SET_SCENE, 4, 64), 'rako/room/13', dict(state='ON', brightness=64)),
        ("diff scene", RakoStatusMessage(13, 0, RakoCommandType.SET_SCENE, 2, 192), 'rako/room/13', dict(state='ON', brightness=192)),
        ("diff room", RakoStatusMessage(21, 0, RakoCommandType.SET_SCENE, 4, 64), 'rako/room/21', dict(state='ON', brightness=64)),
        ("room off", RakoStatusMessage(21, 0, RakoCommandType.OFF, 0, 0), 'rako/room/21', dict(state='OFF', brightness=0)),
    ]

    def test_create_topic_payload(self):
        for test_name, in_msg, exp_topic, exp_payload in self.create_topic_payload_cases:
            with self.subTest(test_name):
                topic_result = RakoBridge.create_topic(in_msg)
                self.assertEqual(topic_result, exp_topic)
                payload_result = RakoBridge.create_payload(in_msg)
                self.assertEqual(payload_result, exp_payload)


class TestRakoCommanding(unittest.TestCase):
    """
    Testing commands from mqtt are properly interpreted
    """
    deserialise_topic_payload = [
        # name, in_topic, in_payload, expected
        ("base level", 'rako/room/13/channel/1/set', json.dumps({"state": "ON", "brightness": 25}), RakoCommand(13, 1, None, 25)),
        ("diff room channel", 'rako/room/5/channel/42/set', json.dumps({"state": "ON", "brightness": 25}), RakoCommand(5, 42, None, 25)),
        ("diff level", 'rako/room/5/channel/42/set', json.dumps({"state": "ON", "brightness": 90}), RakoCommand(5, 42, None, 90)),
        ("scene base", 'rako/room/5/set', json.dumps({"state": "ON", "brightness": 90}), RakoCommand(5, 0, 4, None)),
        ("diff scene", 'rako/room/5/set', json.dumps({"state": "ON", "brightness": 100}), RakoCommand(5, 0, 3, None)),
        ("diff room", 'rako/room/9/set', json.dumps({"state": "ON", "brightness": 100}), RakoCommand(9, 0, 3, None)),
    ]

    def test_deserialise_topic_payload(self):
        for name, in_topic, in_payload, expected in self.deserialise_topic_payload:
            with self.subTest(name):
                cmd_result = RakoCommand.from_mqtt(in_topic, in_payload)
                self.assertEqual(cmd_result, expected)
