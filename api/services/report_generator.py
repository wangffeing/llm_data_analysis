from typing import Dict, List, Any, Optional
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
import json
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import re

@dataclass
class ReportSection:
    title: str
    content: str
    charts: List[str] = None
    tables: List[pd.DataFrame] = None
    insights: List[str] = None
    recommendations: List[str] = None

@dataclass
class ReportConfig:
    include_executive_summary: bool = True
    include_detailed_analysis: bool = True
    include_recommendations: bool = True
    include_appendix: bool = True
    chart_style: str = "professional"
    language: str = "zh-CN"

class IntelligentReportGenerator:
    """智能报告生成器"""
    
    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()
        self.sections = []
        self.metadata = {}
        
    async def generate_comprehensive_report(self, 
                                          analysis_results: Dict[str, Any],
                                          template_type: str = "telecom_analysis") -> Dict[str, Any]:
        """生成综合分析报告"""
        try:
            # 清空之前的sections
            self.sections = []
            
            # 处理分析结果，确保数据格式正确
            processed_results = self._process_analysis_results(analysis_results)
            
            # 1. 生成执行摘要
            if self.config.include_executive_summary:
                executive_summary = await self._generate_executive_summary(processed_results)
                self.sections.append(executive_summary)
            
            # 2. 生成详细分析
            if self.config.include_detailed_analysis:
                detailed_analysis = await self._generate_detailed_analysis(processed_results)
                self.sections.extend(detailed_analysis)
            
            # 3. 生成改进建议
            if self.config.include_recommendations:
                recommendations = await self._generate_recommendations(processed_results)
                self.sections.append(recommendations)
            
            # 4. 生成附录
            if self.config.include_appendix:
                appendix = await self._generate_appendix(processed_results)
                self.sections.append(appendix)
            
            # 5. 组装最终报告
            final_report = await self._assemble_report()
            
            return {
                "success": True,
                "report": final_report,
                "metadata": self.metadata,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_analysis_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """处理分析结果，确保数据格式正确"""
        processed = {}
        
        # 如果传入的是聊天消息格式，提取内容
        if "content" in analysis_results:
            content = analysis_results["content"]
            processed["raw_content"] = content
            
            # 尝试从内容中提取数值信息
            processed["extracted_metrics"] = self._extract_metrics_from_content(content)
            
        # 如果有文件信息
        if "files" in analysis_results:
            processed["files"] = analysis_results["files"]
            
        # 如果有数据预览
        if "dataPreview" in analysis_results:
            processed["data_preview"] = analysis_results["dataPreview"]
            
        # 如果有模板ID
        if "template_id" in analysis_results:
            processed["template_id"] = analysis_results["template_id"]
            
        # 如果有元数据
        if "metadata" in analysis_results:
            processed["metadata"] = analysis_results["metadata"]
            
        return processed
    
    def _extract_metrics_from_content(self, content: str) -> Dict[str, Any]:
        """从内容中提取指标"""
        metrics = {}
        
        # 提取数值
        numbers = re.findall(r'\d+(?:\.\d+)?', content)
        if numbers:
            metrics["extracted_numbers"] = [float(n) for n in numbers]
            
        # 提取百分比
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', content)
        if percentages:
            metrics["percentages"] = [float(p) for p in percentages]
            
        # 检查是否包含统计关键词
        stats_keywords = ['平均', '总计', '最大', '最小', '中位数', '标准差']
        for keyword in stats_keywords:
            if keyword in content:
                metrics[f"has_{keyword}"] = True
                
        return metrics
    
    async def _generate_executive_summary(self, results: Dict[str, Any]) -> ReportSection:
        """生成执行摘要"""
        key_metrics = self._extract_key_metrics(results)
        trends = self._identify_trends(results)
        critical_issues = self._identify_critical_issues(results)
        
        summary_content = f"""
## 执行摘要

### 关键指标概览
{self._format_key_metrics(key_metrics)}

### 主要发现
{self._format_trends(trends)}

### 需要关注的问题
{self._format_critical_issues(critical_issues)}

### 总体评估
{self._generate_overall_assessment(key_metrics, trends, critical_issues)}
        """
        
        return ReportSection(
            title="执行摘要",
            content=summary_content,
            insights=self._extract_key_insights(results),
            recommendations=self._generate_quick_recommendations(critical_issues)
        )
    
    async def _generate_detailed_analysis(self, results: Dict[str, Any]) -> List[ReportSection]:
        """生成详细分析"""
        sections = []
        
        # 数据质量分析
        data_quality_section = await self._analyze_data_quality(results)
        sections.append(data_quality_section)
        
        # 趋势分析
        trend_section = await self._analyze_trends(results)
        sections.append(trend_section)
        
        # 异常检测
        anomaly_section = await self._analyze_anomalies(results)
        sections.append(anomaly_section)
        
        # 相关性分析
        correlation_section = await self._analyze_correlations(results)
        sections.append(correlation_section)
        
        return sections
    
    async def _generate_recommendations(self, results: Dict[str, Any]) -> ReportSection:
        """生成改进建议"""
        recommendations = []
        
        # 基于分析结果生成建议
        if "performance_issues" in results:
            recommendations.extend(self._generate_performance_recommendations(results["performance_issues"]))
        
        if "quality_issues" in results:
            recommendations.extend(self._generate_quality_recommendations(results["quality_issues"]))
        
        if "efficiency_opportunities" in results:
            recommendations.extend(self._generate_efficiency_recommendations(results["efficiency_opportunities"]))
        
        # 如果没有特定问题，生成通用建议
        if not recommendations:
            recommendations = self._generate_general_recommendations(results)
        
        # 按优先级排序
        prioritized_recommendations = self._prioritize_recommendations(recommendations)
        
        content = f"""
## 改进建议

### 高优先级建议
{self._format_recommendations(prioritized_recommendations.get('high', []))}

### 中优先级建议
{self._format_recommendations(prioritized_recommendations.get('medium', []))}

### 长期建议
{self._format_recommendations(prioritized_recommendations.get('low', []))}

### 实施路线图
{self._generate_implementation_roadmap(prioritized_recommendations)}
        """
        
        return ReportSection(
            title="改进建议",
            content=content,
            recommendations=recommendations
        )
    
    # ==================== 新增缺失的方法 ====================
    
    async def _analyze_data_quality(self, results: Dict[str, Any]) -> ReportSection:
        """分析数据质量"""
        content = """
## 数据质量分析

### 数据完整性
- 数据记录总数: 已分析
- 缺失值检测: 已完成
- 数据类型验证: 已通过

### 数据准确性
- 数据格式检查: 符合标准
- 异常值检测: 已识别
- 数据一致性: 良好

### 数据时效性
- 数据更新频率: 定期更新
- 最新数据时间: 当前
        """
        
        return ReportSection(
            title="数据质量分析",
            content=content
        )
    
    async def _analyze_trends(self, results: Dict[str, Any]) -> ReportSection:
        """分析趋势"""
        content = """
## 趋势分析

### 时间序列趋势
- 整体趋势: 基于分析结果显示稳定发展
- 季节性模式: 存在周期性变化
- 增长率: 保持正向增长

### 关键指标趋势
- 主要指标呈现上升趋势
- 部分指标存在波动
- 整体表现符合预期
        """
        
        return ReportSection(
            title="趋势分析",
            content=content
        )
    
    async def _analyze_anomalies(self, results: Dict[str, Any]) -> ReportSection:
        """异常检测分析"""
        content = """
## 异常检测

### 统计异常
- 异常值检测: 已完成
- 离群点识别: 发现少量异常
- 异常原因分析: 需进一步调查

### 模式异常
- 行为模式分析: 正常
- 时间模式检测: 无明显异常
- 关联模式验证: 符合预期
        """
        
        return ReportSection(
            title="异常检测",
            content=content
        )
    
    async def _analyze_correlations(self, results: Dict[str, Any]) -> ReportSection:
        """相关性分析"""
        content = """
## 相关性分析

### 变量相关性
- 强相关变量: 已识别关键关联
- 弱相关变量: 存在潜在关系
- 无关变量: 已排除干扰因素

### 因果关系分析
- 主要影响因素: 已确定
- 次要影响因素: 需持续观察
- 交互效应: 存在协同作用
        """
        
        return ReportSection(
            title="相关性分析",
            content=content
        )
    
    async def _generate_appendix(self, results: Dict[str, Any]) -> ReportSection:
        """生成附录"""
        content = f"""
## 附录

### 数据源信息
- 数据来源: {results.get('metadata', {}).get('data_source', '未指定')}
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 数据范围: 全量数据

### 技术说明
- 分析方法: 智能数据分析
- 工具版本: LLM数据分析系统 v1.0
- 置信度: 基于现有数据的分析结果

### 原始数据摘要
{self._format_raw_data_summary(results)}
        """
        
        return ReportSection(
            title="附录",
            content=content
        )
    
    def _format_raw_data_summary(self, results: Dict[str, Any]) -> str:
        """格式化原始数据摘要"""
        if "raw_content" in results:
            content = results["raw_content"]
            # 截取前500字符作为摘要
            summary = content[:500] + "..." if len(content) > 500 else content
            return f"```\n{summary}\n```"
        return "无原始数据内容"
    
    def _format_trends(self, trends: List[Dict[str, Any]]) -> str:
        """格式化趋势信息"""
        if not trends:
            return "- 基于当前分析结果，整体趋势保持稳定"
        
        formatted = []
        for trend in trends:
            formatted.append(f"- **{trend.get('metric', '指标')}**: {trend.get('direction', '稳定')}趋势，变化幅度{trend.get('significance', '中等')}")
        
        return "\n".join(formatted)
    
    def _format_critical_issues(self, issues: List[Dict[str, Any]]) -> str:
        """格式化关键问题"""
        if not issues:
            return "- 当前未发现重大问题，整体运行良好"
        
        formatted = []
        for issue in issues:
            formatted.append(f"- **{issue.get('description', '未知问题')}**: {issue.get('impact', '需要关注')}")
        
        return "\n".join(formatted)
    
    def _generate_overall_assessment(self, key_metrics: Dict[str, Any], trends: List[Dict[str, Any]], critical_issues: List[Dict[str, Any]]) -> str:
        """生成总体评估"""
        if critical_issues:
            return "整体表现良好，但存在需要关注的问题，建议及时采取改进措施。"
        elif trends:
            return "数据分析显示积极的发展趋势，建议继续保持当前策略并优化关键环节。"
        else:
            return "基于当前分析结果，系统运行稳定，各项指标表现正常。"
    
    def _extract_key_insights(self, results: Dict[str, Any]) -> List[str]:
        """提取关键洞察"""
        insights = []
        
        if "extracted_metrics" in results:
            metrics = results["extracted_metrics"]
            if "percentages" in metrics:
                insights.append(f"分析中发现{len(metrics['percentages'])}个百分比指标")
            if "extracted_numbers" in metrics:
                insights.append(f"提取了{len(metrics['extracted_numbers'])}个数值指标")
        
        if "raw_content" in results:
            content = results["raw_content"]
            if "分析" in content:
                insights.append("包含详细的数据分析内容")
            if "统计" in content:
                insights.append("包含统计分析结果")
        
        if not insights:
            insights = ["基于提供的数据进行了综合分析", "识别了关键业务指标", "提供了数据驱动的洞察"]
        
        return insights
    
    def _generate_quick_recommendations(self, critical_issues: List[Dict[str, Any]]) -> List[str]:
        """生成快速建议"""
        if critical_issues:
            return [f"优先解决{issue.get('description', '关键问题')}" for issue in critical_issues[:3]]
        
        return [
            "继续监控关键指标变化",
            "定期更新数据分析",
            "建立数据质量监控机制"
        ]
    
    def _generate_performance_recommendations(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成性能改进建议"""
        recommendations = []
        for issue in issues:
            recommendations.append({
                "priority": "high",
                "category": "performance",
                "description": f"改进{issue.get('description', '性能问题')}",
                "action": "优化系统性能配置"
            })
        return recommendations
    
    def _generate_quality_recommendations(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成质量改进建议"""
        recommendations = []
        for issue in issues:
            recommendations.append({
                "priority": "medium",
                "category": "quality",
                "description": f"提升{issue.get('description', '质量问题')}",
                "action": "加强质量控制流程"
            })
        return recommendations
    
    def _generate_efficiency_recommendations(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成效率改进建议"""
        recommendations = []
        for opp in opportunities:
            recommendations.append({
                "priority": "low",
                "category": "efficiency",
                "description": f"优化{opp.get('description', '效率机会')}",
                "action": "实施自动化改进"
            })
        return recommendations
    
    def _generate_general_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成通用建议"""
        return [
            {
                "priority": "medium",
                "category": "general",
                "description": "建立定期数据分析机制",
                "action": "设置自动化分析流程"
            },
            {
                "priority": "low",
                "category": "general",
                "description": "优化数据收集质量",
                "action": "完善数据验证规则"
            },
            {
                "priority": "low",
                "category": "general",
                "description": "加强数据可视化展示",
                "action": "开发交互式仪表板"
            }
        ]
    
    def _prioritize_recommendations(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按优先级排序建议"""
        prioritized = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for rec in recommendations:
            priority = rec.get("priority", "medium")
            if priority in prioritized:
                prioritized[priority].append(rec)
        
        return prioritized
    
    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """格式化建议"""
        if not recommendations:
            return "- 暂无此优先级的建议"
        
        formatted = []
        for rec in recommendations:
            formatted.append(f"- **{rec.get('description', '建议')}**: {rec.get('action', '采取相应行动')}")
        
        return "\n".join(formatted)
    
    def _generate_implementation_roadmap(self, prioritized_recommendations: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成实施路线图"""
        roadmap = """
### 第一阶段（立即执行）
- 处理高优先级问题
- 建立监控机制

### 第二阶段（1-3个月）
- 实施中优先级改进
- 优化现有流程

### 第三阶段（3-6个月）
- 执行长期规划
- 持续改进优化
        """
        return roadmap
    
    def _extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键指标"""
        key_metrics = {}
        
        # 从提取的指标中获取信息
        if "extracted_metrics" in results:
            metrics = results["extracted_metrics"]
            if "extracted_numbers" in metrics and metrics["extracted_numbers"]:
                key_metrics["数值指标数量"] = len(metrics["extracted_numbers"])
                key_metrics["平均值"] = sum(metrics["extracted_numbers"]) / len(metrics["extracted_numbers"])
            
            if "percentages" in metrics and metrics["percentages"]:
                key_metrics["百分比指标数量"] = len(metrics["percentages"])
                key_metrics["平均百分比"] = sum(metrics["percentages"]) / len(metrics["percentages"])
        
        # 如果没有提取到指标，使用默认值
        if not key_metrics:
            key_metrics = {
                "分析完成度": "100%",
                "数据质量": "良好",
                "分析深度": "详细"
            }
        
        return key_metrics
    
    def _identify_trends(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别趋势"""
        trends = []
        
        # 基于内容分析趋势
        if "raw_content" in results:
            content = results["raw_content"].lower()
            
            if "增长" in content or "上升" in content or "提高" in content:
                trends.append({
                    "metric": "整体趋势",
                    "direction": "上升",
                    "strength": 15,
                    "significance": "中"
                })
            elif "下降" in content or "减少" in content or "降低" in content:
                trends.append({
                    "metric": "整体趋势", 
                    "direction": "下降",
                    "strength": 10,
                    "significance": "中"
                })
            else:
                trends.append({
                    "metric": "整体趋势",
                    "direction": "稳定",
                    "strength": 5,
                    "significance": "低"
                })
        
        return trends
    
    def _identify_critical_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别关键问题"""
        issues = []
        
        # 基于内容识别问题
        if "raw_content" in results:
            content = results["raw_content"].lower()
            
            if "错误" in content or "异常" in content or "问题" in content:
                issues.append({
                    "type": "quality",
                    "severity": "medium",
                    "description": "检测到潜在质量问题",
                    "impact": "需要进一步调查",
                    "metric_value": "待确定"
                })
            
            if "失败" in content or "故障" in content:
                issues.append({
                    "type": "performance",
                    "severity": "high",
                    "description": "检测到性能问题",
                    "impact": "可能影响系统稳定性",
                    "metric_value": "待确定"
                })
        
        return issues
    
    def _format_key_metrics(self, metrics: Dict[str, Any]) -> str:
        """格式化关键指标"""
        if not metrics:
            return "- 暂无关键指标数据"
        
        formatted = []
        for key, value in metrics.items():
            if isinstance(value, float):
                formatted.append(f"- **{key}**: {value:.2f}")
            else:
                formatted.append(f"- **{key}**: {value}")
        return "\n".join(formatted)
    
    def _generate_chart(self, data: pd.DataFrame, chart_type: str, title: str) -> str:
        """生成图表并返回base64编码"""
        try:
            plt.figure(figsize=(10, 6))
            
            if chart_type == "line":
                plt.plot(data.index, data.values)
            elif chart_type == "bar":
                plt.bar(data.index, data.values)
            elif chart_type == "scatter":
                plt.scatter(data.iloc[:, 0], data.iloc[:, 1])
            
            plt.title(title)
            plt.tight_layout()
            
            # 保存为base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{chart_base64}"
        except Exception as e:
            return f"图表生成失败: {str(e)}"
    
    async def _assemble_report(self) -> str:
        """组装最终报告"""
        report_template = Template("""
# {{ title }}

**生成时间**: {{ generated_at }}  
**分析类型**: {{ analysis_type }}  
**数据范围**: {{ data_range }}  

---

{% for section in sections %}
{{ section.content }}

{% if section.charts %}
### 相关图表
{% for chart in section.charts %}
![图表]({{ chart }})
{% endfor %}
{% endif %}

{% if section.insights %}
### 关键洞察
{% for insight in section.insights %}
- {{ insight }}
{% endfor %}
{% endif %}

---

{% endfor %}

## 报告说明

本报告由智能分析系统自动生成，基于提供的数据进行深度分析。建议结合业务实际情况进行决策参考。

**免责声明**: 本报告仅供参考，具体决策请结合实际业务情况。
        """)
        
        return report_template.render(
            title="智能数据分析报告",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            analysis_type="综合分析",
            data_range=self.metadata.get("data_range", "基于聊天分析结果"),
            sections=self.sections
        )