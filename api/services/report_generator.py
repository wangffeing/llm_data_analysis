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
            # 1. 生成执行摘要
            if self.config.include_executive_summary:
                executive_summary = await self._generate_executive_summary(analysis_results)
                self.sections.append(executive_summary)
            
            # 2. 生成详细分析
            if self.config.include_detailed_analysis:
                detailed_analysis = await self._generate_detailed_analysis(analysis_results)
                self.sections.extend(detailed_analysis)
            
            # 3. 生成改进建议
            if self.config.include_recommendations:
                recommendations = await self._generate_recommendations(analysis_results)
                self.sections.append(recommendations)
            
            # 4. 生成附录
            if self.config.include_appendix:
                appendix = await self._generate_appendix(analysis_results)
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
        
        # 按优先级排序
        prioritized_recommendations = self._prioritize_recommendations(recommendations)
        
        content = f"""
## 改进建议

### 高优先级建议
{self._format_recommendations(prioritized_recommendations['high'])}

### 中优先级建议
{self._format_recommendations(prioritized_recommendations['medium'])}

### 长期建议
{self._format_recommendations(prioritized_recommendations['low'])}

### 实施路线图
{self._generate_implementation_roadmap(prioritized_recommendations)}
        """
        
        return ReportSection(
            title="改进建议",
            content=content,
            recommendations=recommendations
        )
    
    def _extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键指标"""
        key_metrics = {}
        
        if "statistics" in results:
            stats = results["statistics"]
            key_metrics.update({
                "total_records": stats.get("count", 0),
                "data_completeness": stats.get("completeness_rate", 0),
                "quality_score": stats.get("quality_score", 0)
            })
        
        if "performance_metrics" in results:
            perf = results["performance_metrics"]
            key_metrics.update({
                "avg_response_time": perf.get("avg_response_time", 0),
                "satisfaction_score": perf.get("satisfaction_score", 0),
                "resolution_rate": perf.get("resolution_rate", 0)
            })
        
        return key_metrics
    
    def _identify_trends(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别趋势"""
        trends = []
        
        if "time_series" in results:
            ts_data = results["time_series"]
            
            # 分析各指标趋势
            for metric, values in ts_data.items():
                if len(values) > 1:
                    trend_direction = "上升" if values[-1] > values[0] else "下降"
                    trend_strength = abs(values[-1] - values[0]) / values[0] * 100
                    
                    trends.append({
                        "metric": metric,
                        "direction": trend_direction,
                        "strength": trend_strength,
                        "significance": "高" if trend_strength > 20 else "中" if trend_strength > 10 else "低"
                    })
        
        return trends
    
    def _identify_critical_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别关键问题"""
        issues = []
        
        # 检查性能问题
        if "performance_metrics" in results:
            perf = results["performance_metrics"]
            
            if perf.get("avg_response_time", 0) > 300:  # 响应时间超过5分钟
                issues.append({
                    "type": "performance",
                    "severity": "high",
                    "description": "平均响应时间过长",
                    "impact": "客户满意度下降",
                    "metric_value": perf.get("avg_response_time")
                })
            
            if perf.get("satisfaction_score", 100) < 70:
                issues.append({
                    "type": "quality",
                    "severity": "high",
                    "description": "客户满意度偏低",
                    "impact": "客户流失风险",
                    "metric_value": perf.get("satisfaction_score")
                })
        
        return issues
    
    def _format_key_metrics(self, metrics: Dict[str, Any]) -> str:
        """格式化关键指标"""
        formatted = []
        for key, value in metrics.items():
            if isinstance(value, float):
                formatted.append(f"- **{key}**: {value:.2f}")
            else:
                formatted.append(f"- **{key}**: {value}")
        return "\n".join(formatted)
    
    def _generate_chart(self, data: pd.DataFrame, chart_type: str, title: str) -> str:
        """生成图表并返回base64编码"""
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
            title="电信客服数据分析报告",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            analysis_type="综合分析",
            data_range=self.metadata.get("data_range", "未指定"),
            sections=self.sections
        )