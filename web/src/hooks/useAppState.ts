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

  const setupHeartbeatInterval = useCallback((sessionId: string) => {
    clearHeartbeatInterval();
    heartbeatIntervalRef.current = setInterval(async () => {
      try {
        await apiService.sessionHeartbeat(sessionId);
      } catch (error: any) {
        console.warn(`心跳失败: ${sessionId}`, error);
        
        // 如果是404错误，说明会话已被清理
        if (error.message?.includes('404') || error.response?.status === 404) {
          console.log('会话已被服务器清理，重置本地状态');
          setCurrentSession(null);
          clearHeartbeatInterval();
          messageApi?.warning('会话已过期，请创建新会话');
        }
      }
    }, 120 * 1000); // 改为2min，给后端更多缓冲时间
  }, [clearHeartbeatInterval, messageApi]);

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
      setFilePreview(null); // 新增：重置文件预览
      setAttachedFiles([]); // 新增：重置附件列表
      messageApi?.success('新会话已创建');
    } catch (error) {
      messageApi?.error('创建新会话失败');
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
      } catch (error) {
        messageApi?.error('获取数据预览失败');
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
    } catch (error) {
      messageApi?.error('刷新数据源失败');
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
      } catch (error) {
        messageApi?.error('应用初始化失败');
      } finally {
        setLoading(false);
      }
    };
    initializeApp();
    return () => {
      clearHeartbeatInterval();
    };
  }, [setupHeartbeatInterval, clearHeartbeatInterval, messageApi]);

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
  };
};

export default useAppState;