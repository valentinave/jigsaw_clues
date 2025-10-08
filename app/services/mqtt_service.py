from __future__ import annotations

import logging
from typing import Iterable

import paho.mqtt.client as mqtt

from ..config import DeviceConfig, Settings, get_settings

logger = logging.getLogger(__name__)


class MqttService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = mqtt.Client()
        if self.settings.mqtt_username and self.settings.mqtt_password:
            self._client.username_pw_set(self.settings.mqtt_username, self.settings.mqtt_password)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        try:
            self._client.connect(self.settings.mqtt_host, self.settings.mqtt_port, 60)
            self._client.loop_start()
        except Exception:  # pragma: no cover - network environment dependent
            logger.exception("Failed to connect to MQTT broker")

    def stop(self) -> None:
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:  # pragma: no cover
            logger.exception("Error stopping MQTT client")

    def publish(self, device: DeviceConfig, kind: str, payload: str) -> None:
        topic = device.topic_for(kind)
        try:
            self._client.publish(topic, payload)
            logger.info("MQTT publish %s → %s", topic, payload)
        except Exception:  # pragma: no cover
            logger.exception("Failed to publish MQTT message")

    def publish_multi(self, devices: Iterable[DeviceConfig], kind: str, payload: str) -> None:
        for device in devices:
            self.publish(device, kind, payload)

    @staticmethod
    def _on_connect(client: mqtt.Client, userdata, flags, rc):  # pragma: no cover - callback
        if rc == 0:
            logger.info("Connected to MQTT broker")
        else:
            logger.error("MQTT connection failed with code %s", rc)

    @staticmethod
    def _on_disconnect(client: mqtt.Client, userdata, rc):  # pragma: no cover - callback
        logger.info("MQTT disconnected (%s)", rc)
