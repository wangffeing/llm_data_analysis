import React, { useState } from 'react';
import { Button, Switch, Tooltip } from 'antd';
import { DatabaseOutlined, PlusOutlined, SettingOutlined, SyncOutlined, SaveOutlined, KeyOutlined } from '@ant-design/icons';
import DataSourceModal from './DataSourceModal';
import { DescriptionUpdateMode } from '../hooks/useXChat';
import { DESIGN_GUIDE } from '../constants/appConstants'; // 导入分析指南
import logo from '../resource/logo.png';
import ConfigModal from './ConfigModal';
import AdminKeyManager from './AdminKeyManager'; // 新增
import { FileTextOutlined } from '@ant-design/icons';
import AnalysisGuide from './AnalysisGuide';
import HelpGuide from './HelpGuide';
import { QuestionCircleOutlined, ExperimentOutlined } from '@ant-design/icons';

interface ChatSiderProps {
  styles: any;
  loading: boolean;
  dataSources: any[];
  selectedDataSource: any;
  descriptionMode: DescriptionUpdateMode;
  onDescriptionModeChange: (mode: DescriptionUpdateMode) => void;
  onCreateNewSession: () => void;
  onDataSourceSelect: (dataSource: any) => void;
  onSubmit?: (value: string) => void;
  currentSession: string | null;
  onDataSourcesChange?: () => void;
  onOpenTemplateSelector?: () => void;
  onOpenGPTVisTest: () => void;
  attachedFiles?: any[]; // 新增：当前附加的文件
}

const ChatSider: React.FC<ChatSiderProps> = ({
  styles,
  loading,
  dataSources,
  selectedDataSource,
  descriptionMode,
  onDescriptionModeChange,
  onCreateNewSession,
  onDataSourceSelect,
  onSubmit,
  currentSession,
  onDataSourcesChange,
  onOpenTemplateSelector,
  onOpenGPTVisTest,
  attachedFiles = [], // 新增：添加attachedFiles参数并设置默认值
}) => {
  const [dataSourceModalVisible, setDataSourceModalVisible] = useState(false);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [adminKeyModalVisible, setAdminKeyModalVisible] = useState(false); // 新增
  const [guideVisible, setGuideVisible] = useState(false);
  const [helpVisible, setHelpVisible] = useState(false); // 新增帮助页面状态

  // 直接删除 uploadedFiles 的 useMemo 计算
  // 判断是否有数据源（数据库或文件）
  const hasDataSource = selectedDataSource || attachedFiles.length > 0;
  const dataSourceType = selectedDataSource ? 'database' : attachedFiles.length > 0 ? 'file' : 'none';

  // 处理分析指南点击
  const handleGuideClick = (guide: any) => {
    if (onSubmit && hasDataSource) {
      let prompt;
      if (selectedDataSource) {
        prompt = `请对 ${selectedDataSource.name} 数据集进行${guide.label}：${guide.description}`;
      } else if (attachedFiles.length > 0) {
        const fileNames = attachedFiles.map((f: any) => f.name).join('、');
        prompt = `请对已上传的文件（${fileNames}）进行${guide.label}：${guide.description}`;
      }
      if (prompt) {
        onSubmit(prompt);
      }
    }
  };

  return (
    <div className={styles.sider}>
      {/* Logo */}
      <div className={styles.logo}>
        <img 
          src={logo} 
          alt="Logo" 
          style={{ 
            width: 32, 
            height: 32, 
            marginRight: 8 
          }} 
        />
        <span>数据分析助手</span>
      </div>
      
      {/* 新建会话按钮 */}
      <Button
        onClick={onCreateNewSession}
        type="link"
        className={styles.addBtn}
        icon={<PlusOutlined />}
        disabled={loading}
        style={{ width: '100%', marginBottom: '16px', backgroundImage:'linear-gradient(123deg, #f0f9ff 0%, #f8f6ff 100%)' }}
      >
        新建会话
      </Button>

      {/* 占位符区域 - 根据是否选择数据源显示不同内容 */}
      <div style={{ 
        flex: 1, 
        minHeight: '200px',
        maxHeight: 'calc(100vh - 400px)', // 新增：限制最大高度，为底部按钮预留空间
        overflow: 'hidden', // 新增：隐藏溢出
        display: 'flex',
        flexDirection: 'column'
      }}>
        {hasDataSource ? (
          // 显示分析指南
          <div style={{ 
            padding: '12px',
            flex: 1,
            overflow: 'auto' // 新增：允许滚动
          }}>
            <div style={{ 
              marginBottom: '12px', 
              fontSize: '14px', 
              fontWeight: 'bold',
              color: dataSourceType === 'database' ? '#1677ff' : '#52c41a',
              position: 'sticky', // 新增：标题固定在顶部
              top: 0,
              backgroundColor: '#fff',
              zIndex: 1,
              paddingBottom: '8px'
            }}>
              {DESIGN_GUIDE.label}
              {dataSourceType === 'file' && (
                <span style={{ fontSize: '12px', fontWeight: 'normal', marginLeft: '8px' }}>
                  (基于上传文件)
                </span>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {DESIGN_GUIDE.children.map((guide) => (
                <div
                  key={guide.key}
                  onClick={() => handleGuideClick(guide)}
                  style={{
                    padding: '10px', // 减少内边距
                    border: '1px solid #f0f0f0',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    backgroundColor: '#fff',
                    backgroundImage: dataSourceType === 'database' 
                      ? 'linear-gradient(123deg, #f0f9ff 0%, #f8f6ff 100%)' 
                      : 'linear-gradient(123deg, #f6ffed 0%, #f0f9ff 100%)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = dataSourceType === 'database' ? '#1677ff' : '#52c41a';
                    e.currentTarget.style.backgroundColor = dataSourceType === 'database' ? '#f6f9ff' : '#f6ffed';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#f0f0f0';
                    e.currentTarget.style.backgroundColor = '#fff';
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px', // 减少间距
                    marginBottom: '3px' // 减少底部间距
                  }}>
                    {guide.icon}
                    <span style={{ 
                      fontSize: '13px', // 稍微减小字体
                      fontWeight: '500',
                      color: '#333'
                    }}>
                      {guide.label}
                    </span>
                  </div>
                  <div style={{ 
                    fontSize: '11px', // 减小描述字体
                    color: '#666',
                    lineHeight: '1.3', // 减小行高
                    paddingLeft: '20px' // 减少左边距
                  }}>
                    {guide.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          // 默认占位符
          <div style={{ 
            padding: '20px 12px', 
            textAlign: 'center', 
            color: '#999', 
            fontSize: '14px' 
          }}>
            选择数据源或上传文件
          </div>
        )}
      </div>

      {/* 思维链模式设置 - 移到底部 */}
      <div style={{ 
        marginBottom: '16px', 
        borderBottom: '1px solid #f0f0f0', 
        paddingBottom: '16px',
        flexShrink: 0 // 新增：防止被压缩
      }}>
        <div style={{ padding: '0 12px', marginBottom: '8px', fontSize: '12px', color: '#999' }}>
          思维链模式
        </div>
        <div style={{ padding: '0 12px' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            marginBottom: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {descriptionMode === 'replace' ? (
                <SyncOutlined style={{ fontSize: '14px', color: '#1677ff' }} />
              ) : (
                <SaveOutlined style={{ fontSize: '14px', color: '#52c41a' }} />
              )}
              <span style={{ fontSize: '14px' }}>
                {descriptionMode === 'replace' ? '实时更新' : '一直保留'}
              </span>
            </div>
            <Tooltip title={descriptionMode === 'replace' ? '切换到一直保留模式' : '切换到实时更新模式'}>
              <Switch
                size="small"
                checked={descriptionMode === 'keep'}
                onChange={(checked) => {
                  const newMode = checked ? 'keep' : 'replace';
                  onDescriptionModeChange(newMode);
                }}
                checkedChildren="保留"
                unCheckedChildren="更新"
              />
            </Tooltip>
          </div>
          <div style={{ fontSize: '12px', color: '#999', lineHeight: '1.4' }}>
            {descriptionMode === 'replace' 
              ? '思维链描述会实时更新显示最新内容' 
              : '思维链描述一直保留所有更新内容'
            }
          </div>
        </div>
      </div>

      {/* 数据源选择按钮 - 移到最底部 */}
      <div>
        <div style={{ padding: '0 12px', marginBottom: '8px', fontSize: '12px', color: '#999' }}>
          数据源
        </div>
        <Button
          onClick={() => setDataSourceModalVisible(true)}
          type="default"
          style={{
            width: '100%',
            height: 'auto',
            padding: '12px 16px',
            textAlign: 'center',     // 文字居中
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: selectedDataSource ? '1px solid #1677ff' : '1px solid #d9d9d9',
            backgroundImage: selectedDataSource 
              ? 'linear-gradient(123deg, #f0f9ff 0%, #f8f6ff 100%)' 
              : 'none',
            backgroundColor: selectedDataSource ? 'transparent' : '#fff',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            <DatabaseOutlined style={{ fontSize: '14px', color: selectedDataSource ? '#1677ff' : '#666' }} />
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '14px', fontWeight: selectedDataSource ? 'bold' : 'normal' }}>
                {selectedDataSource ? selectedDataSource.name : '选择数据源'}
              </div>
              {selectedDataSource?.description && (
                <div style={{ 
                  fontSize: '12px', 
                  color: '#999', 
                  marginTop: '2px',
                  wordWrap: 'break-word',
                  wordBreak: 'break-all',
                  whiteSpace: 'normal',
                  lineHeight: '1.4'
                }}>
                  {selectedDataSource.description}
                </div>
              )}
            </div>
          </div>
        </Button>
      </div>

      {/* 数据源选择模态框 */}
      <DataSourceModal
        visible={dataSourceModalVisible}
        dataSources={dataSources}
        selectedDataSource={selectedDataSource}
        onSelect={onDataSourceSelect}
        onCancel={() => setDataSourceModalVisible(false)}
        onDataSourcesChange={onDataSourcesChange} // 新增
      />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        <Button
          type="default"
          icon={<FileTextOutlined />}
          onClick={onOpenTemplateSelector}
          block
          style={{ 
            width: '100%',
            backgroundImage: 'linear-gradient(123deg,rgb(236, 251, 252) 0%,rgb(254, 243, 255) 100%)'
          }}
        >
          选择分析模板
        </Button>
        {/* <Button
          type="default"
          icon={<ExperimentOutlined />}
          onClick={onOpenGPTVisTest}
          block
          style={{ 
            width: '100%',
            marginTop: '8px',
            backgroundImage: 'linear-gradient(123deg,rgb(240, 248, 255) 0%,rgb(245, 245, 255) 100%)'
          }}
        >
          GPT-Vis 测试
        </Button> */}

        <div style={{ display: 'flex'}}>
          <Button
            onClick={() => setGuideVisible(true)}
            type="default"
            icon={<QuestionCircleOutlined />}
            style={{ 
              flex: 1,
              backgroundImage: 'linear-gradient(123deg,rgb(236, 251, 252) 0%,rgb(242, 242, 255) 100%)'
            }}
          >
            数据分析指引
          </Button>

          <Button
            onClick={() => setHelpVisible(true)}
            type="default"
            icon={<QuestionCircleOutlined />}
            style={{ 
              flex: 1,
              backgroundImage: 'linear-gradient(123deg,rgb(242, 242, 255) 0%,rgb(254, 243, 255) 100%)'
            }}
          >
            功能帮助
          </Button>
        </div>
      </div>

      <AnalysisGuide
        visible={guideVisible}
        onClose={() => setGuideVisible(false)}
        selectedDataSource={selectedDataSource}
        onSubmit={onSubmit} // 新增：传递提交函数
      />

      <HelpGuide
        visible={helpVisible}
        onClose={() => setHelpVisible(false)}
      />
      
      {/* 管理员密钥管理按钮 */}
      <Button 
        type="default" 
        icon={<KeyOutlined />}
        onClick={() => setAdminKeyModalVisible(true)}
        style={{ 
          width: '100%', 
          marginTop: 8,
          backgroundImage: 'linear-gradient(123deg,rgb(255, 248, 240) 0%,rgb(255, 243, 224) 100%)'
        }}
      >
        管理员密钥
      </Button>
      
      <Button 
        type="default" 
        icon={<SettingOutlined />}
        onClick={() => setConfigModalVisible(true)}
        style={{ width: '100%', marginTop: 8,
          backgroundImage: 'linear-gradient(123deg,rgb(250, 250, 250) 0%,rgb(238, 238, 238) 100%)'
         }}
        disabled={!currentSession}
      >
        会话配置
      </Button>
      
      {/* 管理员密钥管理模态框 */}
      <AdminKeyManager 
        visible={adminKeyModalVisible}
        onClose={() => setAdminKeyModalVisible(false)}
      />
      
      <ConfigModal 
        visible={configModalVisible}
        onClose={() => setConfigModalVisible(false)}
        sessionId={currentSession || ''} // 传递sessionId
      />
    </div>
  );
};

export default ChatSider;