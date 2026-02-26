from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="健康管理系统API",
    description="健康管理系统的后端API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "健康管理系统API正在运行"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# 简单的登录接口
@app.post("/api/auth/login")
async def login(username: str, password: str):
    # 模拟用户验证
    if username == "admin" and password == "123456":
        return {
            "access_token": "mock-token-user",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": "admin",
                "email": "admin@health.com",
                "role": "user"
            }
        }
    else:
        return {"error": "用户名或密码错误"}

# 管理员登录接口
@app.post("/api/auth/admin/login")
async def admin_login(username: str, password: str):
    # 模拟管理员验证
    if username == "admin" and password == "admin123":
        return {
            "access_token": "mock-token-admin",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": "admin",
                "email": "admin@health.com",
                "role": "admin"
            }
        }
    else:
        return {"error": "管理员账号或密码错误"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
