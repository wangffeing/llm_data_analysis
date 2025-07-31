import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

# 导入依赖项和模块
from dependencies import cleanup_dependencies, get_taskweaver_app, get_db_connection
import dependencies as deps
from services.sse_service import SSEService
from routers import chat_router, session_router, data_source_router, system_router, file_upload_router, config_router, template_router, report_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动事件
    logger.info("TaskWeaver SSE API starting up...")
    
    try:
        # 初始化核心依赖
        _ = get_taskweaver_app()
        _ = get_db_connection()

        # 初始化并配置SSE服务
        sse_service_instance = SSEService()
        loop = asyncio.get_event_loop()
        sse_service_instance.configure(loop)
        # deps._sse_service = sse_service_instance  # 将实例注入到依赖模块
        deps.set_sse_service(sse_service_instance)

        logger.info("所有依赖初始化成功")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
    
    yield
    
    # 关闭事件
    logger.info("TaskWeaver SSE API shutting down...")
    await cleanup_dependencies()

# 创建FastAPI应用
app = FastAPI(
    title="TaskWeaver SSE API",
    description="TaskWeaver聊天API with Server-Sent Events",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(session_router.router, prefix="/api/session", tags=["session"])
app.include_router(data_source_router.router, prefix="/api/data", tags=["data"])
app.include_router(system_router.router, prefix="/api/system", tags=["system"])
app.include_router(file_upload_router.router, prefix="/api/files", tags=["files"])
app.include_router(config_router.router, prefix="/api/config", tags=["config"])
app.include_router(template_router.router, prefix="/api/templates", tags=["templates"])
app.include_router(report_router.router, prefix="/api/reports", tags=["reports"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)