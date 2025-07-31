from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from services.simple_template_service import SimpleTemplateService
from pydantic import BaseModel

router = APIRouter()

class TemplatePromptRequest(BaseModel):
    template_id: str
    data_columns: List[str]

class CustomTemplateRequest(BaseModel):
    template_id: str
    template_config: Dict[str, Any]

class UpdateTemplateRequest(BaseModel):
    template_config: Dict[str, Any]

@router.get("/analysis")
async def get_analysis_templates():
    """获取分析模板列表"""
    try:
        template_service = SimpleTemplateService()
        templates = template_service.get_available_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-prompt")
async def generate_template_prompt(request: TemplatePromptRequest):
    """生成模板分析提示"""
    try:
        template_service = SimpleTemplateService()
        result = template_service.analyze_with_template(request.template_id)
        
        if result["success"]:
            return {
                "success": True,
                "prompt": result["analysis_prompt"]
            }
        else:
            return {
                "success": False,
                "error": result["error"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom")
async def add_custom_template(request: CustomTemplateRequest):
    """添加自定义模板"""
    try:
        template_service = SimpleTemplateService()
        success = template_service.add_custom_template(
            request.template_id, 
            request.template_config
        )
        
        if success:
            return {
                "success": True,
                "message": "自定义模板添加成功"
            }
        else:
            return {
                "success": False,
                "error": "添加自定义模板失败"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/custom/{template_id}")
async def update_custom_template(template_id: str, request: UpdateTemplateRequest):
    """更新自定义模板"""
    try:
        template_service = SimpleTemplateService()
        success = template_service.update_custom_template(
            template_id, 
            request.template_config
        )
        
        if success:
            return {
                "success": True,
                "message": "模板更新成功"
            }
        else:
            return {
                "success": False,
                "error": "模板不存在或更新失败"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/custom/{template_id}")
async def delete_custom_template(template_id: str):
    """删除自定义模板"""
    try:
        template_service = SimpleTemplateService()
        success = template_service.delete_custom_template(template_id)
        
        if success:
            return {
                "success": True,
                "message": "模板删除成功"
            }
        else:
            return {
                "success": False,
                "error": "模板不存在或删除失败"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/template/{template_id}")
async def get_template_detail(template_id: str):
    """获取模板详情"""
    try:
        template_service = SimpleTemplateService()
        template = template_service.get_template_by_id(template_id)
        
        if template:
            return {
                "success": True,
                "template": template
            }
        else:
            raise HTTPException(status_code=404, detail="模板不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))