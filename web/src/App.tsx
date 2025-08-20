
import React, { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import './App.css';
import { Spin, App as AntdApp } from 'antd';
import ChatSider from './components/ChatSider';
import ChatList from './components/ChatList';
import ChatSender from './components/ChatSender';
import TemplateSelector from './components/TemplateSelector';
import ReportViewer from './components/ReportViewer';
import ErrorBoundary from './components/ErrorBoundary';
import UserVerification from './components/UserVerification';
import { useAppStyles } from './styles/appStyles';
import { useAppState } from './hooks/useAppState';
import { useXChat, DescriptionUpdateMode } from './hooks/useXChat';
import { HOT_TOPICS, DESIGN_GUIDE, SENDER_PROMPTS } from './constants/appConstants';
import { handleError, withErrorHandling } from './utils/errorUtils';
import ConnectionStatus from './components/ConnectionStatus';
import GPTVisTestPage from './components/GPTVisTestPage';
import { apiService } from './services/apiService';

function AppContent() {
  const { message } = AntdApp.useApp();
  const { styles } = useAppStyles();
  const abortController = useRef<AbortController>(null);
  
  // 用户验证状态
  const [isUserVerified, setIsUserVerified] = useState(false);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [checkingUserStatus, setCheckingUserStatus] = useState(true);
  const [userVerificationEnabled, setUserVerificationEnabled] = useState(true);
  
  const [descriptionMode, setDescriptionMode] = useState<DescriptionUpdateMode>('keep');
  
  // 新增：模板和报告相关状态
  const [templateSelectorVisible, setTemplateSelectorVisible] = useState(false);
  const [reportViewerVisible, setReportViewerVisible] = useState(false);
  const [currentAnalysisResults, setCurrentAnalysisResults] = useState<any>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | undefined>(undefined);
  const [gptVisTestVisible, setGptVisTestVisible] = useState(false);

  // 检查用户验证是否启用和用户登录状态
  useEffect(() => {
    const checkUserStatus = async () => {
      // 检查URL参数
      const urlParams = new URLSearchParams(window.location.search);
      const urlAppCode = urlParams.get('appCode');
      const urlToken = urlParams.get('token');
      
      if (urlAppCode && urlToken) {
        // 自动验证URL参数
        try {
          const response = await apiService.verifyUser(
            urlAppCode.replace(/"/g, ''), // 移除引号
            urlToken.replace(/"/g, '')
          );
          
          if (response.success) {
            // 保存用户信息并设置验证状态
            const userInfo = {
              user_id: response.user_id,
              username: response.username,
              app_code: urlAppCode.replace(/"/g, ''),
              permissions: response.permissions || []
            };
            
            sessionStorage.setItem('user_info', JSON.stringify(userInfo));
            sessionStorage.setItem('app_code', urlAppCode.replace(/"/g, ''));
            sessionStorage.setItem('user_token', urlToken.replace(/"/g, ''));
            
            setUserInfo(userInfo);
            setIsUserVerified(true);
            setCheckingUserStatus(false); // 添加这行，设置检查状态为false
            
            // 清除URL参数并刷新页面状态
            const newUrl = window.location.origin + window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
            
            return;
          }
        } catch (error) {
          console.error('URL参数验证失败:', error);
        }
      }
      
      try {
        // 首先检查后端是否启用了用户验证
        const systemStatus = await apiService.getSystemStatus();
        const verificationEnabled = systemStatus.user_verification_enabled;
        setUserVerificationEnabled(verificationEnabled);
        
        if (!verificationEnabled) {
          // 如果未启用用户验证，直接设置为已验证状态
          setIsUserVerified(true);
          setUserInfo({
            user_id: 'default_user',
            username: '默认用户',
            app_code: 'default',
            permissions: ['data_analysis', 'report_generation']
          });
          return;
        }
        
        // 如果启用了用户验证，检查sessionStorage中是否有用户信息
        const storedUserInfo = sessionStorage.getItem('user_info');
        const appCode = sessionStorage.getItem('app_code');
        const userToken = sessionStorage.getItem('user_token');
        
        if (storedUserInfo && appCode && userToken) {
          // 验证会话是否仍然有效
          const status = await apiService.getUserStatus();
          if (status.is_logged_in && status.user_info) {
            setUserInfo(status.user_info);
            setIsUserVerified(true);
          } else {
            // 清除无效的用户信息
            sessionStorage.removeItem('user_info');
            sessionStorage.removeItem('app_code');
            sessionStorage.removeItem('user_token');
          }
        }
      } catch (error) {
        console.log('用户状态检查失败');
        if (userVerificationEnabled) {
          // 如果启用了验证但检查失败，清除可能无效的用户信息
          sessionStorage.removeItem('user_info');
          sessionStorage.removeItem('app_code');
          sessionStorage.removeItem('user_token');
        } else {
          // 如果未启用验证，设置默认状态
          setIsUserVerified(true);
          setUserInfo({
            user_id: 'default_user',
            username: '默认用户',
            app_code: 'default',
            permissions: ['data_analysis', 'report_generation']
          });
        }
      } finally {
        setCheckingUserStatus(false);
      }
    };

    checkUserStatus();
  }, [userVerificationEnabled]);

  // 监听认证过期事件
  useEffect(() => {
    const handleAuthExpired = () => {
      setIsUserVerified(false);
      setUserInfo(null);
      message.warning('登录已过期，请重新验证');
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => window.removeEventListener('auth:expired', handleAuthExpired);
  }, [message]);

  // 用户验证成功处理
  const handleUserVerified = useCallback((userData: any) => {
    setUserInfo(userData);
    setIsUserVerified(true);
    message.success(`欢迎，${userData.username}！`);
  }, [message]);

  // 用户登出处理
  const handleUserLogout = useCallback(async () => {
    try {
      await apiService.userLogout();
      setIsUserVerified(false);
      setUserInfo(null);
      sessionStorage.removeItem('user_info');
      sessionStorage.removeItem('app_code');
      sessionStorage.removeItem('user_token');
      message.success('已成功登出');
    } catch (error) {
      console.error('登出失败:', error);
      // 即使登出失败，也清除本地状态
      setIsUserVerified(false);
      setUserInfo(null);
      sessionStorage.removeItem('user_info');
      sessionStorage.removeItem('app_code');
      sessionStorage.removeItem('user_token');
      message.warning('登出请求失败，但已清除本地登录状态');
    }
  }, [message]);

  // 使用简化的状态管理，传递messageApi
  const {
    attachmentsOpen,
    attachedFiles,
    inputValue,
    dataSources,
    loading,
    selectedDataSource,
    currentSession,
    setAttachmentsOpen,
    setAttachedFiles,
    setInputValue,
    createNewSession,
    handleDataSourceSelect,
    dataPreview,
    checkSessionValidity,
    refreshDataSources,
    filePreview,
    setFilePreview,
  } = useAppState(message);

  // 配置思维链模式
  const thoughtChainConfig = useMemo(() => ({
    descriptionMode
  }), [descriptionMode]);
  
  // 优化描述模式变更处理
  const handleDescriptionModeChange = useCallback(
    (newMode: DescriptionUpdateMode) => setDescriptionMode(newMode),
    []
  );
  
  // 使用增强的聊天Hook，传递messageApi
  const {
    messages,
    thoughtSteps,
    isLoading,
    isConnected,
    connectionStatus,
    sendMessage
  } = useXChat({
    sessionId: currentSession,
    selectedDataSource,
    thoughtChainConfig,
    messageApi: message
  });

  // 新增：模板选择处理
  const handleTemplateSelect = useCallback((templateId: string, prompt: string) => {
    setSelectedTemplateId(templateId);
    setInputValue(prompt);
    setTemplateSelectorVisible(false);
    message.success('模板已选择，分析提示已生成');
  }, [setInputValue, message]);

  // 新增：打开模板选择器
  const handleOpenTemplateSelector = useCallback(() => {
    if (!selectedDataSource && (!attachedFiles || attachedFiles.length === 0)) {
      message.warning('请先选择数据源或上传文件');
      return;
    }
    setTemplateSelectorVisible(true);
  }, [selectedDataSource, attachedFiles, message]);

  // 改进：生成智能报告
  // 修改handleGenerateReport函数，改为基于session_id生成报告
  // 修改handleGenerateReport函数，修复TypeScript错误
  const handleGenerateReport = useCallback(async (reportData: any) => {
    console.log('收到报告生成请求:', reportData);
    
    try {
      // 显示加载状态
      message.loading('正在生成智能报告...', 0);
      
      // 使用apiService调用后端API
      const result = await apiService.generateIntelligentReport({
        session_id: currentSession || 'default_session',
        template_id: 'comprehensive',
        config: {
          include_executive_summary: true,
          include_detailed_analysis: true,
          include_recommendations: true,
          include_appendix: true,
          language: 'zh-CN'
        }
      });
      
      message.destroy(); // 清除loading消息
      
      if (result.success) {
        // 设置报告数据并显示报告查看器
        setCurrentAnalysisResults(result);
        setSelectedTemplateId('comprehensive');
        setReportViewerVisible(true);
        
        message.success('智能报告生成成功！');
      } else {
        throw new Error('报告生成失败');
      }
      
    } catch (error) {
      message.destroy();
      console.error('报告生成失败:', error);
      // 修复error类型问题
      const errorMessage = error instanceof Error ? error.message : String(error);
      message.error(`报告生成失败: ${errorMessage}`);
    }
  }, [message, currentSession]);

  const getDataColumns = useCallback(() => {
    // 如果有选中的数据源，使用原始字段名
    if (selectedDataSource?.table_columns) {
      return selectedDataSource.table_columns;
    }
    // 如果是文件预览，继续使用列名
    if (dataPreview?.columns) {
      return dataPreview.columns;
    }
    if (filePreview?.columns) {
      return filePreview.columns;
    }
    return [];
  }, [selectedDataSource, dataPreview, filePreview]);


  // 优化消息发送处理，使用传递的messageApi
  // 修改onSubmit方法，不传递templateId
  const onSubmit = useCallback(withErrorHandling(async (val: string) => {
    if (!val) return;
  
    // 检查会话中是否已经有过文件上传的历史
    const hasUploadedFiles = messages.some(msg => msg.files && msg.files.length > 0);
    
    // 修改验证逻辑：如果会话中已有文件上传历史，则不强制要求数据源
    if (!hasUploadedFiles && !selectedDataSource && (!attachedFiles || attachedFiles.length === 0)) {
      message.error('请先选择数据源或上传文件');
      return;
    }
    
    if (!isConnected) {
      message.error('连接未建立，请稍后重试');
      return;
    }
  
    const isValid = await checkSessionValidity();
    if (!isValid) {
      message.error('会话已失效，请创建新会话');
      return;
    }
  
    // 修改：不再传递模板ID，因为模板内容已经包含在prompt中
    await sendMessage(val, attachedFiles);
  
    setAttachedFiles([]);
    setAttachmentsOpen(false);
    setSelectedTemplateId(undefined); 
  }, 'sendMessage', message), [messages, selectedDataSource, attachedFiles, isConnected, sendMessage, setAttachedFiles, setAttachmentsOpen, checkSessionValidity, message]);

  // 错误处理函数，传递messageApi
  const handleAppError = useCallback((error: Error, errorInfo: React.ErrorInfo) => {
    handleError(error, 'App组件错误', message);
  }, [message]);
  const handleOpenGPTVisTest = useCallback(() => {
    setGptVisTestVisible(true);
  }, []);

  // 如果正在检查用户状态，显示加载界面
  if (checkingUserStatus) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        background: '#f0f2f5'
      }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px', fontSize: '16px', color: '#555' }}>
          正在检查用户状态...
        </div>
      </div>
    );
  }

  // 如果启用了用户验证但用户未验证，显示验证组件
  if (userVerificationEnabled && !isUserVerified) {
    return (
      <UserVerification
        visible={true}
        onVerificationSuccess={handleUserVerified}
        onCancel={() => {
          // 用户取消验证时的处理逻辑
          message.warning('需要验证身份才能使用系统');
        }}
      />
    );
  }

  // Loading状态
  if (loading && !currentSession) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        background: '#f0f2f5'
      }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px', fontSize: '16px', color: '#555' }}>
          正在初始化应用...
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary onError={handleAppError}>
      <div className={styles.layout}>
        {/* 添加全局连接状态显示和用户信息 */}
        <div style={{ position: 'fixed', top: 10, right: 10, zIndex: 1000, display: 'flex', gap: '10px', alignItems: 'center' }}>
          {/* 用户信息显示 */}
          {userInfo && (
            <div style={{ 
              background: 'rgba(255, 255, 255, 0.9)', 
              padding: '8px 12px', 
              borderRadius: '6px',
              fontSize: '12px',
              color: '#666',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>用户: {userInfo.username}</span>
              <span>|</span>
              <span>应用: {userInfo.app_code}</span>
              <button 
                onClick={handleUserLogout}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#1890ff',
                  cursor: 'pointer',
                  fontSize: '12px',
                  padding: '0',
                  textDecoration: 'underline'
                }}
              >
                登出
              </button>
            </div>
          )}
          <ConnectionStatus 
            connectionStatus={connectionStatus}
            isConnected={isConnected}
          />
        </div>
        <ErrorBoundary 
          onError={handleAppError}
          fallback={
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <p>侧边栏加载失败，请刷新页面重试</p>
            </div>
          }
        >
          <ChatSider
            styles={styles}
            loading={loading}
            dataSources={dataSources}
            selectedDataSource={selectedDataSource}
            descriptionMode={descriptionMode}
            onDescriptionModeChange={handleDescriptionModeChange}
            onCreateNewSession={createNewSession}
            onDataSourceSelect={handleDataSourceSelect}
            onSubmit={onSubmit}
            currentSession={currentSession}
            onDataSourcesChange={refreshDataSources}
            onOpenTemplateSelector={handleOpenTemplateSelector}
            onOpenGPTVisTest={handleOpenGPTVisTest}
            attachedFiles={attachedFiles}
          />
        </ErrorBoundary>
        
        <div className={styles.chat}>
          <ErrorBoundary 
            onError={handleAppError}
            fallback={
              <div style={{ padding: '20px', textAlign: 'center' }}>
                <p>聊天区域加载失败，请刷新页面重试</p>
              </div>
            }
          >
            <ChatList
              messages={messages}
              selectedDataSource={selectedDataSource}
              styles={styles}
              hotTopics={HOT_TOPICS}
              designGuide={DESIGN_GUIDE}
              onSubmit={onSubmit}
              thoughtSteps={thoughtSteps}
              isLoading={isLoading}
              dataPreview={dataPreview}
              filePreview={filePreview}
              // 新增：报告生成功能
              onGenerateReport={handleGenerateReport}
            />
          </ErrorBoundary>
          
          <ErrorBoundary 
            onError={handleAppError}
            fallback={
              <div style={{ padding: '20px', textAlign: 'center' }}>
                <p>输入区域加载失败，请刷新页面重试</p>
              </div>
            }
          >
            <ChatSender
              inputValue={inputValue}
              attachmentsOpen={attachmentsOpen}
              attachedFiles={attachedFiles}
              selectedDataSource={selectedDataSource}
              styles={styles}
              senderPrompts={SENDER_PROMPTS}
              abortController={abortController}
              onSubmit={onSubmit}
              setInputValue={setInputValue}
              setAttachmentsOpen={setAttachmentsOpen}
              setAttachedFiles={setAttachedFiles}
              isLoading={isLoading}
              connectionStatus={connectionStatus}
              setFilePreview={setFilePreview}
              // 新增：模板选择功能
              onOpenTemplateSelector={handleOpenTemplateSelector}
              // 新增：传递messages用于判断会话状态
              messages={messages}
            />
          </ErrorBoundary>
        </div>
        
        {/* 新增：模板选择器 */}
        <TemplateSelector
          visible={templateSelectorVisible}
          onClose={() => setTemplateSelectorVisible(false)}
          onSelect={handleTemplateSelect}
          dataColumns={getDataColumns()}
        />
        
        {/* 新增：报告查看器 */}
        <ReportViewer
          visible={reportViewerVisible}
          onClose={() => setReportViewerVisible(false)}
          analysisResults={currentAnalysisResults}
          templateId={selectedTemplateId}
        />
        <GPTVisTestPage
          visible={gptVisTestVisible}
          onClose={() => setGptVisTestVisible(false)}
        />
      </div>
    </ErrorBoundary>
  );
}

function App() {
  return (
    <AntdApp>
      <AppContent />
    </AntdApp>
  );
}

export default App;