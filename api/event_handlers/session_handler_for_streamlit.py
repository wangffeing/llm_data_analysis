import streamlit as st
import logging
from typing import Any, Dict, List, Tuple, Union
from taskweaver.module.event_emitter import PostEventType, RoundEventType, SessionEventHandlerBase
from taskweaver.memory.attachment import AttachmentType

logger = logging.getLogger(__name__)

class StreamlitMessageUpdater(SessionEventHandlerBase):
    def __init__(self):
        self.reset_cur_step()
        self.placeholders = {}
        # 添加一个变量来跟踪中间状态
        self.intermediate_messages = []

    def reset_cur_step(self):
        self.cur_step = None
        self.cur_attachment_list: List[Tuple[str, AttachmentType, str, bool]] = []
        self.cur_post_status: str = "更新中"
        self.cur_send_to: str = "未知"
        self.cur_message: str = ""
        self.cur_message_is_end: bool = False
        self.cur_message_sent: bool = False

    def handle_round(
            self,
            type: RoundEventType,
            msg: str,
            extra: Any,
            round_id: str,
            **kwargs: Any,
    ):
        if type == RoundEventType.round_error:
            st.error(f"错误: {msg}")
            # 保存错误信息到历史记录
            if "messages" in st.session_state:
                st.session_state.messages.append(
                    {"role": "system", "content": f"错误: {msg}", "is_intermediate": True}
                )

    def handle_post(
            self,
            type: PostEventType,
            msg: str,
            extra: Any,
            post_id: str,
            round_id: str,
            **kwargs: Any,
    ):
        if type == PostEventType.post_start:
            self.reset_cur_step()
            self.cur_step = f"步骤由 {extra['role']} 开始"
            self.placeholders[round_id] = st.empty()
            # 保存开始状态到中间消息
            self.intermediate_messages.append(
                {"role": "assistant", "content": f"步骤由 {extra['role']} 开始", "is_intermediate": True}
            )
            # 更新会话状态
            if "messages" in st.session_state:
                st.session_state.messages.append(self.intermediate_messages[-1])
        elif type == PostEventType.post_end:
            content, _ = self.format_post_body(is_end=True)
            self.placeholders[round_id].markdown(content, unsafe_allow_html=True)
            st.divider()
            # 保存结束状态到中间消息
            if content.strip():
                self.intermediate_messages.append(
                    {"role": "assistant", "content": content, "is_intermediate": True}
                )
                # 更新会话状态
                if "messages" in st.session_state:
                    st.session_state.messages.append(self.intermediate_messages[-1])
            self.reset_cur_step()
        elif type == PostEventType.post_error:
            # 保存错误信息到历史记录
            if "messages" in st.session_state:
                st.session_state.messages.append(
                    {"role": "system", "content": f"错误: {msg}", "is_intermediate": True}
                )
        elif type == PostEventType.post_message_update:
            self.cur_message += msg
            if extra.get("is_end"):
                self.cur_message_is_end = True
            self.update_streamlit_content(round_id)
        elif type == PostEventType.post_send_to_update:
            self.cur_send_to = extra["role"]
        elif type == PostEventType.post_status_update:
            self.cur_post_status = msg
            self.update_streamlit_content(round_id)
            # 保存状态更新到中间消息
            if msg.strip():
                self.intermediate_messages.append(
                    {"role": "assistant", "content": f"**状态**: {msg}", "is_intermediate": True}
                )
                # 更新会话状态
                if "messages" in st.session_state:
                    st.session_state.messages.append(self.intermediate_messages[-1])
        elif type == PostEventType.post_attachment_update:
            attachment_type = extra["type"]
            attachment_id = extra["id"]
            is_end = extra.get("is_end", False)

            existing_attachment = None
            for i, (aid, atype, content, _) in enumerate(self.cur_attachment_list):
                if aid == attachment_id:
                    existing_attachment = i
                    break

            if existing_attachment is not None:
                # 更新现有附件
                aid, atype, content, _ = self.cur_attachment_list[existing_attachment]
                self.cur_attachment_list[existing_attachment] = (aid, atype, content + msg, is_end)
            else:
                self.cur_attachment_list.append((attachment_id, attachment_type, msg, is_end))

            self.update_streamlit_content(round_id)

            # 保存附件更新到中间消息
            if is_end and attachment_type.name in ["plan", "execution_result", "text"]:
                content = ""
                if attachment_type.name == "plan_reasoning":
                    content = f"**思考过程**:\n```\n{msg}\n```"
                elif attachment_type.name == "plan":
                    content = f"**计划**:\n```\n{msg}\n```"
                elif attachment_type.name == "current_plan_step":
                    content = f"**当前计划**:\n```\n{msg}\n```"
                elif attachment_type.name == "execution_result":
                    content = f"**执行结果**:\n```\n{msg}\n```"
                elif attachment_type.name == "text":
                    content = msg

                if content.strip():
                    self.intermediate_messages.append(
                        {"role": "assistant", "content": content, "is_intermediate": True}
                    )
                    # 更新会话状态
                    if "messages" in st.session_state:
                        st.session_state.messages.append(self.intermediate_messages[-1])

    def update_streamlit_content(self, round_id: str):
        if round_id in self.placeholders:
            content, has_content = self.format_post_body()
            if has_content:
                self.placeholders[round_id].markdown(content, unsafe_allow_html=True)

    def format_post_body(self, is_end: bool = False) -> Tuple[str, bool]:
        has_content = False
        content = ""
        if self.cur_post_status:
            content += f"**状态**: {self.cur_post_status}\n\n"
            has_content = True

        if self.cur_message:
            content += f"{self.cur_message}\n\n"
            has_content = True

        for _, atype, amsg, _ in self.cur_attachment_list:
            display_types = ["plan", "execution_result", "text"]

            if atype.name in display_types:
                if atype.name == "plan_reasoning":
                    content += f"**思考过程**:\n```\n{amsg}\n```\n\n"
                    has_content = True
                elif atype.name == "plan":
                    content += f"**计划**:\n```\n{amsg}\n```\n\n"
                    has_content = True
                elif atype.name == "current_plan_step":
                    content += f"**当前计划**:\n```\n{amsg}\n```\n\n"
                    has_content = True
                elif atype.name == "execution_result":
                    content += f"**执行结果**:\n```\n{amsg}\n```\n\n"
                    has_content = True
                elif atype.name == "text":
                    content += f"{amsg}\n\n"
                    has_content = True

        return content, has_content