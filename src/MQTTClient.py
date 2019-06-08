import paho.mqtt.client as mqtt

from src.AppConfig import app_config
from src.logger import logger


class MQTTClient:
    def __init__(self):
        self.mqttc = mqtt.Client()
        self.mqttc.enable_logger()

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                logger.info(f"Unexpected MQTT disconnection. rc = {rc}. Will auto-reconnect")

        self.mqttc.on_disconnect = on_disconnect
        self.mqttc.username_pw_set(app_config.mqtt_user, app_config.mqtt_pwd)
        self.mqttc.reconnect_delay_set()

    def publish(self, topic, payload=None, qos=0, retain=False):
        (rc, message_id) = self.mqttc.publish(topic, payload, qos, retain)
        logger.debug(f"published to {topic}: {payload}. response: {(rc, message_id)}")

    def connect(self):
        self.mqttc.connect(app_config.mqtt_host, 1883, 60)

