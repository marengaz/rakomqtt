import logging
import re

import paho.mqtt.client as mqtt

from rakomqtt import serder
from rakomqtt.MQTTClient import MQTTClient
from rakomqtt.RakoBridge import RakoBridge
from rakomqtt.model import mqtt_payload_schema


_LOGGER = logging.getLogger(__name__)


def run_commander(rako_bridge_host, mqtt_host, mqtt_user, mqtt_password):
    rako_bridge = RakoBridge(rako_bridge_host)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        _LOGGER.info("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("rako/room/+/set")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg: mqtt.MQTTMessage):
        m = re.match('^rako/room/([0-9]+)/set$', msg.topic)
        if not m:
            _LOGGER.debug(f"Topic unrecognised ${msg.topic}")
            return

        room_id = int(m.group(1))
        payload_str = str(msg.payload.decode("utf-8"))
        payload = serder.deserialise(mqtt_payload_schema, payload_str)
        rako_bridge.post_scene(room_id, payload['brightness'])

    mqttc = MQTTClient(mqtt_host, mqtt_user, mqtt_password)
    mqttc.mqttc.on_connect = on_connect
    mqttc.mqttc.on_message = on_message
    mqttc.connect()
    mqttc.mqttc.loop_forever()


