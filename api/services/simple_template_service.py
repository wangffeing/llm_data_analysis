import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

class SimpleTemplateService:
    def __init__(self):
        self.templates_file = Path("templates/simple_templates.json")
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """加载模板配置"""
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """获取可用模板列表 - 返回完整的模板结构"""
        templates_list = []
        for template_id, template_config in self.templates.items():
            # 直接返回完整的模板结构，添加id字段
            template_with_id = {
                "id": template_id,
                "template_metadata": template_config.get("template_metadata", {}),
                "data_schema": template_config.get("data_schema", {}),
                "execution_plan": template_config.get("execution_plan", {}),
                "output_specification": template_config.get("output_specification", {})
            }
            templates_list.append(template_with_id)
        return templates_list
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取模板详情 - 直接返回原始JSON结构"""
        template_config = self.templates.get(template_id)
        if not template_config:
            return None
            
        # 直接返回原始JSON结构，添加id字段
        result = {
            "id": template_id,
            "template_metadata": template_config.get("template_metadata", {}),
            "data_schema": template_config.get("data_schema", {}),
            "execution_plan": template_config.get("execution_plan", {}),
            "output_specification": template_config.get("output_specification", {})
        }
        
        return result
            
    def generate_analysis_prompt(self, template_id: str) -> str:
        """生成分析提示词 - 适配新的模板格式"""
        template = self.templates.get(template_id)
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
            self.templates[template_id] = template_config
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"添加模板失败: {e}")
            return False
    
    def update_custom_template(self, template_id: str, template_config: Dict[str, Any]) -> bool:
        """更新自定义模板"""
        try:
            if template_id in self.templates:
                self.templates[template_id] = template_config
                with open(self.templates_file, 'w', encoding='utf-8') as f:
                    json.dump(self.templates, f, ensure_ascii=False, indent=2)
                return True
            return False
        except Exception as e:
            print(f"更新模板失败: {e}")
            return False
    
    def delete_custom_template(self, template_id: str) -> bool:
        """删除自定义模板"""
        try:
            if template_id in self.templates:
                del self.templates[template_id]
                with open(self.templates_file, 'w', encoding='utf-8') as f:
                    json.dump(self.templates, f, ensure_ascii=False, indent=2)
                return True
            return False
        except Exception as e:
            print(f"删除模板失败: {e}")
            return False