# FastAPI entry point
# FastAPI entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import ai_assistant, auth, health_data, knowledge

 
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
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(health_data.router, prefix="/api/health", tags=["健康数据"])
app.include_router(ai_assistant.router, prefix="/api/ai", tags=["AI聊天"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["健康知识"])


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