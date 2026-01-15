"""
Model Manager with LRU eviction for ML models.

This module manages the lifecycle of ML models to control memory usage.
Features:
- Lazy loading: Models are only loaded when first accessed
- LRU eviction: Least recently used models are unloaded when memory limit is reached
- Idle timeout: Models unused for a period are automatically unloaded
- Thread safety: Safe for concurrent access
"""

import os
import gc
import time
import threading
from typing import Optional, Dict, Callable, Any
from dataclasses import dataclass, field

# Feature flag
FEATURE_MODEL_MANAGER = os.getenv("FEATURE_MODEL_MANAGER", "true").lower() == "true"

# Configuration from environment
MAX_MEMORY_MB = int(os.getenv("MODEL_MANAGER_MAX_MEMORY_MB", "6000"))
IDLE_TIMEOUT_SECONDS = int(os.getenv("MODEL_MANAGER_IDLE_TIMEOUT", "300"))  # 5 minutes


@dataclass
class ManagedModel:
    """Container for a managed model with metadata."""
    name: str
    loader: Callable[[], Any]
    size_mb: int
    model: Any = None
    last_used: float = 0
    load_count: int = 0
    unload_count: int = 0


class ModelManager:
    """
    Manages ML models with LRU eviction and memory limits.

    Usage:
        manager = get_model_manager()

        # Register a model (does not load immediately)
        manager.register(
            name="whisper_english",
            loader=lambda: load_english_whisper(),
            size_mb=1500
        )

        # Get the model (loads on first access)
        model = manager.get("whisper_english")

        # Use the model...
        result = model.transcribe(audio)
    """

    def __init__(self, max_memory_mb: int = MAX_MEMORY_MB, idle_timeout: int = IDLE_TIMEOUT_SECONDS):
        """
        Initialize the model manager.

        Args:
            max_memory_mb: Maximum total memory for all models
            idle_timeout: Seconds of inactivity before model is unloaded
        """
        self.max_memory_mb = max_memory_mb
        self.idle_timeout = idle_timeout
        self.models: Dict[str, ManagedModel] = {}
        self.lock = threading.RLock()
        self.total_memory_mb = 0
        self._running = True

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        print(f"[ModelManager] Initialized with max_memory={max_memory_mb}MB, idle_timeout={idle_timeout}s")

    def register(self, name: str, loader: Callable[[], Any], size_mb: int):
        """
        Register a model loader (does not load the model immediately).

        Args:
            name: Unique identifier for the model
            loader: Callable that returns the loaded model
            size_mb: Estimated memory size in MB
        """
        with self.lock:
            if name in self.models:
                print(f"[ModelManager] Updating registration for '{name}'")
            else:
                print(f"[ModelManager] Registering model '{name}' (estimated {size_mb}MB)")

            self.models[name] = ManagedModel(
                name=name,
                loader=loader,
                size_mb=size_mb
            )

    def get(self, name: str) -> Any:
        """
        Get a model, loading if necessary.

        Args:
            name: Model identifier

        Returns:
            The loaded model

        Raises:
            KeyError: If model is not registered
        """
        with self.lock:
            if name not in self.models:
                raise KeyError(f"Model '{name}' not registered")

            managed = self.models[name]

            # Load if not already loaded
            if managed.model is None:
                self._ensure_memory(managed.size_mb)
                self._load_model(managed)

            # Update last used time
            managed.last_used = time.time()
            return managed.model

    def is_loaded(self, name: str) -> bool:
        """Check if a model is currently loaded."""
        with self.lock:
            if name not in self.models:
                return False
            return self.models[name].model is not None

    def unload(self, name: str) -> bool:
        """
        Manually unload a model.

        Args:
            name: Model identifier

        Returns:
            True if model was unloaded, False if not loaded
        """
        with self.lock:
            if name not in self.models:
                return False

            managed = self.models[name]
            if managed.model is None:
                return False

            self._unload_model(managed)
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about managed models."""
        with self.lock:
            loaded = [(m.name, m.size_mb) for m in self.models.values() if m.model is not None]
            registered = [(m.name, m.size_mb) for m in self.models.values()]

            return {
                "max_memory_mb": self.max_memory_mb,
                "used_memory_mb": self.total_memory_mb,
                "idle_timeout_s": self.idle_timeout,
                "registered_models": len(self.models),
                "loaded_models": len(loaded),
                "registered": registered,
                "loaded": loaded,
                "load_counts": {m.name: m.load_count for m in self.models.values()},
                "unload_counts": {m.name: m.unload_count for m in self.models.values()},
            }

    def shutdown(self):
        """Stop the cleanup thread and unload all models."""
        self._running = False
        with self.lock:
            for managed in self.models.values():
                if managed.model is not None:
                    self._unload_model(managed)

    def _ensure_memory(self, needed_mb: int):
        """Evict models if needed to make room for a new model."""
        while self.total_memory_mb + needed_mb > self.max_memory_mb:
            # Find least recently used loaded model
            lru_model = None
            lru_time = float('inf')

            for managed in self.models.values():
                if managed.model is not None and managed.last_used < lru_time:
                    lru_time = managed.last_used
                    lru_model = managed

            if lru_model is None:
                # No models to evict - we're at capacity
                print(f"[ModelManager] WARNING: Cannot free memory, at capacity ({self.total_memory_mb}MB)")
                break

            self._unload_model(lru_model)

    def _load_model(self, managed: ManagedModel):
        """Load a model into memory."""
        print(f"[ModelManager] Loading '{managed.name}' (~{managed.size_mb}MB)...")
        start_time = time.time()

        try:
            managed.model = managed.loader()
            managed.last_used = time.time()
            managed.load_count += 1
            self.total_memory_mb += managed.size_mb

            elapsed = time.time() - start_time
            print(f"[ModelManager] Loaded '{managed.name}' in {elapsed:.1f}s (total memory: {self.total_memory_mb}MB)")
        except Exception as e:
            print(f"[ModelManager] ERROR loading '{managed.name}': {e}")
            raise

    def _unload_model(self, managed: ManagedModel):
        """Unload a model to free memory."""
        print(f"[ModelManager] Unloading '{managed.name}' (freeing ~{managed.size_mb}MB)...")

        # Try to move model to CPU first (for PyTorch models)
        if hasattr(managed.model, 'to'):
            try:
                managed.model.to('cpu')
            except Exception:
                pass

        # Try to delete model-specific caches
        if hasattr(managed.model, 'clear_cache'):
            try:
                managed.model.clear_cache()
            except Exception:
                pass

        # Delete the model
        del managed.model
        managed.model = None
        managed.unload_count += 1
        self.total_memory_mb -= managed.size_mb

        # Force garbage collection
        gc.collect()

        # Clear CUDA cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        print(f"[ModelManager] Unloaded '{managed.name}' (total memory: {self.total_memory_mb}MB)")

    def _cleanup_loop(self):
        """Background thread to unload idle models."""
        while self._running:
            time.sleep(60)  # Check every minute

            if not self._running:
                break

            current_time = time.time()

            with self.lock:
                for managed in self.models.values():
                    if managed.model is not None:
                        idle_time = current_time - managed.last_used
                        if idle_time > self.idle_timeout:
                            print(f"[ModelManager] '{managed.name}' idle for {idle_time:.0f}s, unloading...")
                            self._unload_model(managed)


# Global singleton instance
_model_manager: Optional[ModelManager] = None
_manager_lock = threading.Lock()


def get_model_manager() -> ModelManager:
    """
    Get the global ModelManager instance.

    Returns:
        ModelManager singleton
    """
    global _model_manager

    if not FEATURE_MODEL_MANAGER:
        # Return a pass-through manager that doesn't do LRU eviction
        return _get_simple_manager()

    if _model_manager is None:
        with _manager_lock:
            if _model_manager is None:
                _model_manager = ModelManager()

    return _model_manager


def _get_simple_manager() -> 'SimpleModelManager':
    """Get a simple pass-through manager when feature is disabled."""
    return SimpleModelManager()


class SimpleModelManager:
    """
    Simple pass-through manager when model management is disabled.
    Models are loaded on first access and never unloaded.
    """

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.loaders: Dict[str, Callable] = {}
        self.lock = threading.Lock()

    def register(self, name: str, loader: Callable[[], Any], size_mb: int):
        """Register a model loader."""
        self.loaders[name] = loader

    def get(self, name: str) -> Any:
        """Get a model, loading if necessary."""
        with self.lock:
            if name not in self.models:
                if name not in self.loaders:
                    raise KeyError(f"Model '{name}' not registered")
                self.models[name] = self.loaders[name]()
            return self.models[name]

    def is_loaded(self, name: str) -> bool:
        """Check if a model is loaded."""
        return name in self.models

    def unload(self, name: str) -> bool:
        """No-op in simple manager."""
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get basic stats."""
        return {
            "mode": "simple (feature disabled)",
            "loaded_models": list(self.models.keys())
        }

    def shutdown(self):
        """No-op in simple manager."""
        pass
