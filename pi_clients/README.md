# Raspberry Pi Clue Players

Each Raspberry Pi in the experience listens to MQTT topics and either plays a video clue or shows a text message on its local display. This folder ships a lightweight client that you can run on every Pi.

## Prerequisites

- Copy the entire repository to the Pi.
- Place the MP4 assets under the `assets/` directory, preserving the folder names (`boiler room`, `hol intrare`, etc.).
- Install the Python dependencies (a small venv per Pi is recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ..  # installs the shared project dependencies
```

`cvlc` must also be available for fullscreen playback (preinstalled on Raspberry Pi OS with VLC).

## Running

Use the `run_client.py` helper to start the correct profile. The client automatically reads the MQTT broker host/port from `app/config.py`, but you can override them via flags if needed.

```bash
python -m pi_clients.run_client boilerroom
```

Available device profiles:

- `boilerroom` – covers Boiler Room and Small Room videos (topic prefix `boiler/…`).
- `holintrare` – plays Hol Intrare and Hall Room videos (topic prefix `hall/…`).
- `lastroom` – plays Jigsaw and Last Room videos (topic prefix `last/…`).

To run the clients persistently, create a `systemd` service on each Pi that executes the command above inside its virtual environment. When the control UI triggers a clue, the Pi will immediately start VLC fullscreen; text clues fade automatically after 30 seconds.

## Text overlay

Text messages sent from the control room appear on a full-screen overlay with white text on a black background. Pressing `Esc` on the Pi keyboard will close the client in case you need to exit the kiosk view manually.

## Customisation

- Adjust the default video command by editing `VideoPlayer` in `pi_clients/common.py` (for example to use `omxplayer`).
- Change the asset folder mapping in `pi_clients/device_profiles.py` if you relocate the media files.
- To tweak message duration, update `TextOverlay.show()` or change the call in the MQTT handler.

