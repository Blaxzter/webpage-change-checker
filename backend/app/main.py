import asyncio
import logging
import os
from contextlib import asynccontextmanager
import inspect

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from fastapi import Request

from app.api.api import api_router
from app.core.config import settings


# Global variables to hold the monitoring service and task
monitoring_service = None
monitoring_task = None


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler to manage monitoring service"""
    global monitoring_service, monitoring_task

    # Check if monitoring should be enabled
    enable_monitoring = os.getenv("ENABLE_MONITORING", "false").lower() == "true"

    if enable_monitoring:
        print("🔍 Starting Website Monitoring Service...")
        try:
            from app.logic.website_checker import WebsiteMonitorService

            monitoring_service = WebsiteMonitorService(check_interval_seconds=60)

            # Start monitoring in background task
            monitoring_task = asyncio.create_task(monitoring_service.start())
            print("✅ Website Monitoring Service started")
        except Exception as e:
            print(f"❌ Failed to start monitoring service: {e}")
            monitoring_service = None
    else:
        print(
            "ℹ️  Website Monitoring Service disabled (set ENABLE_MONITORING=true to enable)"
        )

    yield  # Application runs here

    # Cleanup
    if monitoring_service:
        print("🛑 Stopping Website Monitoring Service...")
        try:
            await monitoring_service.stop()
            print("✅ Website Monitoring Service stopped")
        except Exception as e:
            print(f"❌ Error stopping monitoring service: {e}")

    if monitoring_task and not monitoring_task.done():
        print("🛑 Cancelling monitoring task...")
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            print("✅ Monitoring task cancelled")


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    import sentry_sdk

    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


def custom_openapi():
    """
    Custom OpenAPI function to add HTTPException schema
    This allows us to generate a frontend client with the HTTPException schema for type safe error handling
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    # Add HTTPException schema
    # Add HTTPException schema
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}

    openapi_schema["components"]["schemas"]["HTTPException"] = {
        "type": "object",
        "properties": {"detail": {"type": "string"}},
        "required": ["detail"],
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

app.openapi = custom_openapi

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/HTTPException"}
                }
            },
        },
    },
)

middleware_logger = logging.getLogger("middleware")
ignore_paths = ["/openapi.json", "/oapi/live"]


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Get the route handler function
    route_handler = None
    for route in request.app.routes:
        # Check if the route has a path_regex and if it matches the current path
        if (
            hasattr(route, "path_regex")
            and hasattr(request, "url")
            and request.url is not None
            and route.path_regex.match(request.url.path)
            and hasattr(route, "methods")
            and hasattr(request, "method")
            and request.method in route.methods
        ):
            route_handler = route.endpoint
            break

    # Get handler location info
    if route_handler:
        # Get the actual function if it's wrapped
        while hasattr(route_handler, "__wrapped__"):
            route_handler = route_handler.__wrapped__

        # Get the absolute file path and convert to standard format
        route_handler_module = inspect.getmodule(route_handler)
        if route_handler_module:
            file_path = route_handler_module.__file__.replace("\\", "/")
        else:
            file_path = "unknown location"

        # Find the 'app' directory in the path and get everything after it
        if "/app/" in file_path:
            relative_path = "app/" + file_path.split("/app/")[1]
        else:
            relative_path = file_path

        line_number = inspect.getsourcelines(route_handler)[1]
        location = f"{relative_path}:{line_number}"
    else:
        location = "unknown location"

    # do not print options requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Log request with handler location
    if (
        hasattr(request, "method")
        and hasattr(request, "url")
        and hasattr(request.url, "path")
        and request.url.path not in ignore_paths
    ):
        # check request.method path legth and pad it with spaces to 5 characters
        request_method = request.method.ljust(5)
        middleware_logger.info(
            f"Request {request_method} {request.url.path} - Handler at {location}"
        )

    response = await call_next(request)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True,
    )
