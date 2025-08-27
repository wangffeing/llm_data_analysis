import { useState, useEffect, useCallback, useRef } from 'react';
import { type GetProp } from 'antd';
import { Attachments } from '@ant-design/x';
import { apiService } from '../services/apiService';
import { DataSource } from '../types/appTypes';

export const useAppState = (messageApi?: any) => {
  const [attachmentsOpen, setAttachmentsOpen] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<GetProp<typeof Attachments, 'items'>>([]);
  const [inputValue, setInputValue] = useState('');
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true); // 初始为true
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [dataPreview, setDataPreview] = useState<any>(null);
  const [filePreview, setFilePreview] = useState<any>(null); // 新增文件预览状态
  const [previewLoading, setPreviewLoading] = useState(false);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const clearHeartbeatInterval = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // 新增：完整状态重置函数
  const resetAllState = useCallback(() => {
    setCurrentSession(null);
    setSelectedDataSource(null);
    setDataPreview(null);
    setFilePreview(null);
    setAttachedFiles([]);
    setInputValue('');
    clearHeartbeatInterval();
    console.log('✅ 所有状态已重置');
  }, [clearHeartbeatInterval]);

  const setupHeartbeatInterval = useCallback((sessionId: string) => {
    clearHeartbeatInterval();
    heartbeatIntervalRef.current = setInterval(async () => {
      try {
        await apiService.sessionHeartbeat(sessionId);
      } catch (error: any) {
        console.warn(`心跳失败: ${sessionId}`, error);
        
        // 如果是404错误，说明会话已被清理
        if (error.message?.includes('404') || error.response?.status === 404 || error.message?.includes('会话已过期')) {
          console.log('会话已被服务器清理，重置本地状态');
          resetAllState();
          messageApi?.warning('会话已过期，请创建新会话');
        }
      }
    }, 120 * 1000); // 改为2min，给后端更多缓冲时间
  }, [clearHeartbeatInterval, resetAllState, messageApi]);

  const createNewSession = useCallback(async () => {
    if (loading) return;
    try {
      setLoading(true);
      clearHeartbeatInterval();
      
      if (currentSession) {
        try {
          await apiService.sessionHeartbeat(currentSession);
          await apiService.deleteSession(currentSession);
          console.log(`成功删除旧会话: ${currentSession}`);
        } catch (error: any) {
          if (error.message?.includes('404') || error.response?.status === 404) {
            console.log(`旧会话 ${currentSession} 已经不存在，跳过删除`);
          } else {
            console.warn('删除旧会话失败:', error);
          }
        }
      }
      
      const response = await apiService.createSession();
      setCurrentSession(response.session_id);
      setupHeartbeatInterval(response.session_id);
      setSelectedDataSource(null);
      setDataPreview(null);
      setFilePreview(null);
      setAttachedFiles([]);
      messageApi?.success('新会话已创建');
    } catch (error: any) {
      // 修复：将错误信息合并到消息中
      const errorMessage = error?.message || error?.toString() || '未知错误';
      messageApi?.error(`创建新会话失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, [loading, currentSession, clearHeartbeatInterval, setupHeartbeatInterval, messageApi]);

  const checkSessionValidity = useCallback(async () => {
    if (!currentSession) return false;
    try {
      await apiService.sessionHeartbeat(currentSession);
      return true;
    } catch (error) {
      console.warn('Session is invalid:', currentSession);
      setCurrentSession(null);
      clearHeartbeatInterval();
      return false;
    }
  }, [currentSession, clearHeartbeatInterval]);

  const handleDataSourceSelect = useCallback(async (dataSource: DataSource) => {
    setSelectedDataSource(dataSource);
    if (dataSource?.name) {
      setPreviewLoading(true);
      try {
        const preview = await apiService.getDataPreview(dataSource.name, 10);
        setDataPreview(preview);
      } catch (error: any) {
        // 修复：添加错误详细信息
        const errorMessage = error?.message || error?.toString() || '未知错误';
        messageApi?.error(`获取数据预览失败: ${errorMessage}`);
        setDataPreview(null);
      } finally {
        setPreviewLoading(false);
      }
    } else {
      setDataPreview(null);
    }
  }, [messageApi]);

  const refreshDataSources = useCallback(async () => {
    try {
      const dataSourcesResponse = await apiService.getDataSources();
      const formattedDataSources = dataSourcesResponse.data_sources.map((ds: any) => ({ ...ds }));
      setDataSources(formattedDataSources);
    } catch (error: any) {
      // 修复：添加错误详细信息
      const errorMessage = error?.message || error?.toString() || '未知错误';
      messageApi?.error(`刷新数据源失败: ${errorMessage}`);
    }
  }, [messageApi]);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        const dataSourcesResponse = await apiService.getDataSources();
        const formattedDataSources = dataSourcesResponse.data_sources.map((ds: any) => ({ ...ds }));
        setDataSources(formattedDataSources);
        
        const sessionResponse = await apiService.createSession();
        setCurrentSession(sessionResponse.session_id);
        setupHeartbeatInterval(sessionResponse.session_id);
      } catch (error: any) {
        // 修复：添加错误详细信息
        const errorMessage = error?.message || error?.toString() || '未知错误';
        messageApi?.error(`应用初始化失败: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    initializeApp();

    // 监听全局状态重置事件
    const handleSessionInvalid = (event: CustomEvent) => {
      console.log('收到会话无效事件:', event.detail);
      resetAllState();
      messageApi?.warning('会话已过期，请创建新会话');
    };

    window.addEventListener('session:invalid', handleSessionInvalid as EventListener);

    return () => {
      clearHeartbeatInterval();
      window.removeEventListener('session:invalid', handleSessionInvalid as EventListener);
    };
  }, [setupHeartbeatInterval, clearHeartbeatInterval, resetAllState, messageApi]);

  return {
    attachmentsOpen,
    attachedFiles,
    inputValue,
    dataSources,
    loading,
    selectedDataSource,
    currentSession,
    dataPreview,
    previewLoading,
    setAttachmentsOpen,
    setAttachedFiles,
    setInputValue,
    setDataSources,
    setLoading,
    setSelectedDataSource,
    setCurrentSession,
    setDataPreview,
    createNewSession,
    handleDataSourceSelect,
    checkSessionValidity,
    refreshDataSources,
    filePreview,
    setFilePreview,
    resetAllState, // 新增导出
  };
};

export default useAppState;