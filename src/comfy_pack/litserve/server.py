"""Server factory for ComfyPack LitServe implementation."""
import logging
from typing import Any, Callable, Dict, List, Optional, Union

import litserve as ls
from litserve.server import LitServer

from ..schema import ComfyPackSettings
from .api import ComfyLitAPI

logger = logging.getLogger("comfy_pack.litserve")

def create_server(
    settings: Optional[ComfyPackSettings] = None,
    workers: int = 1,
    timeout: Union[float, bool] = 300.0,
    stream: bool = False,
    track_requests: bool = True,
    callbacks: Optional[List[Callable]] = None,
    middlewares: Optional[List[Union[Callable, tuple[Callable, dict]]]] = None,
    loggers: Optional[List[logging.Logger]] = None,
    **kwargs: Any,
) -> LitServer:
    """Create a LitServe server instance.
    
    Args:
        settings: ComfyPack settings
        workers: Number of worker processes per device
        timeout: Request timeout in seconds, or False for no timeout
        stream: Enable streaming responses
        track_requests: Enable request tracking
        callbacks: Server callbacks
        middlewares: Server middleware functions
        loggers: Additional loggers
        **kwargs: Additional arguments to pass to LitServer
        
    Returns:
        LitServer: Configured server instance
    """
    settings = settings or ComfyPackSettings()
    
    # Create API instance
    api = ComfyLitAPI(settings)
    
    # Configure server
    server_kwargs = {
        # Device configuration
        "accelerator": "auto" if settings.gpu_enabled else "cpu",
        "devices": "auto",
        "workers_per_device": workers,
        
        # Request handling
        "timeout": timeout,
        "max_batch_size": settings.max_batch_size,
        "batch_timeout": 0.0,  # No batching delay
        "max_payload_size": None,  # No size limit
        
        # API paths
        "api_path": "/predict",
        "healthcheck_path": "/health",
        "info_path": "/info",
        
        # Features
        "stream": stream,
        "track_requests": track_requests,
        "fast_queue": True,  # Use fast queue for better performance
        
        # Extensions
        "callbacks": callbacks,
        "middlewares": middlewares,
        "loggers": loggers,
        
        # Model metadata
        "model_metadata": {
            "name": "comfy-pack",
            "version": "1.0.0",
            "description": "ComfyUI workflow executor",
            "gpu_enabled": settings.gpu_enabled,
            "max_batch_size": settings.max_batch_size,
        },
        
        # Additional settings
        **kwargs
    }
    
    # Create server
    logger.info("Creating LitServe server...")
    logger.debug("Server configuration: %s", server_kwargs)
    
    server = ls.LitServer(api, **server_kwargs)
    
    return server
