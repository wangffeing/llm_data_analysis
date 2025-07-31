from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from services.report_generator import IntelligentReportGenerator, ReportConfig
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ReportGenerationRequest(BaseModel):
    analysis_results: Dict[str, Any]
    template_id: Optional[str] = None
    config: Dict[str, Any]

@router.post("/generate")
async def generate_intelligent_report(request: ReportGenerationRequest):
    """生成智能分析报告"""
    try:
        # 创建报告配置
        config = ReportConfig(
            include_executive_summary=request.config.get("include_executive_summary", True),
            include_detailed_analysis=request.config.get("include_detailed_analysis", True),
            include_recommendations=request.config.get("include_recommendations", True),
            language=request.config.get("language", "zh-CN")
        )
        
        # 生成报告
        generator = IntelligentReportGenerator(config)
        result = await generator.generate_comprehensive_report(
            request.analysis_results,
            request.template_id or "telecom_analysis"
        )
        
        if result["success"]:
            return {
                "success": True,
                "report": result["report"],
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "analysis_type": request.template_id or "通用分析",
                    "data_range": "全量数据"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))