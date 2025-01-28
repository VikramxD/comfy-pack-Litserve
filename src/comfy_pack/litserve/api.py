"""LitServe API implementation for ComfyPack."""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import litserve as ls
from pydantic import ValidationError

from ..schema import (
    ComfyPackSettings,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowValidationError,
)
from ..core import ComfyUIServer, execute_remote_workflow, run

logger = logging.getLogger("comfy_pack.litserve")

class ComfyLitAPI(ls.LitAPI):
    """LitServe implementation of the ComfyUI workflow executor."""
    
    def __init__(self, settings: Optional[ComfyPackSettings] = None):
        super().__init__()
        self.settings = settings or ComfyPackSettings()
        self.server = None
        
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        logger.info("Creating required directories...")
        self.settings.workspace_root.mkdir(parents=True, exist_ok=True)
        self.settings.input_dir.mkdir(parents=True, exist_ok=True)
        self.settings.model_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def setup(self, device: str) -> None:
        """Initialize ComfyUI server and resources.
        
        Args:
            device: Device to use for computation (e.g., 'cpu', 'cuda:0')
        """
        # Create directories first
        self._ensure_directories()
        
        if self.settings.comfyui_server_url:
            logger.info(f"Using external ComfyUI server at {self.settings.comfyui_server_url}")
            return
            
        logger.info("Starting local ComfyUI server...")
        self.server = ComfyUIServer(
            str(self.settings.workspace_root),
            str(self.settings.input_dir),
            verbose=int(self.settings.verbose)
        )
        self.server.start()
        logger.info(
            "ComfyUI Server started at %s:%s", 
            self.server.host, 
            self.server.port
        )
    
    def decode_request(self, request: Dict[str, Any]) -> WorkflowExecutionRequest:
        """Convert raw request to WorkflowExecutionRequest.
        
        Args:
            request: Raw request data
            
        Returns:
            WorkflowExecutionRequest: Validated request object
            
        Raises:
            ValidationError: If request validation fails
        """
        try:
            return WorkflowExecutionRequest(**request)
        except ValidationError as e:
            errors = [
                WorkflowValidationError(
                    loc=err["loc"],
                    msg=err["msg"],
                    type=err["type"]
                )
                for err in e.errors()
            ]
            raise ValueError({"errors": errors})
    
    def predict(self, request: WorkflowExecutionRequest) -> Dict[str, Any]:
        """Execute the workflow.
        
        Args:
            request: Validated workflow execution request
            
        Returns:
            Dict containing the execution results
            
        Raises:
            RuntimeError: If workflow execution fails
        """
        try:
            if self.settings.comfyui_server_url:
                # Use external server
                result = execute_remote_workflow(
                    self.settings.comfyui_server_url,
                    request.workflow_id,
                    request.inputs,
                    request.session_id
                )
            else:
                # Use local server
                result = self.server.execute_workflow(
                    request.workflow_id,
                    request.inputs,
                    request.session_id
                )
            
            return {
                "session_id": request.session_id,
                "status": "completed",
                "outputs": result,
                "metadata": {
                    "workflow_id": request.workflow_id,
                    **(request.metadata.dict() if request.metadata else {})
                }
            }
        except Exception as e:
            logger.exception("Workflow execution failed")
            return {
                "session_id": request.session_id,
                "status": "failed",
                "outputs": {},
                "error": str(e),
                "metadata": {
                    "workflow_id": request.workflow_id,
                    **(request.metadata.dict() if request.metadata else {})
                }
            }
    
    def encode_response(
        self, 
        output: Dict[str, Any]
    ) -> WorkflowExecutionResponse:
        """Convert raw output to WorkflowExecutionResponse.
        
        Args:
            output: Raw output data
            
        Returns:
            WorkflowExecutionResponse: Validated response object
        """
        return WorkflowExecutionResponse(**output)
    
    def cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        if self.server:
            logger.info("Stopping ComfyUI server")
            self.server.stop()
