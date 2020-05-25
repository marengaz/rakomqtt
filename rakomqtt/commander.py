import logging
import paho.mqtt.client as mqtt

from rakomqtt.MQTTClient import MQTTClient
from rakomqtt.RakoBridge import RakoBridge, RakoCommand


_LOGGER = logging.getLogger(__name__)


def run_commander(rako_bridge_host, mqtt_host, mqtt_user, mqtt_password):
    rako_bridge = RakoBridge(rako_bridge_host)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        _LOGGER.info("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        result, mid = client.subscribe([
            ("rako/room/+/set", 1),
            ("rako/room/+/channel/+/set", 1),
        ])
        if result != mqtt.MQTT_ERR_SUCCESS:
            _LOGGER.error("Couldn't subscribe to mqtt topics. Commander ain't gonna work")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg: mqtt.MQTTMessage):
        rako_command = RakoCommand.from_mqtt(msg.topic, str(msg.payload.decode("utf-8")))

        if rako_command:
            rako_bridge.post_command(rako_command)

    mqttc = MQTTClient(mqtt_host, mqtt_user, mqtt_password)
    mqttc.mqttc.on_connect = on_connect
    mqttc.mqttc.on_message = on_message
    mqttc.connect()
    mqttc.mqttc.loop_forever()


