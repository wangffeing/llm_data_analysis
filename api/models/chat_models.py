from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ChatMessage(BaseModel):
    content: str = Field(..., description="用户消息内容")
    selected_table: Optional[str] = Field(default=None, description="选择的数据源表名")
    uploaded_files: Optional[List[Dict[str, Any]]] = Field(default=None, description="上传的文件信息")
    template_id: Optional[str] = None  # 新增：模板ID
    template_context: Optional[Dict[str, Any]] = None  # 新增：模板上下文
    message_type: str = Field(default="user_message", description="消息类型")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="附加元数据")
    files: Optional[List[str]] = Field(default=None, description="附件文件列表")

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    conversation_id: str

class DataSource(BaseModel):
    name: str
    table_name: str
    description: str
    table_columns: List[str]
    table_columns_names: List[str]
    table_order: Optional[str] = None

class DataSourcesResponse(BaseModel):
    data_sources: List[DataSource]