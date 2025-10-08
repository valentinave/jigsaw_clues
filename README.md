# Jigsaw Control

Modern control surface for the Jigsaw escape room network. The application exposes a FastAPI backend with a responsive, dark-mode web UI to control room timers, send video or text clues, and keep track of puzzle status across Raspberry Pi devices.

## Features

- Real-time WebSocket updates for timer, puzzle status, and activity log.
- Timer controls with quick adjustments and manual set input.
- Per-room puzzle dashboard with buttons to trigger video clues, toggle solved state, and adjust hint counters.
- Text clue sender with device selectors to target individual Raspberry Pis.
- MQTT integration with configurable topics and broker host.

## Project layout

```
app/
├── config.py          # Environment configuration & MQTT topic helpers
├── core/
│   ├── state.py       # In-memory state store and timers
│   ├── timer.py       # Countdown timer helper
│   └── websocket_manager.py
├── data.py            # Room/puzzle catalogue and default targets
├── main.py            # FastAPI application factory & routes
├── models/
│   └── game.py        # Game metadata and state dataclasses
├── services/
│   └── mqtt_service.py
├── static/
│   ├── app.js         # Front-end logic
│   └── style.css      # Dark glassmorphism theme
└── templates/
    └── index.html     # UI shell
```

## Running locally

Install dependencies and start the server.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:create_app --reload
```

Open http://localhost:8000 in a browser. Update `app/config.py` if your MQTT broker host or topic structure differs.

## Deployment on Raspberry Pi

### Control interface (Hol Intrare Pi)

1. Copy the repository to the Hol Intrare Pi (the one hosting the web app).
2. Create a Python virtual environment and install dependencies as above.
3. Configure a systemd service pointing to `uvicorn app.main:create_app` to keep the control room available on boot.

### Clue players (Boiler Room / Hol Intrare / Last Room Pis)

Each Pi that plays videos or shows text clues runs the lightweight client in `pi_clients/`:

```bash
python -m pi_clients.run_client boilerroom   # or holintrare / lastroom
```

The client connects to the MQTT broker configured in `app/config.py`, listens for `/video/play` and `/text/send` topics under its prefix, launches VLC fullscreen for videos, and displays text messages on a dark overlay. See `pi_clients/README.md` for detailed setup steps and customization notes.

The UI is designed for large touch displays with dim light conditions and should render crisply on Chromium-based kiosk browsers.
