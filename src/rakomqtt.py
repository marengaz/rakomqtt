#!/usr/bin/python
import re

import paho.mqtt.client as mqtt
from marshmallow import Schema, fields, post_load, validate

from src import serder
from src.AppConfig import app_config
from src.MQTTClient import MQTTClient
from src.RakoBridge import RakoBridge
from src.logger import logger


class PayloadSchema(Schema):
    state = fields.Str(validate=validate.OneOf(choices=('ON', 'OFF')))
    brightness = fields.Int(validate=validate.Range(min=0, max=255))

    @post_load
    def post_load(self, item):
        if item.get('brightness') is None and item['state'] == 'ON':
            item['brightness'] = 255
        if item.get('brightness') is None and item['state'] == 'OFF':
            item['brightness'] = 0


payload_schema = PayloadSchema()


def run_state_watcher(rako_bridge: RakoBridge):
    rako_bridge.listen()


def run_commander(rako_bridge: RakoBridge):
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        logger.info("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("rako/room/+/set")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg: mqtt.MQTTMessage):
        m = re.match('^rako/room/([0-9]+)/set$', msg.topic)
        if not m:
            logger.debug(f"Topic unrecognised ${msg.topic}")
            return

        room__id = int(m.group(1))
        payload_str = str(msg.payload.decode("utf-8"))
        payload = serder.deserialise(payload_schema, payload_str)
        rako_bridge.post_scene(room__id, payload['brightness'])

    mqttc = MQTTClient()
    mqttc.mqttc.on_connect = on_connect
    mqttc.mqttc.on_message = on_message
    mqttc.connect()
    mqttc.mqttc.loop_forever()


def run():
    br = RakoBridge()
    logger.debug(f'Running the rakomqtt {app_config.mode}')
    if app_config.mode == "state_watcher":
        run_state_watcher(br)
    if app_config.mode == "commander":
        run_commander(br)


if __name__ == '__main__':
    run()





