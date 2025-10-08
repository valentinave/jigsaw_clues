"""Shared helpers for Raspberry Pi clue players."""
from __future__ import annotations

import logging
import queue
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import paho.mqtt.client as mqtt
import tkinter as tk
import tkinter.font as tkfont

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MessageEvent:
    text: str
    duration: float


class TextOverlay:
    """Simple full-screen text display driven by a queue."""

    def __init__(self, *, background: str = "black", foreground: str = "white") -> None:
        self._queue: queue.Queue[MessageEvent | None] = queue.Queue()
        self._root = tk.Tk()
        self._root.attributes("-fullscreen", True)
        self._root.configure(bg=background)
        self._root.bind("<Escape>", lambda _: self._root.quit())
        width = self._root.winfo_screenwidth()
        base_font = tkfont.Font(family="Helvetica", size=max(48, width // 20), weight="bold")
        self._label = tk.Label(
            self._root,
            text="",
            fg=foreground,
            bg=background,
            font=base_font,
            wraplength=width - 200,
            justify="center",
        )
        self._label.pack(expand=True, fill="both", padx=40, pady=40)
        self._hide_after: float | None = None
        self._root.after(100, self._poll)

    def show(self, text: str, duration: float = 30.0) -> None:
        self._queue.put(MessageEvent(text=text, duration=duration))

    def hide(self) -> None:
        self._queue.put(None)

    def shutdown(self) -> None:
        """Exit the Tk main loop."""
        try:
            if self._root.winfo_exists():
                self._root.quit()
        except tk.TclError:  # pragma: no cover - teardown safety
            pass

    def run(self) -> None:
        logger.info("Starting overlay loop")
        self._root.mainloop()

    def _poll(self) -> None:
        try:
            while True:
                event = self._queue.get_nowait()
                if event is None:
                    logger.info("Clearing on-screen message")
                    self._label.config(text="")
                    self._hide_after = None
                else:
                    logger.info("Displaying message: %s", event.text)
                    self._label.config(text=event.text)
                    self._hide_after = time.time() + event.duration
        except queue.Empty:
            pass

        if self._hide_after and time.time() >= self._hide_after:
            logger.info("Message timeout reached, hiding")
            self._label.config(text="")
            self._hide_after = None

        self._root.after(100, self._poll)


class VideoPlayer:
    """Launches fullscreen video playback with cvlc or omxplayer."""

    def __init__(self, videos: Mapping[str, Path], *, command: Iterable[str] | None = None) -> None:
        self._videos = videos
        self._command = list(command) if command else ["cvlc", "--fullscreen", "--play-and-exit"]
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    def play(self, video_id: str) -> None:
        video_path = self._videos.get(video_id)
        if not video_path:
            logger.warning("Received unknown video id %s", video_id)
            return
        if not video_path.exists():
            logger.error("Video file missing: %s", video_path)
            return
        with self._lock:
            self.stop()
            logger.info("Playing %s", video_path)
            try:
                self._process = subprocess.Popen([*self._command, str(video_path)])
            except FileNotFoundError:
                logger.exception("Video player command not found: %s", self._command[0])
            except Exception:  # pragma: no cover - subprocess errors
                logger.exception("Failed to start video player")

    def stop(self) -> None:
        with self._lock:
            if self._process and self._process.poll() is None:
                logger.info("Stopping current video")
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            self._process = None


class PiClient:
    """MQTT listener that bridges messages to local playback."""

    def __init__(
        self,
        *,
        device_key: str,
        mqtt_prefix: str,
        video_map: Mapping[str, Path],
        mqtt_host: str | None = None,
        mqtt_port: int | None = None,
    ) -> None:
        settings = get_settings()
        self._mqtt_host = mqtt_host or settings.mqtt_host
        self._mqtt_port = mqtt_port or settings.mqtt_port
        self._prefix = mqtt_prefix.rstrip("/")
        self._client = mqtt.Client(client_id=f"jigsaw-{device_key}")
        self._player = VideoPlayer(video_map)
        self._overlay = TextOverlay()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._stopping = threading.Event()

    def start(self) -> None:
        logger.info("Connecting to MQTT at %s:%s", self._mqtt_host, self._mqtt_port)
        self._client.connect(self._mqtt_host, self._mqtt_port, keepalive=60)
        self._client.loop_start()
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        try:
            self._overlay.run()
        finally:
            self.stop()

    def stop(self) -> None:
        if self._stopping.is_set():
            return
        self._stopping.set()
        logger.info("Stopping Pi client")
        self._player.stop()
        self._overlay.shutdown()
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:  # pragma: no cover - shutdown safety
            logger.exception("Error while disconnecting MQTT client")

    # MQTT callbacks -----------------------------------------------------

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc) -> None:  # pragma: no cover - callback
        if rc != 0:
            logger.error("MQTT connection failed with code %s", rc)
            return
        logger.info("Connected to MQTT broker")
        client.subscribe(f"{self._prefix}/video/play")
        client.subscribe(f"{self._prefix}/text/send")

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:  # pragma: no cover - callback
        topic = msg.topic
        payload = msg.payload.decode(errors="ignore").strip()
        logger.info("Received MQTT message on %s: %s", topic, payload)
        if topic.endswith("/video/play"):
            if payload:
                self._player.play(payload)
        elif topic.endswith("/text/send"):
            if payload:
                self._overlay.show(payload)
            else:
                self._overlay.hide()

    def _handle_signal(self, signum, frame) -> None:  # pragma: no cover - signal handler
        logger.info("Received signal %s, shutting down", signum)
        self.stop()
