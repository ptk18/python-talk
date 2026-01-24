from .auth import router as auth_router
from .users import router as users_router
from .posts import router as posts_router
from .messages import router as messages_router
from .translate import router as translate_router
from .paraphrase import router as paraphrase_router
from .favorites import router as favorites_router

__all__ = [
    "auth_router",
    "users_router",
    "posts_router",
    "messages_router",
    "translate_router",
    "paraphrase_router",
    "favorites_router",
]
