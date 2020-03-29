import json
import unittest

from rakomqtt.model import mqtt_payload_schema


class TestMarshmallowModels(unittest.TestCase):

    deserialise_mqtt_payload_cases = [
        # name, in str, expected dict
        ("standard", json.dumps({"state": "OFF", "brightness": 25}), {"state": "OFF", "brightness": 25}),
        ("missing_brightness_off", json.dumps({"state": "OFF"}), {"state": "OFF", "brightness": 0}),
        ("missing_brightness_on", json.dumps({"state": "ON"}), {"state": "ON", "brightness": 255}),
    ]

    def test_deserialise_mqtt_payload(self):
        for test_name, in_str, exp_dict in self.deserialise_mqtt_payload_cases:
            with self.subTest(test_name):
                payload_result = mqtt_payload_schema.loads(in_str)
                self.assertEqual(payload_result, exp_dict)


