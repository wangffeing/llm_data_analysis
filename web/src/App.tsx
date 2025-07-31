
import React, { useState, useRef, useCallback, useMemo } from 'react';
import './App.css';
import { Spin, App as AntdApp } from 'antd';
import ChatSider from './components/ChatSider';
import ChatList from './components/ChatList';
import ChatSender from './components/ChatSender';
import TemplateSelector from './components/TemplateSelector';
import ReportViewer from './components/ReportViewer';
import ErrorBoundary from './components/ErrorBoundary';
import { useAppStyles } from './styles/appStyles';
import { useAppState } from './hooks/useAppState';
import { useXChat, DescriptionUpdateMode } from './hooks/useXChat';
import { HOT_TOPICS, DESIGN_GUIDE, SENDER_PROMPTS } from './constants/appConstants';
import { handleError, withErrorHandling } from './utils/errorUtils';
import ConnectionStatus from './components/ConnectionStatus';
import GPTVisTestPage from './components/GPTVisTestPage';

function AppContent() {
  const { message } = AntdApp.useApp();
  const { styles } = useAppStyles();
  const abortController = useRef<AbortController>(null);
  
  const [descriptionMode, setDescriptionMode] = useState<DescriptionUpdateMode>('replace');
  
  // 新增：模板和报告相关状态
  const [templateSelectorVisible, setTemplateSelectorVisible] = useState(false);
  const [reportViewerVisible, setReportViewerVisible] = useState(false);
  const [currentAnalysisResults, setCurrentAnalysisResults] = useState<any>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | undefined>(undefined);
  const [gptVisTestVisible, setGptVisTestVisible] = useState(false);

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

  // 新增：生成智能报告
  const handleGenerateReport = useCallback((analysisResults: any) => {
    setCurrentAnalysisResults(analysisResults);
    setReportViewerVisible(true);
  }, []);

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
  
    if (!selectedDataSource && (!attachedFiles || attachedFiles.length === 0)) {
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
  }, 'sendMessage', message), [selectedDataSource, attachedFiles, isConnected, sendMessage, setAttachedFiles, setAttachmentsOpen, checkSessionValidity, message]);

  // 错误处理函数，传递messageApi
  const handleAppError = useCallback((error: Error, errorInfo: React.ErrorInfo) => {
    handleError(error, 'App组件错误', message);
  }, [message]);
  const handleOpenGPTVisTest = useCallback(() => {
    setGptVisTestVisible(true);
  }, []);

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
        {/* 添加全局连接状态显示 */}
        <div style={{ position: 'fixed', top: 10, right: 10, zIndex: 1000 }}>
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
            // 新增：GPT-Vis 测试页面
            onOpenGPTVisTest={handleOpenGPTVisTest}
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