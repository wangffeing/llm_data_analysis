import json
import math
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services.data_source_service import DataSourceService
from config import get_config
from auth import verify_admin_permission_cookie
from db_connection import get_db_manager  # 添加缺失的导入

router = APIRouter()

class DataSourcesResponse(BaseModel):
    data_sources: List[Dict[str, Any]]
    total: int
    current_database_type: str
    available_database_types: List[str]

class DataSourceCreateRequest(BaseModel):
    name: str
    table_name: str
    table_des: str
    table_order: str
    table_columns: List[str]
    table_columns_names: List[str]
    database_type: Optional[str] = None  # 添加数据库类型字段

class DataSourceUpdateRequest(BaseModel):
    table_name: str
    table_des: str
    table_order: str
    table_columns: List[str]
    table_columns_names: List[str]
    database_type: Optional[str] = None  # 添加数据库类型字段

# 依赖注入 - 修复：使用配置文件中的 CONFIG_DB_PATH
def get_data_source_service() -> DataSourceService:
    config = get_config()
    return DataSourceService(config.config_db_path)

@router.get("/sources", response_model=DataSourcesResponse)
async def get_data_sources(
    database_type: Optional[str] = Query(None, description="按数据库类型过滤"),
    current_only: bool = Query(False, description="只显示当前数据库类型的数据源"),
    service: DataSourceService = Depends(get_data_source_service)
):
    """获取所有数据源"""
    try:
        # 根据参数决定获取哪些数据源
        if current_only:
            data_sources_dict = service.get_data_sources_by_current_db_type()
        elif database_type:
            data_sources_dict = service.config_service.get_data_sources_by_database_type(database_type)
        else:
            data_sources_dict = service.get_all_data_sources()
        
        data_sources_list = []
        
        for name, config in data_sources_dict.items():
            data_sources_list.append({
                "name": name,
                "table_name": config["table_name"],
                "description": config["table_des"],
                "table_columns": config["table_columns"],
                "table_columns_names": config["table_columns_names"],
                "table_order": config["table_order"],
                "database_type": config.get("database_type", "unknown")
            })
        
        # 获取当前数据库类型和可用类型
        current_db_type = service.get_current_database_type()
        available_types = service.get_available_database_types()
        
        return DataSourcesResponse(
            data_sources=data_sources_list,
            total=len(data_sources_list),
            current_database_type=current_db_type,
            available_database_types=available_types
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源失败: {str(e)}")

@router.post("/sources")
async def create_data_source(
    request: DataSourceCreateRequest,
    service: DataSourceService = Depends(get_data_source_service),
    _: bool = Depends(verify_admin_permission_cookie)  # 使用 cookie 认证
):
    """创建数据源"""
    try:
        # 检查数据源是否已存在
        if service.get_data_source(request.name):
            raise HTTPException(status_code=400, detail="数据源已存在")
        
        config = {
            "table_name": request.table_name,
            "table_des": request.table_des,
            "table_order": request.table_order,
            "table_columns": request.table_columns,
            "table_columns_names": request.table_columns_names,
            "database_type": request.database_type  # 添加数据库类型
        }
        
        success = service.add_data_source(request.name, config)
        if success:
            return {"success": True, "message": "数据源创建成功"}
        else:
            raise HTTPException(status_code=500, detail="数据源创建失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建数据源失败: {str(e)}")

@router.put("/sources/{source_name}")
async def update_data_source(
    source_name: str,
    request: DataSourceUpdateRequest,
    service: DataSourceService = Depends(get_data_source_service),
    _: bool = Depends(verify_admin_permission_cookie)  # 使用 cookie 认证
):
    """更新数据源"""
    try:
        # 检查数据源是否存在
        if not service.get_data_source(source_name):
            raise HTTPException(status_code=404, detail="数据源不存在")
        
        config = {
            "table_name": request.table_name,
            "table_des": request.table_des,
            "table_order": request.table_order,
            "table_columns": request.table_columns,
            "table_columns_names": request.table_columns_names,
            "database_type": request.database_type  # 添加数据库类型
        }
        
        success = service.update_data_source(source_name, config)
        if success:
            return {"success": True, "message": "数据源更新成功"}
        else:
            raise HTTPException(status_code=500, detail="数据源更新失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新数据源失败: {str(e)}")

@router.delete("/sources/{source_name}")
async def delete_data_source(
    source_name: str,
    service: DataSourceService = Depends(get_data_source_service),
    _: bool = Depends(verify_admin_permission_cookie)  # 使用 cookie 认证
):
    """删除数据源"""
    try:
        success = service.delete_data_source(source_name)
        if success:
            return {"success": True, "message": "数据源删除成功"}
        else:
            raise HTTPException(status_code=404, detail="数据源不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据源失败: {str(e)}")

def clean_nan_values(data):
    """清理数据中的 NaN 值，将其转换为 None"""
    if isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_nan_values(value) for key, value in data.items()}
    elif isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
        return None
    elif pd.isna(data):
        return None
    else:
        return data

@router.get("/sources/{source_name}/preview")
async def get_data_preview(
    source_name: str, 
    limit: int = 5,
    service: DataSourceService = Depends(get_data_source_service)
):
    """获取数据源预览数据"""
    try:
        # 获取数据源配置
        source_config = service.get_data_source(source_name)
        if not source_config:
            raise HTTPException(status_code=404, detail="数据源不存在")
        
        table_name = source_config["table_name"]
        table_columns = ", ".join(source_config["table_columns"])
        
        # 获取数据库管理器
        db_manager = get_db_manager()
        
        # 构建查询语句
        query = f"SELECT {table_columns} FROM {table_name} LIMIT {limit}"
        
        # 执行查询 - 改为异步调用
        df = await db_manager.execute_query_to_dataframe(query)
        df.columns = source_config['table_columns']

        # 转换为字典格式
        preview_data = df.to_dict('records')

        # 清理 NaN 值
        cleaned_data = clean_nan_values(preview_data)
        
        response_data = {
            "source_name": source_name,
            "table_name": table_name,
            "database_type": source_config.get("database_type", "unknown"),
            "columns": source_config["table_columns"],
            "columns_names": source_config["table_columns_names"],
            "data": cleaned_data,
            "total_rows": len(cleaned_data)
        }
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据预览失败: {str(e)}")

@router.get("/database-types")
async def get_database_types(service: DataSourceService = Depends(get_data_source_service)):
    """获取所有可用的数据库类型"""
    try:
        current_type = service.get_current_database_type()
        available_types = service.get_available_database_types()
        
        return {
            "current_database_type": current_type,
            "available_database_types": available_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库类型失败: {str(e)}")

@router.get("/dbstats")
async def get_database_stats(service: DataSourceService = Depends(get_data_source_service)):
    """获取数据库统计信息"""
    try:
        return service.get_database_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")