"""Common types and enums for ComfyPack."""
from enum import Enum
from typing import Any, Dict, List, Union
from pathlib import Path

class NodeType(str, Enum):
    """Type of node in the workflow."""
    INPUT = "input"
    OUTPUT = "output"
    PROCESS = "process"

class NodeClass(str, Enum):
    """ComfyUI node classes that we handle."""
    OUTPUT_FILE = "CPackOutputFile"
    OUTPUT_IMAGE = "CPackOutputImage"
    INPUT_FILE = "CPackInputFile"
    INPUT_IMAGE = "CPackInputImage"
    INPUT_STRING = "CPackInputString"
    INPUT_INT = "CPackInputInt"
    INPUT_ANY = "CPackInputAny"

# Type aliases for better code readability
JsonDict = Dict[str, Any]
NodeId = str
OutputType = Union[Path, List[Path], Dict[str, Union[Path, List[Path]]]]
