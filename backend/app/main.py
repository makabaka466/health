# FastAPI entry point
# FastAPI entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.features.admin.router import router as admin_system_router
from app.features.ai.router import router as ai_assistant_router
from app.features.auth.router import router as auth_router
from app.features.health_data.router import router as health_data_router
from app.features.knowledge.router import router as knowledge_router

 
app = FastAPI(
    title="健康管理系统API",
    description="健康管理系统的后端API服务",
    version="1.0.0"
)
 
# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

 
# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(health_data_router, prefix="/api/health", tags=["健康数据"])
app.include_router(ai_assistant_router, prefix="/api/ai", tags=["AI聊天"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["健康知识"])
app.include_router(admin_system_router, prefix="/api/admin/system", tags=["管理员系统"])


@app.on_event("startup")
def on_startup() -> None:
    init_db()
 
@app.get("/")
async def root():
    return {"message": "健康管理系统API正在运行"}
 
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)