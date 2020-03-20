import json
import logging
import socket

from rakomqtt.MQTTClient import MQTTClient
from rakomqtt.RakoBridge import RakoBridge


_LOGGER = logging.getLogger(__name__)


def run_watcher(mqtt_host, mqtt_user, mqtt_password):
    udp_sock = _connect_udp_socket(RakoBridge.port)
    mqtt_client = _connect_mqtt(mqtt_host, mqtt_user, mqtt_password)

    _listen(udp_sock, mqtt_client)


def _connect_mqtt(mqtt_host, mqtt_user, mqtt_password):
    mqttc = MQTTClient(mqtt_host, mqtt_user, mqtt_password)
    mqttc.connect()
    mqttc.mqttc.loop_start()
    return mqttc


def _connect_udp_socket(rako_bridge_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _LOGGER.info(f"Listening on udp port: {rako_bridge_port}")
    s.bind(("", rako_bridge_port))
    return s


def _listen(udp_sock, mqtt_client):
    while True:
        resp = udp_sock.recvfrom(256)
        if resp:
            byte_list = list(resp[0])
            processed_bytes = RakoBridge.process_udp_bytes(byte_list)
            if not processed_bytes:
                continue
            topic, mqtt_payload = processed_bytes
            mqtt_client.publish(topic, json.dumps(mqtt_payload))
