# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import json
import os
import re
from typing import Any, Dict, Optional, Tuple, List, Union
from taskweaver.plugin import Plugin, register_plugin
from decimal import Decimal

MAX_DATA_POINTS = 100
SUPPORTED_CHART_TYPES = ['line', 'column', 'bar', 'area', 'pie']

# G2 format standard field mapping
G2_FIELD_MAPPING = {
    'line': {'x': 'time', 'y': 'value', 'series': 'group'},
    'area': {'x': 'time', 'y': 'value', 'series': 'group'},
    'column': {'x': 'category', 'y': 'value', 'series': 'group'},
    'bar': {'x': 'category', 'y': 'value', 'series': 'group'},
    'pie': {'x': 'category', 'y': 'value', 'series': 'group'}
}

def json_converter(o: Any) -> Any:
    """Enhanced JSON converter to ensure all data types are properly serializable"""
    if isinstance(o, Decimal): 
        return float(o)
    if isinstance(o, np.integer): 
        return int(o)
    if isinstance(o, np.floating): 
        if np.isnan(o) or np.isinf(o):
            return None
        return float(o)
    if isinstance(o, np.ndarray): 
        return o.tolist()
    if pd.isna(o) or o is pd.NaT: 
        return None
    if o is None: 
        return None
    if isinstance(o, str) and o.lower() in ['nan', 'null', 'none', '']:
        return None
    if hasattr(o, 'isoformat'):  # datetime objects
        return o.isoformat()
    if isinstance(o, (set, tuple)):
        return list(o)
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
        
        try:
            # Strict input validation
            self._validate_inputs(df, chart_type, x_field, y_field, series_field, stack, group)
            
            # Auto-infer fields if not provided
            x_field, y_field = self._auto_infer_fields(df, chart_type, x_field, y_field)
            
            # Data preprocessing
            original_count = len(df)
            if original_count > MAX_DATA_POINTS:
                df = df.head(MAX_DATA_POINTS)
            
            df_processed = self._preprocess_data(df.copy())
            
            # Validate processed data
            self._validate_processed_data(df_processed, x_field, y_field, series_field)
            
            # Generate G2-compliant configuration
            chart_config = self._build_g2_config(
                df_processed, chart_type, x_field, y_field, 
                title, series_field, stack, group
            )
            
            # Validate generated configuration
            self._validate_chart_config(chart_config)
            
            # Generate output
            filename = self._generate_safe_filename(chart_config)
            markdown_content = self._generate_markdown(chart_config, filename)
            summary = self._generate_summary(chart_config, original_count, filename)
            
            return markdown_content, summary
            
        except Exception as e:
            error_msg = f"GPT-Vis Chart Generation Error: {str(e)}"
            print(error_msg)
            # Return error info instead of raising exception
            return f"```\n{error_msg}\n```", f"**Error**: {error_msg}"

    def _validate_inputs(self, df: pd.DataFrame, chart_type: str, x_field: Optional[str], 
                        y_field: Optional[str], series_field: Optional[str], 
                        stack: Optional[bool], group: Optional[bool]):
        """Strict input validation"""
        if chart_type not in SUPPORTED_CHART_TYPES:
            raise ValueError(f"Unsupported chart type '{chart_type}'. Supported types: {SUPPORTED_CHART_TYPES}")
        
        if df.empty:
            raise ValueError("Input DataFrame cannot be empty")
        
        if len(df.columns) < 2:
            raise ValueError("DataFrame must have at least 2 columns for visualization")
        
        # Validate field existence
        available_cols = df.columns.tolist()
        if x_field and x_field not in available_cols:
            raise ValueError(f"x_field '{x_field}' not found in DataFrame. Available columns: {available_cols}")
        if y_field and y_field not in available_cols:
            raise ValueError(f"y_field '{y_field}' not found in DataFrame. Available columns: {available_cols}")
        if series_field and series_field not in available_cols:
            raise ValueError(f"series_field '{series_field}' not found in DataFrame. Available columns: {available_cols}")
        
        # Validate parameter combinations
        if stack and group:
            raise ValueError("stack and group parameters cannot both be True")
        
        if (stack or group) and not series_field:
            raise ValueError("series_field must be specified when using stack or group")

    def _auto_infer_fields(self, df: pd.DataFrame, chart_type: str, 
                          x_field: Optional[str], y_field: Optional[str]) -> Tuple[str, str]:
        """Intelligent field inference"""
        categorical_cols = df.select_dtypes(include=['object', 'category', 'datetime']).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not x_field:
            if chart_type in ['line', 'area']:
                # Time series charts prefer datetime/time columns
                datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
                if datetime_cols:
                    x_field = datetime_cols[0]
                elif categorical_cols:
                    x_field = categorical_cols[0]
                elif numeric_cols:
                    x_field = numeric_cols[0]
            else:
                # Categorical charts prefer categorical columns
                if categorical_cols:
                    x_field = categorical_cols[0]
                elif numeric_cols:
                    x_field = numeric_cols[0]
        
        if not y_field:
            # Y-axis prefers numeric columns
            remaining_numeric = [col for col in numeric_cols if col != x_field]
            if remaining_numeric:
                y_field = remaining_numeric[0]
            elif numeric_cols:
                y_field = numeric_cols[0]
        
        if not x_field or not y_field:
            raise ValueError(f"Cannot auto-infer suitable x_field and y_field for chart type '{chart_type}'. "
                           f"Available columns: {df.columns.tolist()}")
        
        return x_field, y_field

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced data preprocessing"""
        # Handle missing and invalid values
        df = df.replace({np.nan: None, pd.NaT: None, np.inf: None, -np.inf: None})
        
        # Handle string representations of missing values
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].replace(['nan', 'NaN', 'null', 'NULL', '', 'None'], None)
        
        # Handle datetime columns
        for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d')
        
        # Try to convert numeric columns
        for col in df.select_dtypes(include=['object']).columns:
            try:
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                if not numeric_series.isna().all():  # If at least some values can be converted
                    df[col] = numeric_series
            except:
                pass
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        if df.empty:
            raise ValueError("DataFrame is empty after preprocessing, please check data quality")
        
        return df

    def _validate_processed_data(self, df: pd.DataFrame, x_field: str, 
                                y_field: str, series_field: Optional[str]):
        """Validate processed data quality"""
        # Y-axis field must be numeric
        if not pd.api.types.is_numeric_dtype(df[y_field]):
            try:
                df[y_field] = pd.to_numeric(df[y_field], errors='coerce')
            except:
                raise ValueError(f"Field '{y_field}' must contain numeric data for visualization")
        
        # Check for valid numeric values
        valid_y_values = df[y_field].dropna()
        if len(valid_y_values) == 0:
            raise ValueError(f"Field '{y_field}' contains no valid numeric data")
        
        # Check for infinite values
        if np.isinf(valid_y_values).any():
            raise ValueError(f"Field '{y_field}' contains infinite values that cannot be visualized")
        
        # Validate X-axis field validity
        valid_x_values = df[x_field].dropna()
        if len(valid_x_values) == 0:
            raise ValueError(f"Field '{x_field}' contains no valid data")
        
        # Validate data point count
        if len(df) < 1:
            raise ValueError("Insufficient data points after processing to generate chart")

    def _build_g2_config(self, df: pd.DataFrame, chart_type: str, x_field: str, 
                        y_field: str, title: Optional[str], series_field: Optional[str],
                        stack: Optional[bool], group: Optional[bool]) -> Dict[str, Any]:
        """Build G2-compliant configuration"""
        # Get field mapping
        field_mapping = G2_FIELD_MAPPING[chart_type]
        
        # Prepare data
        cols_to_keep = [x_field, y_field]
        rename_map = {
            x_field: field_mapping['x'],
            y_field: field_mapping['y']
        }
        
        if series_field:
            cols_to_keep.append(series_field)
            rename_map[series_field] = field_mapping['series']
        
        # Sort data (except for pie charts)
        if chart_type not in ['pie']:
            df = df.sort_values(by=x_field, ascending=True).reset_index(drop=True)
        
        # Rename columns and select data
        df_renamed = df[cols_to_keep].rename(columns=rename_map)
        
        # Final data cleaning
        df_renamed = df_renamed.dropna()
        
        # Build configuration object
        chart_config = {
            "type": chart_type,
            "data": df_renamed.to_dict("records")
        }
        
        # Add optional configurations
        if title:
            chart_config["title"] = str(title)
        
        if group is True:
            chart_config["group"] = True
        
        if stack is True:
            chart_config["stack"] = True
        
        # Add axis titles (for non-pie charts only)
        if chart_type != 'pie':
            chart_config["axisXTitle"] = str(x_field)
            chart_config["axisYTitle"] = str(y_field)
        
        return chart_config

    def _validate_chart_config(self, chart_config: Dict[str, Any]):
        """Validate generated chart configuration"""
        required_fields = ["type", "data"]
        for field in required_fields:
            if field not in chart_config:
                raise ValueError(f"Chart configuration missing required field: {field}")
        
        if not isinstance(chart_config["data"], list):
            raise ValueError("Chart data must be in list format")
        
        if len(chart_config["data"]) == 0:
            raise ValueError("Chart data cannot be empty")
        
        # Validate data record consistency
        if chart_config["data"]:
            first_record = chart_config["data"][0]
            required_keys = set(first_record.keys())
            
            for i, record in enumerate(chart_config["data"]):
                if set(record.keys()) != required_keys:
                    raise ValueError(f"Data record {i} has inconsistent fields with other records")

    def _generate_safe_filename(self, chart_config: Dict[str, Any]) -> str:
        """Generate safe filename"""
        chart_type = chart_config.get("type", "unknown")
        title = chart_config.get("title", "untitled")
        
        # Clean special characters from filename
        safe_title = re.sub(r'[^\w\-_\.]', '_', str(title))
        safe_title = re.sub(r'_+', '_', safe_title).strip('_')
        
        return f"vis-chart_{chart_type}_{safe_title}.vis"

    def _generate_markdown(self, chart_config: Dict[str, Any], filename: str) -> str:
        """Generate Markdown content"""
        try:
            chart_json = json.dumps(chart_config, ensure_ascii=False, indent=2, default=json_converter)
            json_content = f"```vis-chart\n{chart_json}\n```"
            
            # Try to write file (optional)
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(json_content)
            except Exception as e:
                print(f"Warning: Could not write to file {filename}: {e}")
            
            return json_content
            
        except Exception as e:
            raise ValueError(f"Failed to generate Markdown content: {e}")

    def _generate_summary(self, chart_config: Dict[str, Any], record_count: int, filename: str) -> str:
        """Generate chart summary"""
        chart_type = chart_config.get('type', 'unknown')
        title = chart_config.get('title', 'Untitled Chart')
        
        summary_lines = [
            f"### Chart Summary: {title}",
            f"**Filename**: {filename}",
            f"- **Chart Type**: {chart_type.title()}",
            f"- **Data Points**: {len(chart_config.get('data', []))} / {record_count}"
        ]
        
        if record_count > MAX_DATA_POINTS:
            summary_lines.append(f"- **Data Truncation**: Original {record_count} rows, truncated to {MAX_DATA_POINTS} rows")
        
        if 'axisXTitle' in chart_config:
            summary_lines.append(f"- **X-Axis**: `{chart_config['axisXTitle']}`")
        if 'axisYTitle' in chart_config:
            summary_lines.append(f"- **Y-Axis**: `{chart_config['axisYTitle']}`")
        
        if chart_config.get('stack'):
            summary_lines.append("- **Style**: Stacked display")
        elif chart_config.get('group'):
            summary_lines.append("- **Style**: Grouped display")
        
        return "\n".join(summary_lines)