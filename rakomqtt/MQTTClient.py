import logging

import paho.mqtt.client as mqtt


_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, host, user, pwd):
        self.mqttc = mqtt.Client()
        self.mqttc.enable_logger()
        self.host = host
        self.user = user
        self.pwd = pwd

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                _LOGGER.info(f"Unexpected MQTT disconnection. rc = {rc}. Will auto-reconnect")

        self.mqttc.on_disconnect = on_disconnect
        self.mqttc.username_pw_set(self.user, self.pwd)
        self.mqttc.reconnect_delay_set()

    def publish(self, topic, payload=None, qos=0, retain=False):
        (rc, message_id) = self.mqttc.publish(topic, payload, qos, retain)
        _LOGGER.debug(f"published to {topic}: {payload}. response: {(rc, message_id)}")

    def connect(self):
        self.mqttc.connect(self.host, 1883, 60)

