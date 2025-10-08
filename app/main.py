from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, model_validator

from .config import DeviceConfig, Settings, get_settings
from .core.state import AppState
from .core.websocket_manager import WebSocketManager
from .services.mqtt_service import MqttService

BASE_DIR = Path(__file__).resolve().parent


class TimerControlRequest(BaseModel):
    action: Literal["start", "pause", "reset", "set", "add"]
    value: int | None = Field(default=None, description="Value in seconds")


class SolveRequest(BaseModel):
    solved: bool


class HintRequest(BaseModel):
    delta: int | None = Field(default=None, description="Increment hints by delta")
    value: int | None = Field(default=None, description="Override hints count")

    @model_validator(mode="after")
    def _validate(cls, values: "HintRequest") -> "HintRequest":  # noqa: N805
        if values.delta is None and values.value is None:
            raise ValueError("Either delta or value must be provided")
        if values.delta is not None and values.value is not None:
            raise ValueError("Provide either delta or value, not both")
        return values


class VideoRequest(BaseModel):
    game_id: str
    targets: list[str] | None = Field(default=None, description="Target device keys")


class MessageRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Message to send")
    targets: list[str] = Field(default_factory=list, description="Target device keys")


class ApiContext(BaseModel):
    settings: Settings
    state: AppState
    mqtt: MqttService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    ws_manager = WebSocketManager()
    state = AppState(ws_manager)
    mqtt = MqttService(settings)

    app = FastAPI(title="Jigsaw Control", version="0.1.0")

    if settings.allow_cross_origin:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.state.ws_manager = ws_manager
    app.state.app_state = state
    app.state.mqtt = mqtt
    app.state.timer_task = None

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - lifecycle
        mqtt.start()
        app.state.timer_task = asyncio.create_task(state.timer_tick_loop())

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover - lifecycle
        if app.state.timer_task:
            app.state.timer_task.cancel()
        mqtt.stop()

    async def get_context() -> ApiContext:
        return ApiContext(settings=settings, state=state, mqtt=mqtt)

    @app.get("/", response_class=FileResponse)
    async def index() -> FileResponse:
        return FileResponse(BASE_DIR / "templates" / "index.html")

    @app.get("/api/state")
    async def get_state(ctx: ApiContext = Depends(get_context)) -> JSONResponse:
        data = await ctx.state.full_state()
        data["devices"] = _devices_summary(settings)
        data["mqtt_host"] = settings.mqtt_host
        return JSONResponse(data)

    @app.post("/api/timer/control")
    async def timer_control(payload: TimerControlRequest, ctx: ApiContext = Depends(get_context)) -> JSONResponse:
        value = payload.value
        if payload.action in {"set", "add"} and value is None:
            raise HTTPException(status_code=400, detail="value is required for this action")
        if payload.action == "reset":
            value = value or 0
        snapshot = await ctx.state.timer_action(payload.action, value)
        return JSONResponse({"timer": snapshot.formatted, "running": snapshot.running})

    @app.post("/api/puzzles/{puzzle_id}/solve")
    async def solve_puzzle(puzzle_id: str, payload: SolveRequest, ctx: ApiContext = Depends(get_context)) -> JSONResponse:
        try:
            data = await ctx.state.mark_solved(puzzle_id, payload.solved)
        except KeyError:
            raise HTTPException(status_code=404, detail="Puzzle not found") from None
        return JSONResponse(data)

    @app.post("/api/puzzles/{puzzle_id}/hints")
    async def update_hints(puzzle_id: str, payload: HintRequest, ctx: ApiContext = Depends(get_context)) -> JSONResponse:
        try:
            if payload.value is not None:
                data = await ctx.state.set_hints(puzzle_id, payload.value)
            else:
                delta = payload.delta or 0
                if delta == 0:
                    raise HTTPException(status_code=400, detail="delta cannot be zero")
                data = await ctx.state.increment_hint(puzzle_id, delta)
        except KeyError:
            raise HTTPException(status_code=404, detail="Puzzle not found") from None
        return JSONResponse(data)

    @app.post("/api/video")
    async def play_video(payload: VideoRequest, ctx: ApiContext = Depends(get_context)) -> JSONResponse:
        try:
            game_state = ctx.state.game_state(payload.game_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Game not found") from None

        targets = payload.targets or list(game_state.game.default_targets)
        devices = _resolve_devices(settings, targets)
        if not devices:
            raise HTTPException(status_code=400, detail="No valid targets provided")

        ctx.mqtt.publish_multi(devices, "video", game_state.game.video)
        ctx.state.add_log(
            f"Video {game_state.game.video} sent to {', '.join(device.label for device in devices)}",
            kind="action",
        )
        return JSONResponse({"status": "ok"})

    @app.post("/api/messages")
    async def send_message(payload: MessageRequest, ctx: ApiContext = Depends(get_context)) -> JSONResponse:
        targets = payload.targets or list(settings.devices.keys())
        devices = _resolve_devices(settings, targets)
        if not devices:
            raise HTTPException(status_code=400, detail="No valid targets provided")

        ctx.mqtt.publish_multi(devices, "text", payload.text)
        ctx.state.add_log(
            f"Message sent to {', '.join(device.label for device in devices)}: {payload.text}",
            kind="message",
        )
        return JSONResponse({"status": "ok"})

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, ctx: ApiContext = Depends(get_context)) -> None:
        await app.state.ws_manager.connect(websocket)
        try:
            full_state = await ctx.state.full_state()
            full_state["devices"] = _devices_summary(settings)
            full_state["mqtt_host"] = settings.mqtt_host
            await websocket.send_json({"type": "state", "data": full_state})
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await app.state.ws_manager.disconnect(websocket)

    return app


def _resolve_devices(settings: Settings, keys: list[str]) -> list[DeviceConfig]:
    devices: list[DeviceConfig] = []
    for key in keys:
        device = settings.devices.get(key)
        if device:
            devices.append(device)
    return devices


def _devices_summary(settings: Settings) -> dict[str, dict[str, str]]:
    return {key: {"label": device.label} for key, device in settings.devices.items()}
