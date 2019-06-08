import paho.mqtt.client as mqtt

from src.AppConfig import app_config
from src.logger import logger


class MQTTClient:
    def __init__(self):
        self.mqttc = mqtt.Client()
        self.mqttc.enable_logger()
        self.mqttc.username_pw_set(app_config.mqtt_user, app_config.mqtt_pwd)
        self.mqttc.reconnect_delay_set()

    def publish(self, topic, payload=None, qos=0, retain=False):
        ret = self.mqttc.publish(topic, payload, qos, retain)
        logger.debug(f"published to {topic}: {payload}. response: {ret}")

    def connect(self):
        self.mqttc.connect(app_config.mqtt_host, 1883, 60)
