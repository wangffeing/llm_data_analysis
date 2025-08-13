import time
from typing import Dict, Callable
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from functools import wraps

class RateLimiter:
    """简单的频率限制器"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """检查是否允许请求"""
        now = time.time()
        window_start = now - window_seconds
        
        # 清理过期的请求记录
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        # 检查当前窗口内的请求数
        if len(self.requests[key]) >= max_requests:
            return False
        
        # 记录当前请求
        self.requests[key].append(now)
        return True

# 全局频率限制器实例
rate_limiter = RateLimiter()

def rate_limit(limit_str: str):
    """
    频率限制装饰器
    
    Args:
        limit_str: 限制字符串，格式如 "5/minute", "10/hour", "100/day"
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 解析限制配置
            parts = limit_str.split('/')
            if len(parts) != 2:
                raise ValueError("无效的频率限制格式")
            
            max_requests = int(parts[0])
            unit = parts[1].lower()
            
            # 转换时间单位为秒
            time_windows = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }
            
            window_seconds = time_windows.get(unit)
            if window_seconds is None:
                raise ValueError(f"不支持的时间单位: {unit}")
            
            # 获取客户端标识
            client_ip = getattr(request.client, 'host', 'unknown')
            endpoint = f"{request.method}:{request.url.path}"
            key = f"{client_ip}:{endpoint}"
            
            # 检查频率限制
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，限制: {limit_str}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator