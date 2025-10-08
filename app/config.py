from __future__ import annotations

from functools import lru_cache
from pydantic import BaseModel, Field


class MqttTopicMap(BaseModel):
    video: str = Field(default="video/play")
    text: str = Field(default="text/send")
    status: str = Field(default="status/update")


class DeviceConfig(BaseModel):
    name: str
    label: str
    mqtt_prefix: str
    topics: MqttTopicMap = Field(default_factory=MqttTopicMap)

    def topic_for(self, kind: str) -> str:
        topic = getattr(self.topics, kind)
        if topic.startswith("/"):
            return f"{self.mqtt_prefix}{topic}"
        return f"{self.mqtt_prefix}/{topic}".rstrip("/")


class Settings(BaseModel):
    mqtt_host: str = Field(default="192.168.1.217", description="MQTT broker host")
    mqtt_port: int = Field(default=1883, description="MQTT broker port")
    mqtt_username: str | None = Field(default=None, description="Optional MQTT username")
    mqtt_password: str | None = Field(default=None, description="Optional MQTT password")
    allow_cross_origin: bool = Field(default=True, description="Enable CORS for the UI")

    devices: dict[str, DeviceConfig] = Field(
        default_factory=lambda: {
            "boilerroom": DeviceConfig(name="boilerroom", label="Boiler Room", mqtt_prefix="boiler"),
            "lastroom": DeviceConfig(name="lastroom", label="Last Room", mqtt_prefix="last"),
            "holintrare": DeviceConfig(name="holintrare", label="Hol Intrare", mqtt_prefix="hall"),
        }
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
