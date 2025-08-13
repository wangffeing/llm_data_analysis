import { useState, useRef, useCallback, useEffect } from 'react';

// 消息类型定义（对应后端SSE消息类型）
export enum MessageType {
  ROUND_START = 'round_start',
  ROUND_END = 'round_end',
  ROUND_ERROR = 'error',
  POST_START = 'post_start',
  POST_END = 'post_end',
  POST_ERROR = 'post_error',
  POST_MESSAGE_UPDATE = 'post_message_update',
  POST_STATUS_UPDATE = 'post_status_update',
  POST_ATTACHMENT_UPDATE = 'post_attachment_update',
  POST_SEND_TO_UPDATE = 'post_send_to_update',
  CHAT_COMPLETED = 'chat_completed',
  THOUGHT_STEP_UPDATE = 'thought_step_update',
  FILE_GENERATED = 'file_generated',
  ERROR = 'error',
  HEARTBEAT = 'heartbeat'
}

// 导出SSEMessage接口
export interface SSEMessage {
  id: string;
  type: MessageType;
  data: Record<string, any>;
  timestamp: string;
  session_id: string;
}

interface UseSSEProps {
  sessionId: string | null;
  onMessage?: (message: SSEMessage) => void;
  onError?: (error: Error) => void;
  messageApi?: any; // 添加messageApi参数
}

export const useSSE = ({ sessionId, onMessage, onError, messageApi }: UseSSEProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [retryCount, setRetryCount] = useState(0);

  const eventSourceRef = useRef<EventSource | null>(null);
  const maxRetries = 3;
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef(false); // 防止重复连接
  const currentSessionIdRef = useRef<string | null>(null);

  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const cleanup = useCallback(() => {

    // 清理EventSource连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    // 清理所有定时器
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }
    
    // 重置状态
    isConnectingRef.current = false;
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const scheduleRetry = useCallback(() => {
    // 防止重复调度重试
    if (retryTimeoutRef.current) {
      return;
    }

    if (retryCount < maxRetries) {
      const delay = 1000 * Math.pow(2, retryCount); // 指数退避
      console.log(`🔄 计划重试连接，延迟 ${delay}ms，当前重试次数: ${retryCount}`);

      retryTimeoutRef.current = setTimeout(() => {
        retryTimeoutRef.current = null;
        setRetryCount(prev => prev + 1);
        // 直接调用连接，而不是通过useEffect
        connectInternal();
      }, delay);
    } else {
      console.log('❌ 达到最大重试次数，停止重试');
      setConnectionStatus('error');
      isConnectingRef.current = false;
    }
  }, [retryCount, maxRetries]);

  const connectInternal = useCallback(() => {
    const currentSessionId = currentSessionIdRef.current;
    
    if (!currentSessionId) {
      console.log('❌ 无sessionId，跳过连接');
      return;
    }

    // 防止重复连接
    if (isConnectingRef.current || eventSourceRef.current?.readyState === EventSource.OPEN) {
      console.log('⚠️ 连接已存在或正在连接中，跳过');
      return;
    }
    isConnectingRef.current = true;

    // 清理现有连接
    cleanup();
    isConnectingRef.current = true; // cleanup会重置这个值，需要重新设置

    setConnectionStatus('connecting');
    const url = `http://localhost:8000/api/chat/stream/${currentSessionId}`;

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      // 连接超时处理
      connectionTimeoutRef.current = setTimeout(() => {
        if (eventSource.readyState === EventSource.CONNECTING) {
          console.log('⏰ 连接超时，关闭连接');
          eventSource.close();
          isConnectingRef.current = false;
          setConnectionStatus('error');
          messageApi?.error('连接超时，请检查后端服务是否启动');
          scheduleRetry();
        }
      }, 5000);

      eventSource.onopen = (event) => {
        
        if (connectionTimeoutRef.current) {
          clearTimeout(connectionTimeoutRef.current);
          connectionTimeoutRef.current = null;
        }
        
        isConnectingRef.current = false;
        setIsConnected(true);
        setConnectionStatus('connected');
        setRetryCount(0); // 重置重试计数
      };

      // 注册消息监听器
      Object.values(MessageType).forEach(messageType => {
        eventSource.addEventListener(messageType, (event: MessageEvent) => {
          try {
            const eventData = JSON.parse(event.data);
            const sseMessage: SSEMessage = {
              id: eventData.id || `msg_${Date.now()}`,
              type: messageType,
              data: eventData,
              timestamp: eventData.timestamp || new Date().toISOString(),
              session_id: eventData.session_id || currentSessionId
            };
            if (onMessageRef.current) {
              onMessageRef.current(sseMessage);
            }
          } catch (error) {
            console.error(`❌ 解析${messageType}消息失败:`, error);
            if (onErrorRef.current) {
              onErrorRef.current(error as Error);
            }
          }
        });
      });

      eventSource.onmessage = (event) => {
        try {
          const eventData = JSON.parse(event.data);
          const messageType = eventData.type || 'heartbeat';
          const sseMessage: SSEMessage = {
            id: eventData.id || event.lastEventId || `msg_${Date.now()}`,
            type: messageType as MessageType,
            data: eventData,
            timestamp: eventData.timestamp || new Date().toISOString(),
            session_id: eventData.session_id || currentSessionId
          };
          if (onMessageRef.current) {
            onMessageRef.current(sseMessage);
          }
        } catch (error) {
          console.error('❌ 解析通用SSE消息失败:', error, 'Raw data:', event.data);
          if (onErrorRef.current) {
            onErrorRef.current(error as Error);
          }
        }
      };

      eventSource.onerror = (error) => {
        console.error('❌ SSE连接错误:', error);
        isConnectingRef.current = false;
        setIsConnected(false);
        setConnectionStatus('error');
        
        if (onErrorRef.current) {
          onErrorRef.current(new Error('SSE连接中断，请检查网络连接'));
        }
        
        // 只有在当前session仍然有效时才重试
        if (currentSessionIdRef.current === currentSessionId) {
          scheduleRetry();
        }
      };
    } catch (error) {
      console.error('❌ 创建EventSource失败:', error);
      isConnectingRef.current = false;
      if (onErrorRef.current) {
        onErrorRef.current(error as Error);
      }
      setConnectionStatus('error');
      scheduleRetry();
    }
  }, [cleanup, scheduleRetry]);

  const connect = useCallback(() => {
    currentSessionIdRef.current = sessionId;
    setRetryCount(0); // 重置重试计数
    connectInternal();
  }, [sessionId, connectInternal]);

  // 主要的useEffect，只监听sessionId变化
  useEffect(() => {
    console.log(`🔄 sessionId变化: ${sessionId}`);
    
    if (sessionId) {
      currentSessionIdRef.current = sessionId;
      connect();
    } else {
      currentSessionIdRef.current = null;
      cleanup();
    }

    return () => {
      console.log(`🧹 useEffect清理, sessionId: ${sessionId}`);
      cleanup();
    };
  }, [sessionId]); // 只依赖sessionId，移除retryCount依赖

  // 手动重连方法
  const reconnect = useCallback(() => {
    setRetryCount(0);
    connect();
  }, [connect]);

  return { 
    isConnected, 
    connectionStatus, 
    reconnect, // 暴露手动重连方法
    retryCount 
  };
};