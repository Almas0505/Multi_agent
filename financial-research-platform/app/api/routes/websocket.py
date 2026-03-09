"""WebSocket route for real-time analysis progress streaming."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.services.cache import CacheService

router = APIRouter()


@router.websocket("/ws/analysis/{task_id}")
async def analysis_websocket(websocket: WebSocket, task_id: str) -> None:
    """Stream analysis progress updates over a WebSocket connection.

    Polls Redis every second and sends JSON messages until the task
    reaches a terminal state (completed / failed) or the client disconnects.
    """
    cache = CacheService()
    await websocket.accept()
    logger.info(f"WebSocket connection opened for task {task_id}")

    try:
        while True:
            progress = await cache.get_progress(task_id)
            if progress:
                message = {
                    "agent": progress.get("agent", "unknown"),
                    "status": progress.get("status", "running"),
                    "progress": progress.get("progress", 0),
                    "message": progress.get("message", ""),
                }
                await websocket.send_text(json.dumps(message))

                if message["status"] in ("completed", "failed"):
                    logger.info(f"Task {task_id} finished – closing WebSocket.")
                    break
            else:
                await websocket.send_text(
                    json.dumps(
                        {
                            "agent": "unknown",
                            "status": "waiting",
                            "progress": 0,
                            "message": "Waiting for task to start…",
                        }
                    )
                )
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as exc:
        logger.error(f"WebSocket error for task {task_id}: {exc}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
