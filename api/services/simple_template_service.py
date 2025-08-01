import pandas as pd
from typing import Dict, List, Any, Optional
from services.template_database_service import TemplateDatabaseService

class SimpleTemplateService:
    def __init__(self, db_path: str = None):
        """
        初始化模板服务 - 完全使用数据库模式
        修复：如果没有提供 db_path，则从配置文件读取
        """
        if db_path is None:
            from config import get_config
            config = get_config()
            db_path = config.config_db_path
            
        self.template_db_service = TemplateDatabaseService(db_path)
        
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """获取可用模板列表"""
        templates_dict = self.template_db_service.get_all_templates()
        templates_list = []
        for template_id, template_config in templates_dict.items():
            template_with_id = {
                "id": template_id,
                **template_config
            }
            templates_list.append(template_with_id)
        return templates_list

    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取模板详情"""
        templates_dict = self.template_db_service.get_all_templates()
        template_config = templates_dict.get(template_id)
        if not template_config:
            return None
        return {
            "id": template_id,
            **template_config
        }
            
    def generate_analysis_prompt(self, template_id: str) -> str:
        """生成分析提示词"""
        templates_dict = self.template_db_service.get_all_templates()
        template = templates_dict.get(template_id)
            
        if not template:
            return "模板不存在"
        
        # 提取模板各部分
        metadata = template.get("template_metadata", {})
        data_schema = template.get("data_schema", {})
        execution_plan = template.get("execution_plan", {})
        output_spec = template.get("output_specification", {})
        
        # 模板基本信息
        prompt = f"## 任务描述\n{metadata.get('summary', '')}\n\n"
        
        # 分析目标
        prompt += f"## 分析目标\n{execution_plan.get('analysis_goal', '')}\n\n"
        
        # 数据要求
        prompt += "## 数据要求\n"
        prompt += "**必需列：**\n"
        for col in data_schema.get("required_columns", []):
            prompt += f"- `{col['name']}` ({col['type']}): {col['description']}\n"
        
        prompt += "\n**可选列：**\n"
        for col in data_schema.get("optional_columns", []):
            prompt += f"- `{col['name']}` ({col['type']}): {col['description']}\n"
        prompt += "\n"
        
        # 执行步骤
        prompt += "## 执行步骤\n"
        for i, step in enumerate(execution_plan.get("steps", []), 1):
            prompt += f"{step['prompt']}\n"
            if step.get('save_to_variable'):
                prompt += f"**保存变量：** `{step['save_to_variable']}`\n"
            prompt += "\n"
        
        # 输出要求
        prompt += "## 输出要求\n"
        insights_template = output_spec.get("insights_template", "")
        if insights_template:
            prompt += "**报告格式：**\n"
            prompt += f"```\n{insights_template}\n```\n\n"
        
        prompt += "## 生成文件\n"
        for file_spec in output_spec.get("files", []):
            prompt += f"- 文件名: {file_spec['title']}，文件类型: ({file_spec['type']})，来源数据: ({file_spec['source_variable']}), 保存工具: ({file_spec['tool']})\n"
        
        # 最终要求
        prompt += "\n## 重要提醒\n"
        prompt += "1. 严格按照以上步骤执行分析\n"
        prompt += "2. 确保所有变量都被正确保存和使用\n"
        prompt += "3. 最终报告要使用指定的模板格式\n"
        prompt += "4. 如果遇到条件性步骤，请根据数据情况决定是否执行\n"
        
        return prompt
    
    def analyze_with_template(self, template_id: str) -> Dict[str, Any]:
        """使用模板分析数据"""
        try:
            prompt = self.generate_analysis_prompt(template_id)
            return {
                "success": True,
                "analysis_prompt": prompt
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"生成分析提示失败: {str(e)}"
            }
    
    def add_custom_template(self, template_id: str, template_config: Dict[str, Any]) -> bool:
        """添加自定义模板"""
        try:
            return self.template_db_service.add_template(template_id, template_config)
        except Exception as e:
            print(f"添加模板失败: {e}")
            return False
    
    def update_custom_template(self, template_id: str, template_config: Dict[str, Any]) -> bool:
        """更新自定义模板"""
        try:
            return self.template_db_service.update_template(template_id, template_config)
        except Exception as e:
            print(f"更新模板失败: {e}")
            return False
    
    def delete_custom_template(self, template_id: str) -> bool:
        """删除自定义模板"""
        try:
            return self.template_db_service.delete_template(template_id, template_config)
        except Exception as e:
            print(f"删除模板失败: {e}")
            return False