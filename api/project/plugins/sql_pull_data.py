import pandas as pd
import py_opengauss
from taskweaver.plugin import Plugin, register_plugin
import re
from typing import List
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML

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


def validate_sql_query(sql: str) -> bool:
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False
        
        statement = parsed[0]
        
        if len(parsed) > 1:
            return False
        
        if not statement.get_type() == 'SELECT':
            return False
        
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION', 'GRANT', 'REVOKE'
        ]
        
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        return True
    except Exception:
        return False


def sanitize_sql_input(sql: str) -> str:
    sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    sql = sql.strip().rstrip(';')
    
    return sql


@register_plugin
class SqlPullData(Plugin):
    def __call__(self, sql: str):
        if not sql or not sql.strip():
            raise ValueError("SQL query cannot be empty")
        
        sql = sanitize_sql_input(sql)
        
        if not validate_sql_query(sql):
            raise ValueError(
                "Invalid or potentially dangerous SQL query. "
                "Only SELECT statements are allowed, and certain keywords are prohibited."
            )
        
        try:
            pattern = r"SELECT\s+(.*?)\s+FROM"
            match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
        
            if not match:
                raise ValueError("Could not find SELECT and FROM clauses in the SQL query.")

            db_path = self.get_env('DB_PATH')
            db = py_opengauss.open(db_path)
            get_table = db.prepare(sql)
            result = get_table()
            
        
            column_defs_string = match.group(1)
            column_definitions = parse_sql_columns(column_defs_string)
            columns = [extract_alias(defn) for defn in column_definitions]
            if result and len(columns) != len(result[0]):
                raise ValueError(
                    f"Column name parsing failed. Parsed {len(columns)} columns ({columns}), "
                    f"but data has {len(result[0])} columns. Please check the SQL syntax."
                )
        
            df = pd.DataFrame(result, columns=columns)
        
            if len(df) == 0:
                return df, (
                    f"The SQL query was executed successfully.\n"
                    f"SQL: {sql}\n"
                    f"Result: The result is empty."
                )
            else:
                return df, (
                    f"The SQL query was executed successfully.\n"
                    f"SQL: {sql}\n"
                    f"There are {len(df)} rows in the result.\n"
                    f"The first {min(5, len(df))} rows are:\n{df.head(min(5, len(df))).to_markdown()}"
                )
        except Exception as e:
            raise ValueError(f"Database query failed: {str(e)}")