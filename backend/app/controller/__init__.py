from app.controller.admin_controller import router as admin_router
from app.controller.ai_controller import router as ai_router
from app.controller.auth_controller import router as auth_router
from app.controller.health_data_controller import router as health_data_router
from app.controller.knowledge_controller import router as knowledge_router

__all__ = [
    "auth_router",
    "health_data_router",
    "ai_router",
    "knowledge_router",
    "admin_router",
]

