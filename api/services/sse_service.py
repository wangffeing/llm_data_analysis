import asyncio
import json
import logging
import uuid
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List, AsyncGenerator, Optional, Set
from enum import Enum
from weakref import WeakSet, ref

logger = logging.getLogger(__name__)

class SSEMessageType(Enum):
    """SSE消息类型"""
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    POST_START = "post_start"
    POST_END = "post_end"
    POST_ERROR = "post_error"
    POST_MESSAGE_UPDATE = "post_message_update"
    POST_ATTACHMENT_UPDATE = "post_attachment_update"
    POST_STATE_UPDATE = "post_status_update"
    POST_SEND_TO_UPDATE = "post_send_to_update"
    FILE_GENERATED = "file_generated"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    SESSION_CREATED = "session_created"
    CHAT_COMPLETED = "chat_completed"
    SHUTDOWN = "shutdown"

class SSEJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理枚举和其他特殊类型"""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class SSEMessage:
    """SSE消息数据结构"""
    def __init__(self, message_type: SSEMessageType, data: Dict[str, Any], session_id: str):
        self.id = f"msg_{int(datetime.now().timestamp() * 1000000)}_{uuid.uuid4().hex[:8]}"
        self.type = message_type
        self.data = data
        self.session_id = session_id
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "session_id": self.session_id,
            "timestamp": self.timestamp
        }
    
    def format_for_sse(self) -> str:
        """格式化为SSE标准数据格式"""
        try:
            safe_data = {
                "session_id": self.session_id,
                "timestamp": self.timestamp,
                **self.data
            }
            data_str = json.dumps(safe_data, ensure_ascii=False, cls=SSEJSONEncoder)
            lines = [f"id: {self.id}", f"event: {self.type.value}"]
            lines.extend([f"data: {line}" for line in data_str.split('\n')])
            lines.append("")
            return "\n".join(lines) + "\n"
        except Exception as e:
            logger.error(f"SSE格式化失败: {e}")
            return f"id: error_{int(datetime.now().timestamp())}\nevent: error\ndata: {{\"error\": \"格式化失败\"}}\n\n"

class ConnectionManager:
    """连接管理器，负责管理单个会话的所有连接 - 使用WeakSet自动清理"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        # 使用WeakSet自动处理连接的垃圾回收
        self.connections: WeakSet = WeakSet()
        # 保存连接的弱引用回调，用于清理
        self._connection_refs: Dict[int, ref] = {}
        self.lock = asyncio.Lock()
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    async def add_connection(self, queue: asyncio.Queue):
        """添加连接"""
        async with self.lock:
            # 添加到WeakSet
            self.connections.add(queue)
            
            # 创建弱引用回调，当连接被垃圾回收时自动清理
            def cleanup_callback(weak_ref):
                # 从引用字典中移除
                queue_id = id(queue)
                if queue_id in self._connection_refs:
                    del self._connection_refs[queue_id]
                logger.debug(f"会话 {self.session_id} 连接已被垃圾回收")
            
            # 保存弱引用
            queue_id = id(queue)
            self._connection_refs[queue_id] = ref(queue, cleanup_callback)
            
            self.last_activity = datetime.now()
            logger.info(f"会话 {self.session_id} 添加连接，当前连接数: {len(self.connections)}")
    
    async def remove_connection(self, queue: asyncio.Queue):
        """移除连接"""
        async with self.lock:
            # WeakSet会自动处理，但我们可以显式移除
            self.connections.discard(queue)
            
            # 清理弱引用
            queue_id = id(queue)
            if queue_id in self._connection_refs:
                del self._connection_refs[queue_id]
            
            self.last_activity = datetime.now()
            logger.info(f"会话 {self.session_id} 移除连接，当前连接数: {len(self.connections)}")
    
    async def broadcast_message(self, formatted_data: str):
        """向所有连接广播消息"""
        async with self.lock:
            if not self.connections:
                return
            
            # 创建连接列表的副本，避免在迭代时修改
            active_connections = list(self.connections)
            
            for queue in active_connections:
                try:
                    # 检查队列是否仍然有效
                    if queue.qsize() >= queue.maxsize:
                        logger.warning(f"会话 {self.session_id} 队列满，丢弃消息")
                        continue
                    
                    queue.put_nowait(formatted_data)
                except asyncio.QueueFull:
                    logger.warning(f"会话 {self.session_id} 队列满，丢弃消息")
                except Exception as e:
                    logger.error(f"会话 {self.session_id} 发送失败: {e}")
                    # WeakSet会自动清理无效连接，无需手动移除
            
            self.last_activity = datetime.now()
    
    def is_empty(self) -> bool:
        """检查是否没有活跃连接"""
        return len(self.connections) == 0
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.connections)
    
    def cleanup(self):
        """清理所有连接引用"""
        self.connections.clear()
        self._connection_refs.clear()
        logger.info(f"会话 {self.session_id} 连接管理器已清理")

class SSEService:
    """改进的SSE服务：支持多会话、多连接、心跳、同步调用、安全关闭"""

    def __init__(self):
        self._session_managers: Dict[str, ConnectionManager] = {}
        self._running: bool = True
        self._global_lock = asyncio.Lock()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self._total_messages_sent = 0
        self._total_connections_created = 0
        self._start_time = datetime.now()

    def configure(self, loop: asyncio.AbstractEventLoop):
        """配置事件循环并启动后台任务"""
        self.loop = loop
        
        # 启动心跳任务
        self._heartbeat_task = loop.create_task(self._heartbeat_worker())
        
        # 启动清理任务
        self._cleanup_task = loop.create_task(self._cleanup_worker())
        
        logger.info("SSE服务已配置并启动后台任务")

    async def add_connection(self, session_id: str) -> AsyncGenerator[str, None]:
        """注册新连接，开始推送数据流"""
        queue = asyncio.Queue(maxsize=500)
        connection_id = uuid.uuid4().hex[:8]
        
        # 获取或创建会话管理器
        async with self._global_lock:
            if session_id not in self._session_managers:
                self._session_managers[session_id] = ConnectionManager(session_id)
            session_manager = self._session_managers[session_id]
        
        await session_manager.add_connection(queue)
        self._total_connections_created += 1
        
        logger.info(f"添加SSE连接 session={session_id} conn={connection_id}")

        # 发送连接确认消息
        await self.send_message(session_id, SSEMessageType.HEARTBEAT, {
            "message": "连接已建立",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        })

        try:
            while self._running:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield data
                except asyncio.TimeoutError:
                    # 发送心跳
                    heartbeat = SSEMessage(
                        session_id=session_id,
                        message_type=SSEMessageType.HEARTBEAT,
                        data={"message": "heartbeat", "timestamp": datetime.now().isoformat()}
                    )
                    yield heartbeat.format_for_sse()
                except asyncio.CancelledError:
                    logger.info(f"客户端取消连接 session={session_id} conn={connection_id}")
                    break
        except Exception as e:
            logger.error(f"SSE连接错误 session={session_id} conn={connection_id}: {e}")
            await self.send_message(session_id, SSEMessageType.ERROR, {"message": "连接错误"})
        finally:
            await session_manager.remove_connection(queue)
            
            # 如果会话没有连接了，清理会话管理器
            async with self._global_lock:
                if session_manager.is_empty():
                    if session_id in self._session_managers:
                        del self._session_managers[session_id]
                        logger.info(f"清理空会话管理器: {session_id}")

    async def send_message(self, session_id: str, message_type: SSEMessageType, data: Dict[str, Any]):
        if not self._running:
            logger.warning("SSE服务未运行，跳过发送")
            return

        message = SSEMessage(message_type, data, session_id)
        formatted_data = message.format_for_sse()

        async with self._global_lock:
            if session_id not in self._session_managers:
                logger.debug(f"会话 {session_id} 不存在，跳过发送")
                return
            session_manager = self._session_managers[session_id]

        await session_manager.broadcast_message(formatted_data)
        self._total_messages_sent += 1
        
        logger.debug(f"发送消息 session={session_id} type={message_type.value}")

    def send_message_from_sync(self, session_id: str, message_type: SSEMessageType, data: Dict[str, Any]):
        if not self._running or not self.loop:
            logger.warning("无法从同步发送SSE：服务未配置或已关闭")
            return

        try:
            asyncio.run_coroutine_threadsafe(
                self.send_message(session_id, message_type, data),
                self.loop
            )
        except Exception as e:
            logger.error(f"同步发送SSE消息失败: {e}")

    async def _heartbeat_worker(self):
        while self._running:
            try:
                await asyncio.sleep(30)
                
                if not self._running:
                    break
                
                async with self._global_lock:
                    session_ids = list(self._session_managers.keys())
                
                for session_id in session_ids:
                    await self.send_message(session_id, SSEMessageType.HEARTBEAT, {
                        "message": "定期心跳",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳工作器错误: {e}")

    async def _cleanup_worker(self):
        while self._running:
            try:
                await asyncio.sleep(300)
                
                if not self._running:
                    break
                
                async with self._global_lock:
                    empty_sessions = [
                        session_id for session_id, manager in self._session_managers.items()
                        if manager.is_empty()
                    ]
                    for session_id in empty_sessions:
                        del self._session_managers[session_id]
                        logger.info(f"清理空会话: {session_id}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理工作器错误: {e}")

    async def cleanup(self):
        self._running = False
        logger.info("SSE服务关闭中，通知所有连接...")

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        async with self._global_lock:
            for session_id, session_manager in self._session_managers.items():
                shutdown_msg = SSEMessage(
                    message_type=SSEMessageType.SHUTDOWN,
                    data={"message": "服务即将关闭"},
                    session_id=session_id
                ).format_for_sse()
                await session_manager.broadcast_message(shutdown_msg)
            self._session_managers.clear()
        logger.info("SSE服务清理完成")

    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        total_connections = sum(
            manager.get_connection_count() 
            for manager in self._session_managers.values()
        )
        
        return {
            "running": self._running,
            "total_sessions": len(self._session_managers),
            "total_connections": total_connections,
            "total_messages_sent": self._total_messages_sent,
            "total_connections_created": self._total_connections_created,
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
            "session_details": {
                session_id: {
                    "connection_count": manager.get_connection_count(),
                    "created_at": manager.created_at.isoformat(),
                    "last_activity": manager.last_activity.isoformat()
                }
                for session_id, manager in self._session_managers.items()
            }
        }
