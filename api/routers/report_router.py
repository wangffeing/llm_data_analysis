from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from services.enhanced_report_generator import EnhancedReportGenerator
from services.report_generator import ReportConfig
from dependencies import get_session_manager
from session_manager import SessionManager

router = APIRouter()

class ReportGenerationRequest(BaseModel):
    session_id: str
    template_id: Optional[str] = "comprehensive"
    config: Optional[Dict[str, Any]] = None

@router.post("/generate")
async def generate_intelligent_report(
    request: ReportGenerationRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """生成智能报告"""
    try:
        # 创建报告配置
        config = ReportConfig(
            **(request.config or {})
        )
        
        # 创建增强报告生成器，传入SessionManager实例
        generator = EnhancedReportGenerator(
            config=config,
            session_id=request.session_id,
            session_manager=session_manager  # 使用依赖注入的SessionManager
        )
        
        # 生成报告
        result = await generator.generate_comprehensive_report(
            template_id=request.template_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "report": result["report"],
                "metadata": result["metadata"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")

@router.get("/templates")
async def get_report_templates():
    """获取可用的报告模板"""
    return {
        "templates": [
            {
                "id": "comprehensive",
                "name": "综合分析报告",
                "description": "包含完整分析过程和深度洞察的综合报告"
            },
            {
                "id": "executive",
                "name": "执行摘要报告",
                "description": "面向管理层的简洁摘要报告"
            },
            {
                "id": "technical",
                "name": "技术详细报告",
                "description": "包含详细技术实现和代码分析的报告"
            }
        ]
    }

@router.get("/status/{session_id}")
async def get_report_status(session_id: str):
    """获取报告生成状态"""
    # 这里可以实现报告生成状态查询
    return {
        "session_id": session_id,
        "status": "ready",
        "message": "可以生成报告"
    }