from taskweaver.module.event_emitter import SessionEventHandlerBase, RoundEventType, PostEventType
from services.sse_service import SSEService, SSEMessageType
from typing import Any, Dict, List, Tuple
import logging
import time

logger = logging.getLogger(__name__)

class SSEEventHandler(SessionEventHandlerBase):
    
    def __init__(self, session_id: str, sse_service: SSEService):
        super().__init__()
        self.session_id = session_id
        self.sse_service = sse_service
        self.reset_current_step()
        self.intermediate_messages = []

    def reset_current_step(self):
        self.current_step = None
        self.current_attachment_list: List[Tuple[str, str, str, bool]] = []  # (id, type, content, is_end)
        self.current_post_status: str = "更新中"
        self.current_send_to: str = "未知"
        self.current_message: str = ""
        self.current_message_is_end: bool = False
        self.current_message_sent: bool = False

    def _send_message_immediate(self, message_type: SSEMessageType, data: dict):
        try:
            enhanced_data = {
                **data,
                "session_id": self.session_id,
                "timestamp": time.time()
            }
            
            self.sse_service.send_message_from_sync(self.session_id, message_type, enhanced_data)
            logger.debug(f"[{self.session_id}] 实时发送SSE消息: {message_type.value}")
        except Exception as e:
            logger.error(f"[{self.session_id}] 发送SSE消息失败: {message_type.value}, {e}")
    
    def handle_round(self, type: RoundEventType, msg: str, extra: Any, round_id: str, **kwargs):
        try:
            if type == RoundEventType.round_start:
                self.reset_current_step()  # 新轮次开始时重置状态
                self._send_message_immediate(SSEMessageType.ROUND_START, {
                    "round_id": round_id,
                    "message": "开始处理请求",
                    "extra": extra
                })
                
            elif type == RoundEventType.round_end:
                data = {
                    "round_id": round_id,
                    "message": "请求处理完成"
                }
                if extra:
                    data["result"] = extra
                    
                self._send_message_immediate(SSEMessageType.ROUND_END, data)
                self.reset_current_step()  # 轮次结束时重置状态
                
            elif type == RoundEventType.round_error:
                self._send_message_immediate(SSEMessageType.ERROR, {
                    "round_id": round_id,
                    "error": msg,
                    "message": f"轮次处理错误: {msg}"
                })
                self.intermediate_messages.append({
                    "type": "error",
                    "content": f"错误: {msg}",
                    "timestamp": time.time()
                })
                
        except Exception as e:
            logger.error(f"[{self.session_id}] 处理轮次事件失败: {e}")
    
    def handle_post(self, type: PostEventType, msg: str, extra: Any, post_id: str, round_id: str, **kwargs):
        try:
            base_data = {
                "post_id": post_id,
                "round_id": round_id
            }
            
            if type == PostEventType.post_start:
                self.reset_current_step()
                role = extra.get('role', '未知') if extra else '未知'
                self.current_step = f"步骤由 {role} 开始"
                
                self._send_message_immediate(SSEMessageType.POST_START, {
                    **base_data,
                    "message": self.current_step,
                    "role": role
                })
                
                self.intermediate_messages.append({
                    "type": "post_start",
                    "content": self.current_step,
                    "timestamp": time.time()
                })
                
            elif type == PostEventType.post_end:
                final_content = self._format_post_content(is_end=True)
                
                self._send_message_immediate(SSEMessageType.POST_END, {
                    **base_data,
                    "message": "处理完成",
                    "content": final_content,
                    "final_message": self.current_message
                })
                
                if final_content.strip():
                    self.intermediate_messages.append({
                        "type": "post_end",
                        "content": final_content,
                        "timestamp": time.time()
                    })
                
                self.reset_current_step()
                
            elif type == PostEventType.post_error:
                error_msg = msg or "未知错误"
                self._send_message_immediate(SSEMessageType.POST_ERROR, {
                    **base_data,
                    "error": error_msg,
                    "message": f"帖子处理错误: {error_msg}"
                })
                
                self.intermediate_messages.append({
                    "type": "error",
                    "content": f"错误: {error_msg}",
                    "timestamp": time.time()
                })
                
            elif type == PostEventType.post_message_update:
                content = msg or (extra.get("content", "") if extra else "")
                is_end = extra.get('is_end', False) if extra else False
                
                if content:
                    self.current_message += content
                    
                if is_end:
                    self.current_message_is_end = True
                    self._send_message_immediate(SSEMessageType.POST_MESSAGE_UPDATE, {
                        **base_data,
                        "content": self.current_message,
                        "type": "message_update",
                        "is_complete": True
                    })
                else:
                    pass
                    # 启用增量更新 - 取消注释这部分
                    # if content:  # 只有当有新内容时才发送
                    #     self._send_message_immediate(SSEMessageType.POST_MESSAGE_UPDATE, {
                    #         **base_data,
                    #         "content": content,
                    #         "type": "message_increment",
                    #         "is_complete": False,
                    #         "total_content": self.current_message
                    #     })
                
            elif type == PostEventType.post_status_update:
                status = msg or (extra.get("status", "") if extra else "")
                self.current_post_status = status
                
                self._send_message_immediate(SSEMessageType.POST_STATUS_UPDATE, {
                    **base_data,
                    "status": status,
                    "type": "status_update"
                })
                
                if status.strip():
                    self.intermediate_messages.append({
                        "type": "status_update",
                        "content": f"**状态**: {status}",
                        "timestamp": time.time()
                    })
                
            elif type == PostEventType.post_send_to_update:
                send_to = msg or (extra.get("send_to", "") if extra else "")
                self.current_send_to = send_to
                
                self._send_message_immediate(SSEMessageType.POST_SEND_TO_UPDATE, {
                    **base_data,
                    "send_to": send_to,
                    "type": "status_update"
                })
                
            elif type == PostEventType.post_attachment_update:
                attachment_info = extra if extra else {}
                attachment_type = attachment_info.get("type", "unknown")
                attachment_id = attachment_info.get("id", "unknown")
                is_end = attachment_info.get('is_end', False)
                
                if isinstance(msg, list):
                    msg = ''.join(str(item) for item in msg)
                elif msg is None:
                    msg = ""
                else:
                    msg = str(msg)
                
                existing_attachment_index = None
                for i, (aid, atype, content, _) in enumerate(self.current_attachment_list):
                    if aid == attachment_id:
                        existing_attachment_index = i
                        break
                
                if existing_attachment_index is not None:
                    aid, atype, content, _ = self.current_attachment_list[existing_attachment_index]
                    if isinstance(content, list):
                        content = ''.join(str(item) for item in content)
                    elif content is None:
                        content = ""
                    else:
                        content = str(content)
                    
                    self.current_attachment_list[existing_attachment_index] = (aid, atype, content + msg, is_end)
                else:
                    self.current_attachment_list.append((attachment_id, attachment_type, msg, is_end))
                
                if is_end:
                    full_content = ""
                    for aid, atype, content, _ in self.current_attachment_list:
                        if aid == attachment_id:
                            if isinstance(content, list):
                                full_content = ''.join(str(item) for item in content)
                            elif content is None:
                                full_content = ""
                            else:
                                full_content = str(content)
                            break
                    
                    if full_content.strip():
                        self._send_message_immediate(SSEMessageType.POST_ATTACHMENT_UPDATE, {
                            **base_data,
                            "attachment": {
                                "id": attachment_id,
                                "type": attachment_type,
                                "content": full_content,
                                "is_complete": True
                            },
                            "type": "attachment_update"
                        })
                    
                    display_types = ["plan", "execution_result", "text", "plan_reasoning", "current_plan_step"]
                    if attachment_type.name in display_types:
                        content_formatted = self._format_attachment_content(attachment_type, full_content)
                        if content_formatted and content_formatted.strip():
                            self.intermediate_messages.append({
                                "type": "attachment",
                                "content": content_formatted,
                                "attachment_type": attachment_type,
                                "timestamp": time.time()
                            })
                else:
                    pass
                    # 启用增量附件更新 - 取消注释这部分
                    # if msg and msg.strip():  # 只有当有新内容时才发送
                    #     self._send_message_immediate(SSEMessageType.POST_ATTACHMENT_UPDATE, {
                    #         **base_data,
                    #         "attachment": {
                    #             "id": attachment_id,
                    #             "type": attachment_type,
                    #             "content": msg,
                    #             "is_complete": False
                    #         },
                    #         "type": "attachment_increment"
                    #     })

        except Exception as e:
            logger.error(f"[{self.session_id}] 处理帖子事件失败: {type.value}, {e}")
    
    def _format_post_content(self, is_end: bool = False) -> str:
        """格式化帖子内容 - 参考Streamlit处理器"""
        content = ""
        
        if self.current_post_status and self.current_post_status != "更新中":
            content += f"**状态**: {self.current_post_status}\n\n"
        
        if self.current_message:
            content += f"{self.current_message}\n\n"
        
        # 处理附件
        for _, atype, amsg, _ in self.current_attachment_list:
            formatted_attachment = self._format_attachment_content(atype, amsg)
            if formatted_attachment:
                content += formatted_attachment + "\n\n"
        
        return content.strip()
    
    def _format_attachment_content(self, attachment_type: str, content) -> str:
        """格式化附件内容"""
        display_types = ["plan", "execution_result", "text", "plan_reasoning", "current_plan_step"]
        
        if attachment_type.name not in display_types:
            return ""
        
        # 确保 content 是字符串
        if isinstance(content, list):
            content = ''.join(str(item) for item in content)
        elif content is None:
            content = ""
        else:
            content = str(content)
        
        if attachment_type == "plan_reasoning":
            return f"**思考过程**:\n```\n{content}\n```"
        elif attachment_type == "plan":
            return f"**计划**:\n```\n{content}\n```"
        elif attachment_type == "current_plan_step":
            return f"**当前计划**:\n```\n{content}\n```"
        elif attachment_type == "execution_result":
            return f"**执行结果**:\n```\n{content}\n```"
        elif attachment_type == "text":
            return content
        
        return ""
    
    def send_file_generated(self, file_path: str, file_type: str):
        """发送文件生成消息 - 立即发送"""
        self._send_message_immediate(SSEMessageType.FILE_GENERATED, {
            "file_path": file_path,
            "file_type": file_type
        })
    
    def send_error(self, error_message: str):
        """发送错误消息"""
        self._send_message_immediate(SSEMessageType.ERROR, {
            "error": error_message
        })
        
        # 保存到中间消息
        self.intermediate_messages.append({
            "type": "error",
            "content": f"错误: {error_message}",
            "timestamp": time.time()
        })
    
    def send_chat_completed(self, result: dict = None):
        """发送聊天完成消息"""
        data = {
            "message": "聊天处理完成",
            "intermediate_messages": self.intermediate_messages
        }
        if result:
            data["result"] = result
            
        self._send_message_immediate(SSEMessageType.CHAT_COMPLETED, data)
    
    def get_intermediate_messages(self) -> List[Dict]:
        """获取中间消息列表"""
        return self.intermediate_messages.copy()
    
    def clear_intermediate_messages(self):
        """清空中间消息"""
        self.intermediate_messages.clear()
    
    def cleanup(self):
        """清理资源"""
        self.reset_current_step()
        self.clear_intermediate_messages()
        logger.info(f"[{self.session_id}] SSE事件处理器已清理（优化模式）")
    
    def get_stats(self):
        """获取统计信息"""
        return {
            "session_id": self.session_id,
            "mode": "optimized_immediate",
            "running": True,
            "current_step": self.current_step,
            "message_length": len(self.current_message),
            "attachments_count": len(self.current_attachment_list),
            "intermediate_messages_count": len(self.intermediate_messages)
        }
