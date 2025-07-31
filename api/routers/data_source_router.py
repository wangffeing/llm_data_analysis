import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import py_opengauss
from data_sources_config import DATA_SOURCES
from models.chat_models import DataSource, DataSourcesResponse
from dependencies import get_db_connection
from services.data_source_service import DataSourceService
from anyio import to_thread
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# 请求模型
class DataSourceCreateRequest(BaseModel):
    name: str
    table_name: str
    table_des: str
    table_order: str
    table_columns: List[str]
    table_columns_names: List[str]

class DataSourceUpdateRequest(BaseModel):
    table_name: str
    table_des: str
    table_order: str
    table_columns: List[str]
    table_columns_names: List[str]

# 依赖注入
def get_data_source_service() -> DataSourceService:
    return DataSourceService()

@router.get("/sources", response_model=DataSourcesResponse)
async def get_data_sources(service: DataSourceService = Depends(get_data_source_service)):
    """获取所有数据源"""
    try:
        # 使用service动态获取最新的数据源配置，而不是静态导入的DATA_SOURCES
        data_sources_dict = service.get_all_data_sources()
        data_sources_list = []
        
        for name, config in data_sources_dict.items():
            data_source = DataSource(
                name=name,
                table_name=config["table_name"],
                description=config.get("table_des", name),
                table_columns=config["table_columns"],
                table_columns_names=config["table_columns_names"],
                table_order=config.get("table_order")
            )
            data_sources_list.append(data_source)

        return DataSourcesResponse(data_sources=data_sources_list)
    except Exception as e:
        logger.error(f"获取数据源失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取数据源失败")

@router.post("/sources")
async def create_data_source(
    request: DataSourceCreateRequest,
    service: DataSourceService = Depends(get_data_source_service)
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
            "table_columns_names": request.table_columns_names
        }
        
        success = service.add_data_source(request.name, config)
        if success:
            return {"success": True, "message": "数据源创建成功"}
        else:
            raise HTTPException(status_code=500, detail="数据源创建失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建数据源失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建数据源失败")

@router.put("/sources/{source_name}")
async def update_data_source(
    source_name: str,
    request: DataSourceUpdateRequest,
    service: DataSourceService = Depends(get_data_source_service)
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
            "table_columns_names": request.table_columns_names
        }
        
        success = service.update_data_source(source_name, config)
        if success:
            return {"success": True, "message": "数据源更新成功"}
        else:
            raise HTTPException(status_code=500, detail="数据源更新失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数据源失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新数据源失败")

@router.delete("/sources/{source_name}")
async def delete_data_source(
    source_name: str,
    service: DataSourceService = Depends(get_data_source_service)
):
    """删除数据源"""
    try:
        # 检查数据源是否存在
        if not service.get_data_source(source_name):
            raise HTTPException(status_code=404, detail="数据源不存在")
        
        success = service.delete_data_source(source_name)
        if success:
            return {"success": True, "message": "数据源删除成功"}
        else:
            raise HTTPException(status_code=500, detail="数据源删除失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据源失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除数据源失败")

@router.get("/sources/{source_name}/preview")
async def get_data_preview(source_name: str, limit: int = 5):
    """获取数据预览"""
    try:
        if source_name not in DATA_SOURCES:
            raise HTTPException(status_code=404, detail="数据源不存在")

        source = DATA_SOURCES[source_name]
        table_name = source['table_name']
        table_columns = ','.join(source['table_columns'])

        query = f"SELECT {table_columns} FROM {table_name} LIMIT {limit}"

        def query_db():
            db_connection = get_db_connection()
            try:
                get_table = db_connection.prepare(query)
                return get_table()
            finally:
                db_connection.close()

        result = await to_thread.run_sync(query_db)

        return {
            "source_name": source_name,
            "columns": source['table_columns_names'],
            "data": result,
            "total_shown": len(result)
        }

    except Exception as e:
        logger.error(f"获取数据预览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取数据预览失败") from e