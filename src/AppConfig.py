import os


class AppConfig:
    def __init__(self):
        self.mode = os.environ.get('APP_MODE', 'commander')
        self.mqtt_host = os.environ['MOSQUITTO_HOST']
        self.mqtt_user = os.environ['MOSQUITTO_USER']
        self.mqtt_pwd = os.environ['MOSQUITTO_PASSWORD']


app_config = AppConfig()
