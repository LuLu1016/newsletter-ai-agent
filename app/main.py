from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.routers import events, content
from app.core.config import Settings, get_settings

def create_application(settings: Settings) -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI驱动的活动通讯生成服务",
        version="1.0.0",
        debug=settings.DEBUG
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(events.router)
    app.include_router(content.router)

    return app

# 创建应用实例
app = create_application(get_settings())

# 根路径
@app.get("/")
async def root(settings: Settings = Depends(get_settings)):
    """API根路径"""
    return {
        "message": f"欢迎使用{settings.PROJECT_NAME} API",
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }