"""Command line entry point to launch a clue player on a Raspberry Pi."""
from __future__ import annotations

import argparse
import logging

from .common import PiClient
from .device_profiles import get_device_profiles

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Jigsaw clue player")
    parser.add_argument(
        "device",
        choices=sorted(get_device_profiles().keys()),
        help="Which device profile to run (boilerroom, holintrare, lastroom)",
    )
    parser.add_argument("--mqtt-host", dest="mqtt_host", help="Override MQTT host")
    parser.add_argument("--mqtt-port", dest="mqtt_port", type=int, help="Override MQTT port")
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format=LOG_FORMAT)
    profiles = get_device_profiles()
    profile = profiles[args.device]

    client = PiClient(
        device_key=profile.key,
        mqtt_prefix=profile.mqtt_prefix,
        video_map=profile.video_map,
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
    )

    client.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
