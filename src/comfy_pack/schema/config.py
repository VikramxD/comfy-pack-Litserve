"""Configuration schema for ComfyPack."""
from pathlib import Path
from typing import Optional
from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings

class ComfyPackSettings(BaseSettings):
    """Global settings for ComfyPack."""
    
    # Workspace Configuration
    workspace_root: Path = Field(
        Path("/tmp/comfy_workspace"),
        description="Root directory for workspaces"
    )
    input_dir: Path = Field(
        Path("/tmp/comfy_input"),
        description="Directory for input files"
    )
    model_cache_dir: Path = Field(
        Path("/tmp/comfy_models"),
        description="Directory for cached models"
    )
    
    # Server Configuration
    host: str = Field("0.0.0.0", description="Server host address")
    port: int = Field(8000, description="Server port")
    request_timeout: int = Field(3600, description="Request timeout in seconds")
    
    # GPU Configuration
    gpu_enabled: bool = Field(True, description="Enable GPU acceleration")
    max_batch_size: int = Field(1, description="Maximum batch size for inference")
    
    # Logging Configuration
    verbose: bool = Field(False, description="Enable verbose logging")
    log_level: str = Field("INFO", description="Logging level")
    
    # ComfyUI Server Configuration
    comfyui_server_url: Optional[str] = Field(
        None,
        description="External ComfyUI server URL. If None, will start a local server"
    )
    
    class Config:
        env_prefix = "COMFY_"
        case_sensitive = False
