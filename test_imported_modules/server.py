from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import inspect
import subprocess
import json
import sys
from typing import Optional, Dict, List, Any
from functools import lru_cache
import os

app = FastAPI(title="Python Module Introspector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modules that are safe to introspect (educational/common)
WHITELIST = {
    # Graphics & Visualization
    'turtle', 'tkinter', 'pygame',
    # Math & Science
    'math', 'cmath', 'statistics', 'decimal', 'fractions',
    # Data structures
    'collections', 'itertools', 'functools', 'operator',
    # Data Science (if installed)
    'numpy', 'pandas', 'matplotlib',
    # String & Text
    'string', 're', 'textwrap',
    # Date & Time
    'datetime', 'time', 'calendar',
    # Random
    'random',
    # JSON
    'json',
    # Typing
    'typing',
}

# Modules that should NEVER be introspected (dangerous)
BLACKLIST = {
    'os', 'sys', 'subprocess', 'shutil', 'pathlib',  # System access
    'socket', 'requests', 'urllib', 'http', 'ftplib',  # Network
    'smtplib', 'ssl', 'paramiko',  # Email/SSH
    'threading', 'multiprocessing', 'concurrent',  # Concurrency
    'ctypes', 'cffi',  # Low-level
    'pickle', 'shelve', 'marshal',  # Serialization (security risk)
    'importlib', 'builtins', '__builtins__',  # Meta
    'code', 'codeop', 'compile',  # Code execution
    'eval', 'exec',  # Dangerous builtins
}

# Configuration
INTROSPECTION_TIMEOUT = 10  # seconds
MAX_METHODS_PER_MODULE = 100  # Limit methods to prevent UI overload

# Cache for introspection results
_introspection_cache: Dict[str, Any] = {}

def should_introspect_module(module_name: str) -> tuple[bool, str]:
    """Check if a module is safe to introspect."""
    base_module = module_name.split('.')[0]

    if base_module in BLACKLIST:
        return False, f"Module '{base_module}' is blacklisted for security reasons"

    if base_module in WHITELIST:
        return True, "OK"

    # For unknown modules, allow but warn
    return True, f"Module '{base_module}' not in whitelist, proceeding anyway"


def _extract_method_info(func, name: str) -> Optional[Dict]:
    """Extract parameter and docstring information from a function."""
    try:
        # Skip private/magic methods
        if name.startswith('_'):
            return None

        # Get signature
        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            # Some built-in functions don't have signatures
            return {
                "name": name,
                "parameters": {},
                "required_parameters": [],
                "return_type": None,
                "docstring": inspect.getdoc(func) or None
            }

        parameters = {}
        required_parameters = []

        for param_name, param in sig.parameters.items():
            # Skip self/cls
            if param_name in ('self', 'cls'):
                continue

            # Get type annotation
            param_type = "Any"
            if param.annotation != inspect.Parameter.empty:
                try:
                    param_type = getattr(param.annotation, '__name__', str(param.annotation))
                except:
                    param_type = str(param.annotation)

            parameters[param_name] = param_type

            # Check if required (no default value)
            if param.default == inspect.Parameter.empty and param.kind not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD
            ):
                required_parameters.append(param_name)

        # Get return type
        return_type = None
        if sig.return_annotation != inspect.Signature.empty:
            try:
                return_type = getattr(sig.return_annotation, '__name__', str(sig.return_annotation))
            except:
                return_type = str(sig.return_annotation)

        return {
            "name": name,
            "parameters": parameters,
            "required_parameters": required_parameters,
            "return_type": return_type,
            "docstring": inspect.getdoc(func) or None
        }

    except Exception as e:
        return None


def introspect_module_direct(module_name: str, import_type: str = "module",
                             imported_names: Optional[List[str]] = None) -> Dict:
    """
    Directly introspect a module (runs in same process).
    For subprocess isolation, use safe_introspect_module().
    """
    try:
        # Import the module
        module = __import__(module_name)

        # Handle submodules (e.g., 'matplotlib.pyplot')
        for part in module_name.split('.')[1:]:
            module = getattr(module, part)

        methods = []

        if import_type == "from_import" and imported_names:
            # Only introspect specific names
            for name in imported_names:
                if hasattr(module, name):
                    obj = getattr(module, name)
                    if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.isbuiltin(obj):
                        info = _extract_method_info(obj, name)
                        if info:
                            methods.append(info)
                    elif inspect.isclass(obj):
                        # Extract class methods
                        for method_name in dir(obj):
                            if not method_name.startswith('_'):
                                method = getattr(obj, method_name, None)
                                if callable(method):
                                    info = _extract_method_info(method, method_name)
                                    if info:
                                        methods.append(info)
        else:
            # Introspect all module-level functions
            for name in dir(module):
                if name.startswith('_'):
                    continue

                obj = getattr(module, name, None)
                if obj is None:
                    continue

                if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.isbuiltin(obj):
                    info = _extract_method_info(obj, name)
                    if info:
                        methods.append(info)
                elif inspect.isclass(obj):
                    # For classes like turtle.Turtle, extract their methods
                    # But only if it's a major class (has multiple methods)
                    class_methods = []
                    for method_name in dir(obj):
                        if not method_name.startswith('_'):
                            method = getattr(obj, method_name, None)
                            if callable(method):
                                info = _extract_method_info(method, method_name)
                                if info:
                                    info['class'] = name
                                    class_methods.append(info)

                    # Only include if it's a substantial class
                    if len(class_methods) >= 3:
                        methods.extend(class_methods[:20])  # Limit per class

        # Limit total methods
        methods = methods[:MAX_METHODS_PER_MODULE]

        # Sort alphabetically
        methods.sort(key=lambda m: m['name'])

        return {
            "success": True,
            "module_name": module_name,
            "methods": methods,
            "total_methods": len(methods),
            "docstring": inspect.getdoc(module),
            "error": None
        }

    except ImportError as e:
        return {
            "success": False,
            "module_name": module_name,
            "methods": [],
            "total_methods": 0,
            "docstring": None,
            "error": f"Module not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "module_name": module_name,
            "methods": [],
            "total_methods": 0,
            "docstring": None,
            "error": f"Introspection failed: {str(e)}"
        }


def safe_introspect_module(module_name: str, import_type: str = "module",
                           imported_names: Optional[List[str]] = None) -> Dict:
    """
    Safely introspect a module by running in a subprocess with timeout.
    This prevents side effects from module imports.
    """
    # Check cache first
    cache_key = f"{module_name}:{import_type}:{','.join(imported_names or [])}"
    if cache_key in _introspection_cache:
        return _introspection_cache[cache_key]

    # Build subprocess command
    names_arg = json.dumps(imported_names) if imported_names else "None"

    code = f'''
import json
import inspect
import sys

def extract_method_info(func, name):
    try:
        if name.startswith('_'):
            return None
        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            return {{"name": name, "parameters": {{}}, "required_parameters": [], "return_type": None, "docstring": inspect.getdoc(func)}}

        parameters = {{}}
        required_parameters = []

        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
            param_type = "Any"
            if param.annotation != inspect.Parameter.empty:
                try:
                    param_type = getattr(param.annotation, '__name__', str(param.annotation))
                except:
                    param_type = str(param.annotation)
            parameters[param_name] = param_type
            if param.default == inspect.Parameter.empty and param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                required_parameters.append(param_name)

        return_type = None
        if sig.return_annotation != inspect.Signature.empty:
            try:
                return_type = getattr(sig.return_annotation, '__name__', str(sig.return_annotation))
            except:
                return_type = str(sig.return_annotation)

        return {{"name": name, "parameters": parameters, "required_parameters": required_parameters, "return_type": return_type, "docstring": inspect.getdoc(func)}}
    except:
        return None

try:
    module = __import__("{module_name}")
    for part in "{module_name}".split('.')[1:]:
        module = getattr(module, part)

    methods = []
    import_type = "{import_type}"
    imported_names = {names_arg}

    if import_type == "from_import" and imported_names:
        for name in imported_names:
            if hasattr(module, name):
                obj = getattr(module, name)
                if callable(obj):
                    info = extract_method_info(obj, name)
                    if info:
                        methods.append(info)
    else:
        for name in dir(module):
            if name.startswith('_'):
                continue
            obj = getattr(module, name, None)
            if obj and callable(obj):
                info = extract_method_info(obj, name)
                if info:
                    methods.append(info)

    methods = methods[:100]
    methods.sort(key=lambda m: m['name'])

    print(json.dumps({{"success": True, "module_name": "{module_name}", "methods": methods, "total_methods": len(methods), "docstring": inspect.getdoc(module), "error": None}}))
except Exception as e:
    print(json.dumps({{"success": False, "module_name": "{module_name}", "methods": [], "total_methods": 0, "docstring": None, "error": str(e)}}))
'''

    try:
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            timeout=INTROSPECTION_TIMEOUT
        )

        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            _introspection_cache[cache_key] = data
            return data
        else:
            return {
                "success": False,
                "module_name": module_name,
                "methods": [],
                "total_methods": 0,
                "docstring": None,
                "error": result.stderr or "Unknown error"
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "module_name": module_name,
            "methods": [],
            "total_methods": 0,
            "docstring": None,
            "error": f"Introspection timed out after {INTROSPECTION_TIMEOUT}s"
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "module_name": module_name,
            "methods": [],
            "total_methods": 0,
            "docstring": None,
            "error": f"Failed to parse result: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "module_name": module_name,
            "methods": [],
            "total_methods": 0,
            "docstring": None,
            "error": str(e)
        }



@app.get("/api/introspect")
async def introspect_endpoint(
    module: str = Query(..., description="Module name to introspect (e.g., 'turtle', 'math')"),
    import_type: str = Query("module", description="'module' for 'import X' or 'from_import' for 'from X import Y'"),
    names: Optional[str] = Query(None, description="Comma-separated names for from_import (e.g., 'forward,left,right')")
):
    """
    Introspect a Python module and return its methods.

    Examples:
    - /api/introspect?module=turtle
    - /api/introspect?module=math&import_type=from_import&names=sin,cos,tan
    """
    # Security check
    allowed, message = should_introspect_module(module)
    if not allowed:
        raise HTTPException(status_code=403, detail=message)

    # Parse names if provided
    imported_names = None
    if names:
        imported_names = [n.strip() for n in names.split(',') if n.strip()]

    # Perform introspection (using subprocess for safety)
    result = safe_introspect_module(module, import_type, imported_names)

    if not result["success"]:
        # Still return 200 but with error info
        pass

    return result


@app.get("/api/modules")
async def list_modules():
    """List all whitelisted modules that can be introspected."""
    return {
        "whitelist": sorted(list(WHITELIST)),
        "blacklist": sorted(list(BLACKLIST)),
        "total_whitelisted": len(WHITELIST)
    }


@app.delete("/api/cache")
async def clear_cache():
    """Clear the introspection cache."""
    global _introspection_cache
    count = len(_introspection_cache)
    _introspection_cache = {}
    return {"cleared": count, "message": f"Cleared {count} cached entries"}



# Serve static files from current directory
static_dir = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon requests."""
    return Response(status_code=204)

@app.get("/{filename}")
async def serve_static(filename: str):
    """Serve static files (css, js)."""
    # Ignore Chrome DevTools requests
    if filename.startswith('.well-known'):
        return Response(status_code=204)

    filepath = os.path.join(static_dir, filename)
    if os.path.exists(filepath) and not filename.startswith('.'):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    import uvicorn
    print("Python Module Introspection Server")
    print(f"API: http://localhost:8001/api/introspect?module=turtle")
    print(f"UI:  http://localhost:8001/")
    uvicorn.run(app, host="0.0.0.0", port=8001)
