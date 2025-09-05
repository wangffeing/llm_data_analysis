from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from taskweaver.memory.attachment import AttachmentType
from taskweaver.llm import LLMApi, format_chat_message
from session_manager import SessionManager
from .report_generator import ReportConfig

@dataclass
class DataAnalysisResults:
    """数据分析结果"""
    datasets_analyzed: List[Dict[str, Any]]
    data_summary: Dict[str, Any]
    key_findings: List[str]
    statistical_results: List[Dict[str, Any]]
    visualizations: List[Dict[str, Any]]
    business_insights: List[str]
    recommendations: List[str]
    methods_used: List[str]
    code_snippets: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    execution_outputs: List[Dict[str, Any]]

class EnhancedReportGenerator:
    """专业数据分析报告生成器"""
    
    # 报告章节配置
    SECTION_CONFIG = {
        'key_findings': {'title': '关键发现', 'item_type': '发现'},
        'business_insights': {'title': '业务洞察', 'item_type': '洞察'},
        'recommendations': {'title': '建议', 'item_type': '建议'}
    }
    
    # 数据提取模式
    EXTRACTION_PATTERNS = {
        'dataframe': [
            r'DataFrame.*?(\d+) rows.*?(\d+) columns',
            r'shape.*?\((\d+),\s*(\d+)\)',
            r'Index: (\d+) entries'
        ],
        'stats': [
            (r'mean\s*(\d+\.?\d*)', 'mean'),
            (r'std\s*(\d+\.?\d*)', 'std'),
            (r'min\s*(\d+\.?\d*)', 'min'),
            (r'max\s*(\d+\.?\d*)', 'max')
        ],
        'viz_keywords': ['plot', 'chart', 'figure', 'graph', 'visualization', '图表', '可视化'],
        'analysis_keywords': ['correlation', 'analysis', 'result', 'conclusion', '相关性', '分析', '结果', '结论']
    }
    
    def __init__(self, config: ReportConfig, session_id: str, session_manager: SessionManager):
        self.config = config
        self.session_id = session_id
        self.session_manager = session_manager
        self.llm_api: Optional[LLMApi] = None
        self.analysis_results: Optional[DataAnalysisResults] = None
        # 创建专用的LLM操作线程池
        self.llm_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="llm_ops")
    
    def _get_llm_api_from_session(self) -> Optional[LLMApi]:
        """从session中获取LLM API实例"""
        try:
            session_data = self.session_manager.get_session(self.session_id)
            taskweaver_app = session_data.get("taskweaver_app") if session_data else None
            return taskweaver_app.app_injector.get(LLMApi) if taskweaver_app else None
        except Exception as e:
            print(f"Warning: Could not get LLM API from session: {e}")
            return None
    
    async def generate_comprehensive_report(self, template_id: str = "comprehensive") -> Dict[str, Any]:
        """生成专业的数据分析报告"""
        try:
            self.llm_api = self._get_llm_api_from_session()
            self.analysis_results = await self._extract_analysis_results()
            report_content = await self._generate_professional_report()
            
            return {
                "success": True,
                "report": report_content,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "session_id": self.session_id,
                    "report_type": "data_analysis",
                    "datasets_count": len(self.analysis_results.datasets_analyzed),
                    "findings_count": len(self.analysis_results.key_findings),
                    "recommendations_count": len(self.analysis_results.recommendations)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _extract_analysis_results(self) -> DataAnalysisResults:
        """从TaskWeaver会话中提取数据分析结果"""
        session_data = self.session_manager.get_session(self.session_id)
        if not session_data or not session_data.get("taskweaver_session"):
            raise ValueError(f"Session {self.session_id} not found or not initialized")
        
        conversation = session_data["taskweaver_session"].memory.conversation
        
        # 初始化结果容器
        results = {
            'datasets_analyzed': [],
            'key_findings': [],
            'statistical_results': [],
            'visualizations': [],
            'methods_used': [],
            'code_snippets': [],
            'execution_outputs': []
        }
        
        print(f"开始分析会话数据，共有 {len(conversation.rounds)} 个对话轮次")
        
        # 遍历对话轮次提取数据
        for round_index, round_obj in enumerate(conversation.rounds):
            if not round_obj.user_query:
                continue
                
            for post in round_obj.post_list:
                if not hasattr(post, 'send_from'):
                    continue
                
                # 处理附件
                for attachment in getattr(post, 'attachment_list', []):
                    self._process_attachment(attachment, results, round_index)
                
                # 处理消息文本
                if hasattr(post, 'message') and post.send_from == "CodeInterpreter":
                    findings = self._extract_insights_from_text(post.message)
                    results['key_findings'].extend(findings)
        
        # 异步生成业务洞察和建议
        business_insights, recommendations = await self._generate_insights_and_recommendations_async(results)
        
        return DataAnalysisResults(
            datasets_analyzed=results['datasets_analyzed'],
            data_summary={},
            key_findings=results['key_findings'],
            statistical_results=results['statistical_results'],
            visualizations=results['visualizations'],
            business_insights=business_insights,
            recommendations=recommendations,
            methods_used=list(set(results['methods_used'])),
            code_snippets=results['code_snippets'],
            performance_metrics={},
            execution_outputs=results['execution_outputs']
        )
    
    def _process_attachment(self, attachment, results: Dict, round_index: int):
        """处理单个附件"""
        try:
            attachment_type = attachment.type
            content = getattr(attachment, 'content', '')
            
            if attachment_type == AttachmentType.execution_result:
                # 保存执行输出
                results['execution_outputs'].append({
                    'round': round_index + 1,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 提取结构化数据
                extracted = self._extract_data_from_content(content)
                if extracted:
                    data_type = extracted['type']
                    if data_type == 'dataframe_info':
                        results['datasets_analyzed'].append(extracted['data'])
                    elif data_type == 'statistical_summary':
                        results['statistical_results'].extend(extracted['data'])
                    elif data_type == 'visualization':
                        results['visualizations'].append(extracted['data'])
                    elif data_type == 'analysis_result':
                        results['key_findings'].extend(extracted['data'])
            
            elif attachment_type == AttachmentType.reply_content:
                code_info = self._extract_code_info(content)
                if code_info:
                    results['code_snippets'].append(code_info)
                    results['methods_used'].extend(code_info.get('methods', []))
                    
        except Exception as e:
            print(f"处理附件时出错: {e}")
    
    def _extract_data_from_content(self, content: str) -> Optional[Dict[str, Any]]:
        """从内容中提取结构化数据"""
        if not content:
            return None
        
        # 检查DataFrame信息
        for pattern in self.EXTRACTION_PATTERNS['dataframe']:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    return {
                        'type': 'dataframe_info',
                        'data': {
                            'rows': int(groups[0]),
                            'columns': int(groups[1]),
                            'description': f"数据集包含 {groups[0]} 行和 {groups[1]} 列"
                        }
                    }
                elif len(groups) >= 1:
                    return {
                        'type': 'dataframe_info',
                        'data': {
                            'entries': int(groups[0]),
                            'description': f"数据集包含 {groups[0]} 个条目"
                        }
                    }
        
        # 检查统计信息
        stats_found = []
        for pattern, stat_type in self.EXTRACTION_PATTERNS['stats']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                stats_found.append({'metric': stat_type, 'value': float(match)})
        
        if stats_found:
            return {'type': 'statistical_summary', 'data': stats_found}
        
        # 检查可视化
        if any(keyword in content.lower() for keyword in self.EXTRACTION_PATTERNS['viz_keywords']):
            return {
                'type': 'visualization',
                'data': {'description': '生成了数据可视化', 'content': content[:500]}
            }
        
        # 检查分析结果
        if any(keyword in content.lower() for keyword in self.EXTRACTION_PATTERNS['analysis_keywords']):
            sentences = [s.strip() for s in re.split(r'[.。\n]', content) 
                        if len(s.strip()) > 10 and any(k in s.lower() for k in self.EXTRACTION_PATTERNS['analysis_keywords'])]
            if sentences:
                return {'type': 'analysis_result', 'data': sentences[:3]}
        
        return None
    
    def _extract_code_info(self, content: str) -> Optional[Dict[str, Any]]:
        """提取代码信息"""
        if not content:
            return None
        
        # 提取代码块
        patterns = [r'```python\n(.*?)\n```', r'```\n(.*?)\n```', r'`([^`]+)`']
        code_blocks = []
        for pattern in patterns:
            code_blocks.extend(re.findall(pattern, content, re.DOTALL))
        
        if not code_blocks:
            return None
        
        # 识别使用的库
        libraries = ['pandas', 'numpy', 'matplotlib', 'seaborn', 'sklearn', 'scipy', 'plotly']
        methods = []
        for code in code_blocks:
            methods.extend([lib for lib in libraries if lib in code.lower()])
        
        return {
            'code': '\n'.join(code_blocks),
            'methods': list(set(methods)),
            'source': 'reply_content'
        }
    
    def _extract_insights_from_text(self, text: str) -> List[str]:
        """从文本中提取洞察"""
        patterns = [
            r'结论[：:](.+?)(?=\n|$)', r'发现[：:](.+?)(?=\n|$)', r'结果显示(.+?)(?=\n|$)',
            r'分析表明(.+?)(?=\n|$)', r'可以看出(.+?)(?=\n|$)', r'The analysis shows(.+?)(?=\n|$)',
            r'Results indicate(.+?)(?=\n|$)', r'We can see(.+?)(?=\n|$)'
        ]
        
        insights = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                insight = match.strip()
                if len(insight) > 10 and insight not in insights:
                    insights.append(insight)
        
        return insights
    
    def _sync_llm_call(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """同步LLM调用"""
        try:
            return self.llm_api.chat_completion(
                messages=messages,
                stream=False,
                temperature=kwargs.get('temperature', 0.3),
                max_tokens=kwargs.get('max_tokens', 800)
            )
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return {'content': ''}
    
    async def _generate_insights_and_recommendations_async(self, results: Dict) -> tuple[List[str], List[str]]:
        """异步生成业务洞察和建议"""
        if not self.llm_api or not (results['execution_outputs'] or results['key_findings']):
            return self._generate_rule_based_insights(results)
        
        # 构建上下文
        context_parts = []
        if results['datasets_analyzed']:
            context_parts.append("## 数据概况")
            for i, dataset in enumerate(results['datasets_analyzed'], 1):
                if 'rows' in dataset and 'columns' in dataset:
                    context_parts.append(f"数据集{i}: {dataset['rows']}行 x {dataset['columns']}列")
        
        if results['execution_outputs']:
            context_parts.append("\n## 分析结果")
            for i, output in enumerate(results['execution_outputs'][:3], 1):
                content = output.get('content', '')[:200]
                context_parts.append(f"结果{i}: {content}")
        
        if results['key_findings']:
            context_parts.append("\n## 关键发现")
            for finding in results['key_findings'][:5]:
                context_parts.append(f"- {finding}")
        
        context = "\n".join(context_parts)
        
        if len(context.strip()) < 50:
            return self._generate_rule_based_insights(results)
        
        # 异步LLM生成
        prompt = f"""
作为数据分析师，基于以下分析结果提供业务洞察和建议：

{context}

请严格按照JSON格式返回：
{{
    "insights": ["洞察1", "洞察2", "洞察3"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
        
        try:
            messages = [format_chat_message("user", prompt)]
            
            # 在线程池中执行同步LLM调用
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.llm_executor,
                self._sync_llm_call,
                messages,
                {'temperature': 0.3, 'max_tokens': 800}
            )
            
            content = response.get('content', '').strip()
            if not content:
                raise ValueError("LLM返回空响应")
            
            # 提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                raise ValueError("无法找到JSON格式")
            
            result = json.loads(json_match.group())
            return result.get('insights', []), result.get('recommendations', [])
            
        except Exception as e:
            print(f"异步LLM生成失败: {e}")
            return self._generate_rule_based_insights(results)
    
    def _generate_rule_based_insights(self, results: Dict) -> tuple[List[str], List[str]]:
        """基于规则生成洞察和建议"""
        insights = []
        recommendations = []
        
        # 基于数据集生成洞察
        if results['datasets_analyzed']:
            total_rows = sum(d.get('rows', 0) for d in results['datasets_analyzed'])
            if total_rows > 0:
                insights.append(f"本次分析处理了 {total_rows:,} 条数据记录")
        
        # 基于执行输出生成洞察
        if results['execution_outputs']:
            insights.append(f"完成了 {len(results['execution_outputs'])} 个分析步骤")
            
            # 检查关键词
            all_content = ' '.join(output.get('content', '') for output in results['execution_outputs'])
            if 'chart' in all_content.lower() or '图表' in all_content:
                insights.append("生成了数据可视化图表，有助于直观理解数据趋势")
            if 'sql' in all_content.lower():
                insights.append("使用了SQL查询进行数据提取和处理")
        
        # 基于发现生成洞察
        if results['key_findings']:
            insights.append(f"识别出 {len(results['key_findings'])} 个关键业务发现")
        
        # 生成建议
        recommendations.extend([
            "建议定期进行类似的数据分析，持续监控业务指标",
            "可以考虑将分析结果应用到业务决策中",
            "建议建立数据驱动的决策流程"
        ])
        
        return insights[:5], recommendations[:5]  # 限制数量
    
    async def _generate_professional_report(self) -> str:
        """生成专业报告"""
        results = self.analysis_results
        report_lines = [
            "# 数据分析报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**会话ID**: {self.session_id}",
            "",
            "## 执行摘要",
            "",
            self._generate_executive_summary(),
            ""
        ]
        
        # 动态添加章节
        sections = [
            ('datasets_analyzed', '数据概况', self._generate_data_overview),
            ('execution_outputs', '分析结果', self._generate_analysis_results_section),
            ('key_findings', '关键发现', lambda: self._generate_list_section('key_findings')),
            ('statistical_results', '统计分析', self._generate_statistical_section),
            ('business_insights', '业务洞察', lambda: self._generate_list_section('business_insights')),
            ('recommendations', '建议', lambda: self._generate_list_section('recommendations')),
            ('methods_used', '技术附录', self._generate_technical_appendix)
        ]
        
        for field, title, generator in sections:
            if getattr(results, field):
                report_lines.extend([f"## {title}", "", generator(), ""])
        
        return "\n".join(report_lines)
    
    def _generate_executive_summary(self) -> str:
        """生成执行摘要"""
        results = self.analysis_results
        parts = []
        
        if results.datasets_analyzed:
            total_rows = sum(d.get('rows', 0) for d in results.datasets_analyzed)
            parts.append(f"本次分析涉及 {len(results.datasets_analyzed)} 个数据集")
            if total_rows > 0:
                parts.append(f"，总计 **{total_rows:,}** 条记录。")
        
        if results.key_findings:
            parts.append(f"\n获得了 **{len(results.key_findings)}** 个关键发现")
        
        if results.business_insights:
            parts.append(f"，提炼出 **{len(results.business_insights)}** 个重要业务洞察。")
        
        # 核心结论
        if results.key_findings:
            parts.append("\n\n**核心结论**:")
            for i, finding in enumerate(results.key_findings[:2], 1):
                parts.append(f"\n{i}. {finding}")
        
        return "".join(parts) if parts else "本次数据分析已完成，详细结果请参见下文各章节。"
    
    def _generate_data_overview(self) -> str:
        """生成数据概况"""
        parts = ["### 数据集信息", ""]
        for i, dataset in enumerate(self.analysis_results.datasets_analyzed, 1):
            if 'rows' in dataset and 'columns' in dataset:
                parts.append(f"**数据集 {i}**: {dataset['rows']:,} 行 × {dataset['columns']} 列")
            elif 'entries' in dataset:
                parts.append(f"**数据集 {i}**: {dataset['entries']:,} 个条目")
            if 'description' in dataset:
                parts.append(f"  - {dataset['description']}")
        return "\n".join(parts)
    
    def _generate_analysis_results_section(self) -> str:
        """生成分析结果章节"""
        parts = []
        for i, output in enumerate(self.analysis_results.execution_outputs, 1):
            clean_output = output.get('content', '').strip()
            if len(clean_output) > 1000:
                clean_output = clean_output[:1000] + "..."
            parts.extend([f"### 分析步骤 {i}", "```", clean_output, "```", ""])
        return "\n".join(parts)
    
    def _generate_list_section(self, field_name: str) -> str:
        """通用列表章节生成"""
        items = getattr(self.analysis_results, field_name, [])
        config = self.SECTION_CONFIG.get(field_name, {'item_type': '项目'})
        item_type = config['item_type']
        
        parts = []
        for i, item in enumerate(items, 1):
            parts.extend([f"**{item_type} {i}**: {item}", ""])
        return "\n".join(parts)
    
    def _generate_statistical_section(self) -> str:
        """生成统计分析章节"""
        parts = []
        stats_by_type = {}
        
        # 按类型分组统计结果
        for stat in self.analysis_results.statistical_results:
            metric = stat.get('metric', 'unknown')
            if metric not in stats_by_type:
                stats_by_type[metric] = []
            stats_by_type[metric].append(stat)
        
        # 生成统计摘要
        for metric, stats in stats_by_type.items():
            values = [s.get('value', 0) for s in stats]
            if values:
                parts.extend([
                    f"**{metric.upper()}**: {', '.join(map(str, values))}",
                    ""
                ])
        
        return "\n".join(parts) if parts else "暂无统计分析结果。"
    
    def _generate_technical_appendix(self) -> str:
        """生成技术附录"""
        results = self.analysis_results
        parts = ["### 使用的工具和方法", ""]
        
        if self.analysis_results.methods_used:
            parts.append("**数据处理库**:")
            for method in sorted(set(self.analysis_results.methods_used)):
                parts.append(f"- {method}")
            parts.append("")
        
        if self.analysis_results.code_snippets:
            parts.extend(["### 关键代码片段", ""])
            for i, snippet in enumerate(self.analysis_results.code_snippets[:3], 1):
                code = snippet.get('code', '').strip()
                if len(code) > 500:
                    code = code[:500] + "..."
                parts.extend([
                    f"**代码片段 {i}**:",
                    "```python",
                    code,
                    "```",
                    ""
                ])
        
        return "\n".join(parts)
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'llm_executor'):
            self.llm_executor.shutdown(wait=False)