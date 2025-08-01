import pandas as pd
import sqlite3
import os
from taskweaver.plugin import Plugin, register_plugin
import re
from typing import List
from dotenv import load_dotenv

def parse_sql_columns(column_string: str) -> List[str]:
    """
    Parses a SQL SELECT clause string into a list of individual column definitions.
    This function correctly handles commas within parentheses (e.g., function calls)
    and inside quoted strings.
    """
    columns = []
    current_column = ""
    paren_depth = 0
    in_single_quote = False
    in_double_quote = False

    for char in column_string + ",":
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == '(' and not in_single_quote and not in_double_quote:
            paren_depth += 1
        elif char == ')' and not in_single_quote and not in_double_quote:
            paren_depth = max(0, paren_depth - 1)

        if char == ',' and paren_depth == 0 and not in_single_quote and not in_double_quote:
            if current_column.strip():
                columns.append(current_column.strip())
            current_column = ""
        else:
            current_column += char

    return columns


def extract_alias(column_definition: str) -> str:
    """
    Extracts the alias from a single SQL column definition, handling "AS" keyword.
    """
    # Use regex to find 'AS alias', ignoring case. This is reliable.
    match = re.search(r'\s+AS\s+("?[\w_]+"?)', column_definition, re.IGNORECASE)
    if match:
        return match.group(1).strip('"')

    # If no 'AS', handle simple cases like "table.column" or just "column".
    # This takes the part after the last dot (if any) and then the last word.
    return column_definition.split('.')[-1].split()[-1].strip('"')


def convert_mysql_to_sqlite(sql: str) -> str:
    """
    Convert MySQL-specific SQL syntax to SQLite-compatible syntax
    """
    # Convert DATE_FORMAT to strftime
    # DATE_FORMAT(date_column, '%Y-%m') -> strftime('%Y-%m', date_column)
    date_format_pattern = r"DATE_FORMAT\s*\(\s*([^,]+)\s*,\s*'([^']+)'\s*\)"
    
    def replace_date_format(match):
        column = match.group(1).strip()
        format_str = match.group(2)
        return f"strftime('{format_str}', {column})"
    
    sql = re.sub(date_format_pattern, replace_date_format, sql, flags=re.IGNORECASE)
    
    # Convert other MySQL functions if needed
    # Add more conversions here as needed
    
    return sql


def dataframe_to_string(df, max_rows=5):
    """
    Convert DataFrame to string representation without using tabulate
    """
    if len(df) == 0:
        return "Empty DataFrame"
    
    # Get column names
    columns = df.columns.tolist()
    
    # Get data for first few rows
    data_rows = df.head(max_rows).values.tolist()
    
    # Calculate column widths
    col_widths = []
    for i, col in enumerate(columns):
        max_width = len(str(col))
        for row in data_rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width)
    
    # Create header
    header = " | ".join(str(col).ljust(width) for col, width in zip(columns, col_widths))
    separator = "-|-".join("-" * width for width in col_widths)
    
    # Create data rows
    data_lines = []
    for row in data_rows:
        line = " | ".join(str(row[i] if i < len(row) else "").ljust(col_widths[i]) for i in range(len(columns)))
        data_lines.append(line)
    
    return "\n".join([header, separator] + data_lines)


def load_env_config():
    """
    Load environment configuration from .env file
    """
    # Try to find .env file in multiple locations
    possible_env_paths = [
        # Current directory
        ".env",
        # Parent directory (api folder)
        "../.env",
        # Two levels up
        "../../.env",
        # Absolute path to api folder
        "d:/myproject/2025/llm_data_analysis/api/.env"
    ]
    
    for env_path in possible_env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break
    else:
        # If no .env file found, try to load from current directory anyway
        load_dotenv()


@register_plugin
class SqlPullData(Plugin):
    def __call__(self, sql: str):
        # Load environment variables
        load_env_config()
        
        # Get database path from environment variable
        db_path = os.getenv('SQLITE_DB_PATH', 'd:/myproject/2025/llm_data_analysis/api/test_database.db')
        
        # Ensure absolute path
        if not os.path.isabs(db_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            db_path = os.path.join(project_root, db_path)
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite database file not found: {db_path}")
        
        # Convert MySQL syntax to SQLite syntax
        original_sql = sql
        sql = convert_mysql_to_sqlite(sql)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            
            if sql.strip().upper().startswith('SELECT'):
                pattern = r"SELECT\s+(.*?)\s+FROM"
                match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
                
                if match:
                    column_defs_string = match.group(1)
                    column_definitions = parse_sql_columns(column_defs_string)
                    columns = [extract_alias(defn) for defn in column_definitions]
                    
                    if result and len(columns) != len(result[0]):
                        columns = [description[0] for description in cursor.description]
                else:
                    columns = [description[0] for description in cursor.description]
            else:
                columns = [description[0] for description in cursor.description] if cursor.description else []
            
            df = pd.DataFrame(result, columns=columns)
            
            if len(df) == 0:
                description = (
                    f"The SQL query was executed successfully.\n"
                    f"Original SQL: {original_sql}\n"
                    f"Converted SQL (SQLite): {sql}\n"
                    f"Result: The result is empty."
                )
            else:
                df_string = dataframe_to_string(df, max_rows=5)
                description = (
                    f"The SQL query was executed successfully.\n"
                    f"Original SQL: {original_sql}\n"
                    f"Converted SQL (SQLite): {sql}\n"
                    f"There are {len(df)} rows in the result.\n"
                    f"The first {min(5, len(df))} rows are:\n{df_string}"
                )
            
            return df, description
            
        except Exception as e:
            # If conversion failed, provide helpful error message
            error_msg = f"SQL execution failed: {str(e)}\n"
            error_msg += f"Original SQL: {original_sql}\n"
            error_msg += f"Converted SQL: {sql}\n"
            error_msg += "\nNote: This plugin automatically converts MySQL syntax to SQLite. "
            error_msg += "If you're still getting errors, please check your SQL syntax."
            raise Exception(error_msg)
            
        finally:
            conn.close()