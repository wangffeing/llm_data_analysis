# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import json
from typing import Any, Dict, Optional, Tuple, List, Union
from taskweaver.plugin import Plugin, register_plugin
from decimal import Decimal

MAX_DATA_POINTS = 100
SUPPORTED_CHART_TYPES = ['line', 'column', 'bar', 'area', 'pie']

def json_converter(o: Any) -> Any:
    if isinstance(o, Decimal): return float(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): 
        if np.isnan(o) or np.isinf(o):
            return None
        return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    if pd.isna(o) or o is pd.NaT: return None
    if o is None: return None
    if isinstance(o, str) and o.lower() in ['nan', 'null', 'none', '']:
        return None
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

@register_plugin
class gpt_vis_chart(Plugin):
    def __call__(
            self,
            df: pd.DataFrame,
            chart_type: str,
            x_field: Optional[str] = None,
            y_field: Optional[str] = None,
            title: Optional[str] = None,
            series_field: Optional[str] = None,
            stack: Optional[bool] = None,
            group: Optional[bool] = None,
    ) -> Tuple[str, str]:
        
        if chart_type not in SUPPORTED_CHART_TYPES:
            raise ValueError(f"Unsupported chart_type '{chart_type}'. Supported types: {SUPPORTED_CHART_TYPES}")
        
        if df.empty:
            raise ValueError("Input DataFrame (df) cannot be empty.")
        
        if chart_type == 'pie':
            if x_field is None or y_field is None:
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
                if not x_field and categorical_cols:
                    x_field = categorical_cols[0]
                if not y_field and numeric_cols:
                    y_field = numeric_cols[0]
        
        if not x_field or not y_field:
            raise ValueError(f"For chart type '{chart_type}', both x_field and y_field must be specified or inferable.")
        
        original_count = len(df)
        if original_count > MAX_DATA_POINTS:
            df = df.head(MAX_DATA_POINTS)

        df = self._preprocess_data(df.copy())
        
        chart_config = {"type": chart_type}
        
        if isinstance(y_field, list):
            raise ValueError(f"For '{chart_type}', `y_field` must be a single column name. Use `series_field` for grouping.")
        self._validate_fields(df, [x_field, y_field] + ([series_field] if series_field else []))
        
        if chart_type not in ['pie']:
            df = df.sort_values(by=x_field, ascending=True).reset_index(drop=True)

        df_renamed = self._rename_cols_for_gptvis(df, chart_type, x_field, y_field, series_field)
        
        chart_config["data"] = df_renamed.to_dict("records")
        chart_config["axisXTitle"] = x_field
        chart_config["axisYTitle"] = y_field

        if title: chart_config["title"] = title
        if group: chart_config["group"] = group
        if stack: chart_config["stack"] = stack

        filename = f'''vis-chart_{chart_config["type"]}_{chart_config.get("title", "untitled")}.vis'''
        markdown_content = self._generate_markdown(chart_config, filename)
        summary = self._generate_summary(chart_config, original_count, filename)
        
        return markdown_content, summary

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.replace({np.nan: None, pd.NaT: None, np.inf: None, -np.inf: None})
        
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].replace(['nan', 'NaN', 'null', 'NULL', ''], None)
        
        for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d')
        
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        df = df.dropna(how='all')
        
        return df

    def _validate_fields(self, df: pd.DataFrame, fields: List[str]):
        missing = [f for f in fields if f and f not in df.columns]
        if missing:
            raise ValueError(f"Fields not found in DataFrame: {missing}. Available columns are: {df.columns.tolist()}")
        
        for field in fields[1:]:
            if field and field in df.columns:
                if not pd.api.types.is_numeric_dtype(df[field]):
                    try:
                        df[field] = pd.to_numeric(df[field], errors='coerce')
                    except:
                        raise ValueError(f"Field '{field}' must contain numeric values for visualization.")
                
                valid_values = df[field].dropna()
                if len(valid_values) == 0:
                    raise ValueError(f"Field '{field}' contains no valid numeric values.")
                
                if np.isinf(valid_values).any():
                    raise ValueError(f"Field '{field}' contains infinite values which cannot be visualized.")

    def _rename_cols_for_gptvis(self, df: pd.DataFrame, chart_type: str, x_field: str, y_field: str, series_field: Optional[str]) -> pd.DataFrame:
        cols_to_keep = [x_field, y_field]
        rename_map = {}

        if chart_type in ['line', 'area']:
            rename_map = {x_field: 'time', y_field: 'value'}
        elif chart_type in ['column', 'bar', 'pie']:
            rename_map = {x_field: 'category', y_field: 'value'}
        else: # Default for other chart types
             rename_map = {x_field: 'x', y_field: 'y'}

        if series_field:
            rename_map[series_field] = 'group'
            cols_to_keep.append(series_field)
        
        return df[cols_to_keep].rename(columns=rename_map)

    def _generate_markdown(self, chart_config: Dict[str, Any], filename: str) -> str:
        chart_json = json.dumps(chart_config, ensure_ascii=False, default=json_converter)
        json_content = f"```vis-chart\n{chart_json}\n```"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_content)
        except Exception as e:
            print(f"Warning: Could not write to file {filename}: {e}")
        
        return json_content

    def _generate_summary(self, chart_config: Dict[str, Any], record_count: int, filename: str) -> str:
        chart_type = chart_config.get('type', 'unknown')
        title = chart_config.get('title', 'Untitled')
        
        if record_count > MAX_DATA_POINTS:
            data_points_val = f"Data size ({record_count}) exceeds limit ({MAX_DATA_POINTS}). Truncating data."
            summary_lines = [
                f"### Chart Summary: {title}",
                f"**Filename**: {filename}",
                f"- **Chart Type**: {chart_type.title()}",
                f"- **Data Points**: {data_points_val}"
            ]
        else:
            summary_lines = [
                f"### Chart Summary: {title}",
                f"**Filename**: {filename}",
                f"- **Chart Type**: {chart_type.title()}",
                f"- **Data Points**: {record_count:,}"
            ]

        if 'axisXTitle' in chart_config:
            summary_lines.append(f"- **X-Axis**: `{chart_config['axisXTitle']}`")
        if 'axisYTitle' in chart_config:
            summary_lines.append(f"- **Y-Axis**: `{chart_config['axisYTitle']}`")

        return "\n".join(summary_lines)