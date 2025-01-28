"""CLI for ComfyPack LitServe implementation."""
import logging
from typing import Optional

import typer
from rich.logging import RichHandler

from ..schema import ComfyPackSettings
from .server import create_server

# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("comfy_pack.litserve")

def main(
    # Server Configuration
    host: str = typer.Option(
        "0.0.0.0",
        help="Host to bind to"
    ),
    port: int = typer.Option(
        8000,
        help="Port to bind to"
    ),
    
    # Resource Configuration
    workers: int = typer.Option(
        1,
        help="Number of worker processes per device"
    ),
    gpu: bool = typer.Option(
        True,
        help="Enable GPU acceleration"
    ),
    batch_size: int = typer.Option(
        1,
        help="Maximum batch size for inference"
    ),
    timeout: float = typer.Option(
        300.0,
        help="Request timeout in seconds"
    ),
    
    # Feature Flags
    stream: bool = typer.Option(
        False,
        help="Enable streaming responses"
    ),
    track_requests: bool = typer.Option(
        True,
        help="Enable request tracking"
    ),
    
    # Logging
    verbose: bool = typer.Option(
        False,
        help="Enable verbose logging"
    ),
    
    # ComfyUI Configuration
    comfyui_url: Optional[str] = typer.Option(
        None,
        help="URL of external ComfyUI server"
    )
) -> None:
    """Start the ComfyPack LitServe server."""
    # Configure settings
    settings = ComfyPackSettings(
        host=host,
        port=port,
        gpu_enabled=gpu,
        max_batch_size=batch_size,
        verbose=verbose,
        comfyui_server_url=comfyui_url
    )
    
    # Set log level
    log_level = "DEBUG" if verbose else "INFO"
    logging.getLogger("comfy_pack").setLevel(log_level)
    
    logger.info("Starting ComfyPack LitServe server...")
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Workers: {workers}")
    logger.info(f"GPU Enabled: {settings.gpu_enabled}")
    logger.info(f"Batch Size: {settings.max_batch_size}")
    logger.info(f"Timeout: {timeout}s")
    logger.info(f"Streaming: {stream}")
    logger.info(f"Request Tracking: {track_requests}")
    
    # Create and start server
    server = create_server(
        settings,
        workers=workers,
        timeout=timeout,
        stream=stream,
        track_requests=track_requests
    )
    
    # Run server
    server.run(
        host=settings.host,
        port=settings.port
    )

app = typer.Typer()
app.command()(main)

if __name__ == "__main__":
    app()
