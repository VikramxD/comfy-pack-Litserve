"""Workflow-related schema definitions."""
import uuid
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator

from .types import JsonDict, NodeType, OutputType

class Node(BaseModel):
    """Base model for workflow nodes."""
    id: str
    type: NodeType
    class_type: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"  # Allow extra fields for ComfyUI compatibility

class WorkflowMetadata(BaseModel):
    """Metadata for workflow execution."""
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None

class WorkflowExecutionRequest(BaseModel):
    """Schema for workflow execution requests."""
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input values for the workflow"
    )
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique session identifier"
    )
    metadata: Optional[WorkflowMetadata] = None
    
    @validator("inputs")
    def validate_inputs(cls, v):
        """Ensure inputs are JSON serializable."""
        # Convert Path objects to strings
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(i) for i in obj]
            return obj
        return convert_paths(v)

class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution responses."""
    session_id: str
    status: str = Field(..., description="Status of the workflow execution")
    outputs: Dict[str, OutputType] = Field(
        default_factory=dict,
        description="Output files or values from the workflow"
    )
    metadata: JsonDict = Field(
        default_factory=dict,
        description="Additional metadata about the execution"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if execution failed"
    )

class WorkflowValidationError(BaseModel):
    """Schema for workflow validation errors."""
    loc: List[Union[str, int]]
    msg: str
    type: str
