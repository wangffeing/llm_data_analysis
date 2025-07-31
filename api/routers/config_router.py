import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.config_service import ConfigService
from dependencies import get_session_manager
from session_manager import SessionManager

logger = logging.getLogger(__name__)
router = APIRouter()

# 请求模型
class SessionConfigUpdateRequest(BaseModel):
    session_id: str
    config: Dict[str, Any]

class SessionRolesRequest(BaseModel):
    session_id: str
    roles: List[str]

class AllowedModulesRequest(BaseModel):
    session_id: str
    modules: List[str]

class LLMConfigRequest(BaseModel):
    session_id: str
    model: str
    api_type: str = "qwen"

# 依赖注入
def get_config_service(session_manager: SessionManager = Depends(get_session_manager)) -> ConfigService:
    return ConfigService(session_manager)

@router.get("/session/{session_id}")
async def get_session_config(session_id: str):
    """获取会话配置"""
    try:
        session_manager = get_session_manager()
        config = session_manager.get_session_config(session_id)
        
        if config is None:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"success": True, "config": config}
    except Exception as e:
        logger.error(f"获取会话配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/session/{session_id}")
async def update_session_config(session_id: str, config_update: dict):
    """更新会话配置"""
    try:
        session_manager = get_session_manager()
        
        # 验证配置
        config_service = ConfigService(session_manager)
        if not config_service.validate_config(config_update):
            raise HTTPException(status_code=400, detail="配置验证失败")
        
        # 更新会话配置
        success = session_manager.update_session_config(session_id, config_update)
        
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"success": True, "message": "会话配置更新成功"}
    except Exception as e:
        logger.error(f"更新会话配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/session/{session_id}/roles")
async def update_session_roles(session_id: str, roles_data: dict):
    """更新会话角色配置"""
    try:
        roles = roles_data.get("roles", [])
        session_manager = get_session_manager()
        
        # 验证角色
        config_service = ConfigService(session_manager)
        if not config_service.validate_roles(roles):
            raise HTTPException(status_code=400, detail="角色验证失败")
        
        # 更新配置
        success = session_manager.update_session_config(session_id, {"session.roles": roles})
        
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"success": True, "message": "会话角色配置更新成功"}
    except Exception as e:
        logger.error(f"更新会话角色配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
# 将 POST 方法改为 PUT 方法，并添加 session_id 路径参数
@router.put("/session/{session_id}/llm")
async def update_session_llm_config(
    session_id: str,
    llm_config: dict,
    config_service: ConfigService = Depends(get_config_service)
):
    """更新会话LLM配置"""
    try:
        config_update = {
            "llm.model": llm_config.get("model"),
            "llm.api_type": llm_config.get("api_type", "qwen")
        }
        session_manager = get_session_manager()
        success = session_manager.update_session_config(session_id, config_update)
        if success:
            return {"success": True, "message": "会话LLM配置更新成功"}
        else:
            raise HTTPException(status_code=400, detail="会话LLM配置更新失败")
    except Exception as e:
        logger.error(f"更新会话LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail="更新会话LLM配置失败")

@router.put("/session/{session_id}/modules")
async def update_session_allowed_modules(
    session_id: str,
    modules_data: dict,
    config_service: ConfigService = Depends(get_config_service)
):
    """更新会话允许的模块列表"""
    try:
        modules = modules_data.get("modules", [])
        session_manager = get_session_manager()
        success = session_manager.update_session_config(
            session_id,
            {"code_interpreter.allowed_modules": modules}
        )
        if success:
            return {"success": True, "message": "会话允许模块列表更新成功"}
        else:
            raise HTTPException(status_code=400, detail="会话允许模块列表更新失败")
    except Exception as e:
        logger.error(f"更新会话允许模块列表失败: {e}")
        raise HTTPException(status_code=500, detail="更新会话允许模块列表失败")

# 保留原有的全局配置选项API
@router.get("/options/models")
async def get_available_models(config_service: ConfigService = Depends(get_config_service)):
    """获取可用的模型列表"""
    try:
        models = config_service.get_available_models()
        return {"success": True, "models": models}
    except Exception as e:
        logger.error(f"获取可用模型失败: {e}")
        raise HTTPException(status_code=500, detail="获取可用模型失败")

@router.get("/options/roles")
async def get_available_roles(config_service: ConfigService = Depends(get_config_service)):
    """获取可用的角色列表"""
    try:
        roles = config_service.get_available_roles()
        return {"success": True, "roles": roles}
    except Exception as e:
        logger.error(f"获取可用角色失败: {e}")
        raise HTTPException(status_code=500, detail="获取可用角色失败")

@router.get("/options/modules")
async def get_available_modules(config_service: ConfigService = Depends(get_config_service)):
    """获取可用的模块列表"""
    try:
        modules = config_service.get_available_modules()
        return {"success": True, "modules": modules}
    except Exception as e:
        logger.error(f"获取可用模块失败: {e}")
        raise HTTPException(status_code=500, detail="获取可用模块失败")
