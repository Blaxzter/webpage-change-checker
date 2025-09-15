# app/api/routes/monitoring.py
"""
API routes for manual monitoring service management.
This allows starting/stopping the monitoring service via API calls.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.logic.threaded_monitor import threaded_monitor_service

router = APIRouter()


@router.post("/monitoring/start")
async def start_monitoring() -> Dict[str, Any]:
    """Start the website monitoring service manually."""
    try:
        if threaded_monitor_service.running:
            return {
                "success": False,
                "message": "Monitoring service is already running",
                "status": "running",
            }

        threaded_monitor_service.start()

        return {
            "success": True,
            "message": "Website monitoring service started successfully",
            "status": "running",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start monitoring service: {str(e)}"
        )


@router.post("/monitoring/stop")
async def stop_monitoring() -> Dict[str, Any]:
    """Stop the website monitoring service manually."""
    try:
        if not threaded_monitor_service.running:
            return {
                "success": False,
                "message": "Monitoring service is not running",
                "status": "stopped",
            }

        threaded_monitor_service.stop()

        return {
            "success": True,
            "message": "Website monitoring service stopped successfully",
            "status": "stopped",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop monitoring service: {str(e)}"
        )


@router.get("/monitoring/status")
async def get_monitoring_status() -> Dict[str, Any]:
    """Get the current status of the monitoring service."""
    return {
        "running": threaded_monitor_service.running,
        "status": "running" if threaded_monitor_service.running else "stopped",
        "thread_alive": (
            threaded_monitor_service.thread.is_alive()
            if threaded_monitor_service.thread
            else False
        ),
        "check_interval": threaded_monitor_service.check_interval_seconds,
    }


@router.post("/monitoring/restart")
async def restart_monitoring() -> Dict[str, Any]:
    """Restart the website monitoring service."""
    try:
        # Stop if running
        if threaded_monitor_service.running:
            threaded_monitor_service.stop()

        # Start again
        threaded_monitor_service.start()

        return {
            "success": True,
            "message": "Website monitoring service restarted successfully",
            "status": "running",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to restart monitoring service: {str(e)}"
        )

