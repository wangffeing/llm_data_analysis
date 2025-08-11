// 更新导入，使用统一的类型定义
import { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import { useSSE, MessageType, type SSEMessage } from './useSSE';
import { apiService } from '../services/apiService';
// 移除message导入
// import { message } from 'antd';
import type { ThoughtStep, FileAttachment, ChatMessage } from '../types/appTypes';

// 修改配置类型
export type DescriptionUpdateMode = 'replace' | 'keep';

export interface ThoughtChainConfig {
  descriptionMode: DescriptionUpdateMode;
}

// 默认配置
const DEFAULT_CONFIG: ThoughtChainConfig = {
  descriptionMode: 'replace'
};

interface UseXChatProps {
  sessionId: string | null;
  selectedDataSource?: any;
  thoughtChainConfig?: Partial<ThoughtChainConfig>; 
  messageApi?: any; // 添加messageApi参数
}

export const useXChat = ({ sessionId, selectedDataSource, thoughtChainConfig, messageApi }: UseXChatProps) => {
  
  const config = useMemo(() => {
    const mergedConfig = {
      ...DEFAULT_CONFIG,
      ...thoughtChainConfig
    };
    return mergedConfig;
  }, [thoughtChainConfig]);
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [thoughtSteps, setThoughtSteps] = useState<ThoughtStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const currentMessageRef = useRef<string | null>(null);
  const thoughtStepsRef = useRef<ThoughtStep[]>([]);

  useEffect(() => {
    setMessages([]);
    setThoughtSteps([]);
    setIsLoading(false);
    currentMessageRef.current = null;
    thoughtStepsRef.current = [];
    console.log('🔄 会话ID变化，重置聊天状态:', sessionId);
  }, [sessionId]);

  const handleSSEMessage = useCallback((sseMessage: SSEMessage) => {
    
    switch (sseMessage.type) {
      case MessageType.ROUND_START:
        setIsLoading(true);
        setThoughtSteps([]); // 清空之前的思维链
        break;
        
      case MessageType.POST_START:
        const newStep: ThoughtStep = {
          id: sseMessage.data.post_id || `step-${Date.now()}`,
          title: `${sseMessage.data.role || 'AI'} 开始处理`,
          description: sseMessage.data.message || '正在处理您的请求',
          status: 'process',
          timestamp: sseMessage.timestamp,
          role: sseMessage.data.role,
          attachments: []
        };
        setThoughtSteps(prev => {
          const updated = [...prev, newStep];
          thoughtStepsRef.current = updated;
          return updated;
        });
        break;
        
      case MessageType.POST_STATUS_UPDATE:
        // setThoughtSteps(prev => {
        //   const updated = prev.map(step => {
        //     if (step.id === sseMessage.data.post_id) {
        //       const newStatus = sseMessage.data.status;
        //       return {
        //         ...step,
        //         description: updateDescription(
        //           step.description,
        //           newStatus || '',
        //           '**状态：** '
        //         ),
        //         status: 'process' as const
        //       } as ThoughtStep;
        //     }
        //     return step;
        //   });
        //   thoughtStepsRef.current = updated;
        //   return updated;
        // });
        break;
        
      case MessageType.POST_ATTACHMENT_UPDATE:
        setThoughtSteps(prev => {
          const updated = prev.map(step => {
            if (step.id === sseMessage.data.post_id) {
              const attachment = sseMessage.data.attachment;
              const newAttachments = [...(step.attachments || [])];
              
              const existingIndex = newAttachments.findIndex(a => a.id === attachment.id);
              if (existingIndex >= 0) {
                newAttachments[existingIndex] = attachment;
              } else {
                newAttachments.push(attachment);
              }
              
              let updatedStep = { ...step, attachments: newAttachments };
              
              switch (attachment.type) {
                case 'plan_reasoning':
                  updatedStep.title = '分析推理';
                  updatedStep.description = updateDescription(
                    step.description,
                    attachment.content,
                    '**推理过程：**\n'
                  );
                  break;
                case 'plan':
                  updatedStep.title = '制定计划';
                  updatedStep.description = updateDescription(
                    step.description,
                    attachment.content,
                    '**计划制定：** '
                  );
                  break;
                case 'current_plan_step':
                  updatedStep.title = '执行步骤';
                  updatedStep.description = updateDescription(
                    step.description,
                    attachment.content,
                    '**当前步骤：**\n'
                  );
                  break;
                case 'thought':
                  updatedStep.title = '思考过程';
                  updatedStep.description = updateDescription(
                    step.description,
                    attachment.content,
                    '**思考：**\n'
                  );
                  break;
                case 'execution_result':
                  updatedStep.title = '执行结果';
                  updatedStep.description = updateDescription(
                    step.description,
                    '执行完成',
                    '**'
                  );
                  updatedStep.content = attachment.content;
                  break;
              }
              
              return updatedStep;
            }
            return step;
          });
          thoughtStepsRef.current = updated;
          return updated;
        });
        break;
        
      case MessageType.POST_MESSAGE_UPDATE:
        if (sseMessage.data.is_complete) {
          setThoughtSteps(prev => {
            const updated = prev.map(step => {
              if (step.id === sseMessage.data.post_id) {
                return {
                  ...step,
                  content: sseMessage.data.content,
                  status: 'finish' as const
                } as ThoughtStep;
              }
              return step;
            });
            thoughtStepsRef.current = updated;
            return updated;
          });
        }
        break;
        
      case MessageType.POST_END:
        setThoughtSteps(prev => {
          const updated = prev.map(step => {
            if (step.id === sseMessage.data.post_id) {
              return {
                ...step,
                status: 'finish' as const,
                content: sseMessage.data.final_message || step.content
              } as ThoughtStep;
            }
            return step;
          });
          thoughtStepsRef.current = updated;
          return updated;
        });
        break;
        
      case MessageType.ROUND_END:
        setIsLoading(false);
        // 保持思维链显示一段时间后清理
        // setTimeout(() => {
        //   setThoughtSteps([]);
        //   thoughtStepsRef.current = [];
        // }, 300);
        break;
        
      case MessageType.CHAT_COMPLETED:
        setIsLoading(false);
        
        if (sseMessage.data.response) {
          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: sseMessage.data.response,
            timestamp: sseMessage.timestamp,
            status: 'delivered',
            thoughtSteps: [...thoughtStepsRef.current], 
            files: sseMessage.data.files || [] 
          };
          
          setMessages(prev => [...prev, assistantMessage]);
          
          setThoughtSteps([]);
          thoughtStepsRef.current = [];
        }
        break;
        
      case MessageType.POST_ERROR:
        console.error('❌ 步骤执行错误:', sseMessage.data);
        
        setThoughtSteps(prev => {
          const updated = prev.map(step => {
            if (step.id === sseMessage.data.post_id) {
              return {
                ...step,
                status: 'error' as const,
                content: sseMessage.data.error_message || sseMessage.data.message || '执行出现错误'
              } as ThoughtStep;
            }
            return step;
          });
          thoughtStepsRef.current = updated;
          return updated;
        });
        
        messageApi?.error(sseMessage.data.error_message || sseMessage.data.message || '步骤执行失败');
        setIsLoading(false);
        break;
        
      case MessageType.ROUND_ERROR:
        console.error('❌ 对话轮次错误:', sseMessage.data);
        
        setIsLoading(false);
        setThoughtSteps([]);
        thoughtStepsRef.current = [];
        
        messageApi?.error(sseMessage.data.error_message || sseMessage.data.message || '对话处理失败');
        
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `❌ 处理失败：${sseMessage.data.error_message || sseMessage.data.message || '未知错误'}`,
          timestamp: sseMessage.timestamp,
          status: 'error'
        };
        setMessages(prev => [...prev, errorMessage]);
        break;
        
      case MessageType.ERROR:
        console.error('❌ 系统错误:', sseMessage.data);
        setIsLoading(false);
        
        const errorMsg = sseMessage.data.error || sseMessage.data.message || '系统错误';
        messageApi?.error(errorMsg);
        
        if (currentMessageRef.current) {
          setMessages(prev => prev.map(msg => 
            msg.id === currentMessageRef.current 
              ? { ...msg, status: 'error' }
              : msg
          ));
        }
        break;
    }
  }, [config, messageApi]);

  const { isConnected, connectionStatus } = useSSE({
    sessionId,
    onMessage: handleSSEMessage,
    onError: (error) => {
      console.error('❌ SSE错误:', error);
      setIsLoading(false);
      
      setThoughtSteps([]);
      thoughtStepsRef.current = [];
      
      if (currentMessageRef.current) {
        setMessages(prev => prev.map(msg => 
          msg.id === currentMessageRef.current 
            ? { ...msg, status: 'error' }
            : msg
        ));
      }
    },
    messageApi // 传递messageApi
  });

  // 修改 sendMessage 方法，移除 templateId 参数
  const sendMessage = useCallback(async (content: string, attachedFiles?: any[]) => {
    if (!content.trim()) return;
    if (!sessionId || !isConnected) {
      messageApi?.error('请先创建会话');
      return;
    }
  
    // 移除这部分验证，让App.tsx统一处理
    // if (!hasUploadedFiles && !selectedDataSource && (!attachedFiles || attachedFiles.length === 0)) {
    //   messageApi?.error('请先选择数据源或上传文件');
    //   return;
    // }
  
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
      status: 'sending',
      files: attachedFiles?.map(file => ({
        id: file.uid || `file-${Date.now()}`,
        name: file.name || '',
        type: file.type || '',
        size: file.size || 0,
        path: file.path || file.url || '',
      })) || []
    };
    
    setMessages(prev => [...prev, userMessage]);
    currentMessageRef.current = userMessage.id;
  
    try {
      let uploadedFiles = [];
      
      if (attachedFiles && attachedFiles.length > 0) {
        const loadingKey = 'uploading';
        messageApi?.loading({ content: '正在上传文件...', key: loadingKey, duration: 0 });
        
        const files = attachedFiles.map(file => file.originFileObj || file);
        const uploadResponse = await apiService.uploadFiles(files);
        uploadedFiles = uploadResponse.uploaded_files;
        
        messageApi?.destroy(loadingKey);
        messageApi?.success(`成功上传 ${uploadedFiles.length} 个文件`);
      }
      
      const messageData: any = {
        content,
      };
      
      if (selectedDataSource) {
        messageData.selected_table = selectedDataSource.name;
      }
      
      if (uploadedFiles.length > 0) {
        messageData.uploaded_files = uploadedFiles;
      }
      
      // 移除：不再传递模板ID
      // if (templateId) {
      //   messageData.template_id = templateId;
      // }
      
      await apiService.sendChatMessage(sessionId, messageData);
      
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'sent' }
          : msg
      ));      
    } catch (error) {
      console.error('❌ 发送消息失败:', error);
      messageApi?.destroy();
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'error' }
          : msg
      ));
      messageApi?.error('发送消息失败，请检查网络连接或重新创建会话');
    }
  }, [sessionId, selectedDataSource, isConnected, messageApi]); 

  const updateDescription = useCallback((currentDescription: string | undefined, newContent: string, prefix: string): string => {
    const fullNewContent = `${prefix}${newContent}`;
        
    switch (config.descriptionMode) {
      case 'replace':
        return fullNewContent;
        
      case 'keep':
        return currentDescription 
          ? `${currentDescription}\n\n${fullNewContent}` 
          : fullNewContent;
      default:
        return fullNewContent;
    }
  }, [config.descriptionMode]);

  return {
    messages,
    thoughtSteps,
    isLoading,
    isConnected,
    connectionStatus,
    sendMessage
  };
};