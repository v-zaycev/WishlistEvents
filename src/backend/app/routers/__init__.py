from .register import router as register_router
from .login import router as login_router
from .wishlists import router as wishlists_router
from .events import router as events_router

__all__ = [
    "register_router",
    "login_router",
    "wishlists_router",
    "events_router"
]
