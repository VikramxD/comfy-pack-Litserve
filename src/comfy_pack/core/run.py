"""Core functionality for running ComfyUI workflows."""
from __future__ import annotations

import copy
import json
import logging
import os
import random
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Union
from urllib import parse, request

logger = logging.getLogger(__name__)

def _probe_comfyui_server(port: int) -> None:
    """Probe ComfyUI server to check if it's ready."""
    url = f"http://127.0.0.1:{port}/api/customnode/getmappings"
    params = {"mode": "nickname"}
    full_url = f"{url}?{parse.urlencode(params)}"
    req = request.Request(full_url)
    _ = request.urlopen(req)

    full_url = f"http://127.0.0.1:{port}/api/object_info"
    req = request.Request(full_url)
    _ = request.urlopen(req)

def _is_port_in_use(port: int | str, host="localhost") -> bool:
    """Check if a port is in use."""
    if isinstance(port, str):
        port = int(port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except ConnectionRefusedError:
            return False
        except Exception:
            return True

class ComfyUIServer:
    """Manages a ComfyUI server instance."""
    
    def __init__(
        self,
        workspace: str,
        input_dir: str = "input",
        port: Union[int, str, None] = None,
        verbose: int = 0,
    ):
        """Initialize ComfyUI server.
        
        Args:
            workspace: Working directory for ComfyUI
            input_dir: Directory for input files
            port: Port to run server on, if None a random port will be used
            verbose: Verbosity level
        """
        self.workspace = Path(workspace)
        self.input_dir = Path(input_dir)
        self.port = port or random.randint(10000, 65535)
        self.verbose = verbose
        self.host = "127.0.0.1"
        self.proc = None
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        """Start the ComfyUI server."""
        if self.proc is not None:
            return

        while _is_port_in_use(self.port, self.host):
            self.port = random.randint(10000, 65535)

        env = os.environ.copy()
        env["COMFY_PORT"] = str(self.port)
        
        command = ["python", "-m", "comfy.cli.main"]
        if self.verbose:
            command.append("-" + "v" * self.verbose)

        self.proc = subprocess.Popen(
            command,
            env=env,
            cwd=str(self.workspace),
            stdout=subprocess.PIPE if not self.verbose else None,
            stderr=subprocess.PIPE if not self.verbose else None,
        )
        
        try:
            _wait_for_startup(self.host, self.port)
        except Exception as e:
            self.stop()
            raise RuntimeError(f"Failed to start ComfyUI server: {e}")

    def stop(self) -> None:
        """Stop the ComfyUI server."""
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None

    def execute_workflow(
        self,
        workflow: dict,
        inputs: dict,
        session_id: str = "",
        timeout: int = 300
    ) -> Any:
        """Execute a workflow with given inputs.
        
        Args:
            workflow: Workflow to execute
            inputs: Input values for the workflow
            session_id: Session identifier
            timeout: Execution timeout in seconds
            
        Returns:
            Workflow outputs
            
        Raises:
            RuntimeError: If workflow execution fails
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        output_dir = self.workspace / "output" / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            return run_workflow(
                self.host,
                self.port,
                workflow,
                output_dir=output_dir,
                timeout=timeout,
                verbose=self.verbose,
                workspace=str(self.workspace),
                **inputs
            )
        except Exception as e:
            raise RuntimeError(f"Workflow execution failed: {e}")

def _wait_for_startup(host: str, port: int, timeout: int = 1800) -> None:
    """Wait for ComfyUI server to start up."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            _probe_comfyui_server(port)
            return
        except Exception:
            time.sleep(1)
    raise TimeoutError("ComfyUI server failed to start")

def execute_remote_workflow(
    server_url: str,
    workflow: dict,
    inputs: dict,
    session_id: str = "",
    timeout: int = 300
) -> Any:
    """Execute a workflow on a remote ComfyUI server.
    
    Args:
        server_url: URL of the ComfyUI server
        workflow: Workflow to execute
        inputs: Input values for the workflow
        session_id: Session identifier
        timeout: Execution timeout in seconds
        
    Returns:
        Workflow outputs
        
    Raises:
        RuntimeError: If workflow execution fails
    """
    try:
        # Parse URL for host and port
        parsed = parse.urlparse(server_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 8188
        
        # Execute workflow
        return run_workflow(
            host,
            port,
            workflow,
            timeout=timeout,
            **inputs
        )
    except Exception as e:
        raise RuntimeError(f"Remote workflow execution failed: {e}")

def run_workflow(
    host: str,
    port: int,
    workflow: dict,
    output_dir: Union[str, Path, None] = None,
    timeout: int = 300,
    verbose: int = 0,
    workspace: str = ".",
    **kwargs: Any,
) -> Any:
    """Run a ComfyUI workflow.
    
    Args:
        host: Server host
        port: Server port
        workflow: Workflow to execute
        output_dir: Output directory
        timeout: Execution timeout in seconds
        verbose: Verbosity level
        workspace: Working directory
        **kwargs: Input values for the workflow
        
    Returns:
        Workflow outputs
        
    Raises:
        RuntimeError: If workflow execution fails
    """
    from ..utils import populate_workflow, retrieve_workflow_outputs
    
    if output_dir is None:
        output_dir = Path(workspace) / "output" / str(uuid.uuid4())
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(output_dir)
        
    # Prepare workflow
    workflow = copy.deepcopy(workflow)
    workflow = populate_workflow(workflow, output_dir, **kwargs)
    
    # Execute workflow
    prompt_url = f"http://{host}:{port}/prompt"
    req_data = {"prompt": workflow}
    
    try:
        req = request.Request(
            prompt_url,
            data=json.dumps(req_data).encode(),
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req) as resp:
            prompt_id = json.loads(resp.read())["prompt_id"]
            
        # Wait for completion
        history_url = f"http://{host}:{port}/history/{prompt_id}"
        start_time = time.time()
        while time.time() - start_time < timeout:
            req = request.Request(history_url)
            with request.urlopen(req) as resp:
                history = json.loads(resp.read())
                if history["outputs"]:
                    break
            time.sleep(1)
        else:
            raise TimeoutError("Workflow execution timed out")
            
        # Get outputs
        return retrieve_workflow_outputs(workflow, output_dir)
        
    except Exception as e:
        if isinstance(e, TimeoutError):
            raise
        raise RuntimeError(f"Workflow execution failed: {e}")
