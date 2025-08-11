import React, { useMemo, useRef, useEffect, useCallback } from 'react';
import { Bubble, ThoughtChain, Welcome, Prompts } from '@ant-design/x';
import { Avatar, Space, Flex, Spin, Image, Button, Typography } from 'antd';
import { RobotOutlined, UserOutlined, DownloadOutlined, FileOutlined, FileTextOutlined } from '@ant-design/icons';
import type { ThoughtStep, ChatMessage, FileAttachment } from '../types/appTypes';
import markdownComponents from './markdownComponents';
import { handleError } from '../utils/errorUtils';
import logo from '../resource/logo1.png';
import ReactMarkdown from 'react-markdown';
import DataTable from './DataTable';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-json';
import 'prismjs/themes/prism.css';
import Robot from '../resource/role2.png';
import GPTVisChart from './GPTVisChart';
import { GPTVis } from '@antv/gpt-vis';

const { Text } = Typography;

const mapStepsToThoughtChainItems = (
  steps: ThoughtStep[], 
  mapThoughtStatus: (status: string, role?: string, content?: string) => 'pending' | 'success' | 'error'
) => {
  if (!steps || steps.length === 0) return [];
  return steps.map(step => {
    const trimmedDescription = step.description ? step.description.trim() : step.description;
    const trimmedContent = step.content ? step.content.trim() : step.content;
    const detectedStatus = mapThoughtStatus(step.status, step.role, trimmedContent);
    const isCodeInterpreterError = step.role === 'CodeInterpreter' && detectedStatus === 'error';
    return {
      title: step.title,
      description: trimmedDescription ? (
        <div className="thought-description" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{trimmedDescription}</div>
      ) : trimmedDescription,
      status: detectedStatus,
      content: trimmedContent ? (
        <div className="thought-content">
          {step.role === 'CodeInterpreter' ? (
            <ReactMarkdown components={markdownComponents}>{trimmedContent}</ReactMarkdown>
          ) : (
            <ReactMarkdown>{trimmedContent}</ReactMarkdown>
          )}
        </div>
      ) : trimmedContent,
      extra: step.role ? (
        <span style={{
          fontSize: '12px',
          color: isCodeInterpreterError ? '#ff4d4f' : '#666',
          background: isCodeInterpreterError ? '#fff2f0' : '#f0f0f0',
          padding: '2px 6px',
          borderRadius: '4px',
          border: isCodeInterpreterError ? '1px solid #ffccc7' : 'none'
        }}>
          {isCodeInterpreterError ? '代码执行失败' : step.role}
        </span>
      ) : null
    };
  });
};

interface ChatListProps {
  messages: ChatMessage[];
  thoughtSteps: ThoughtStep[];
  isLoading: boolean;
  selectedDataSource: any;
  styles: any;
  hotTopics: any;
  designGuide: any;
  onSubmit: (val: string) => void;
  dataPreview?: any;
  filePreview?: any;
  onGenerateReport?: (analysisResults: any) => void;  // 新增
}


const ChatList: React.FC<ChatListProps> = React.memo(({
  messages,
  thoughtSteps,
  isLoading,
  selectedDataSource,
  styles,
  hotTopics,
  designGuide,
  onSubmit,
  dataPreview,
  filePreview,
  onGenerateReport,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const safeBase64Decode = useCallback((content: string): string => {
    try {
      const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
      
      if (!base64Regex.test(content)) {
        return content;
      }
      
      const binaryString = atob(content);
      
      try {
        const bytes = Uint8Array.from(binaryString, c => c.charCodeAt(0));
        return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
      } catch (utf8Error) {
        try {
          // 尝试GBK解码
          const bytes = Uint8Array.from(binaryString, c => c.charCodeAt(0));
          return new TextDecoder('gbk', { fatal: false }).decode(bytes);
        } catch (gbkError) {
          // 如果都失败，返回原始内容
          return content;
        }
      }
    } catch (error) {
      console.warn('Base64解码失败，返回原始内容:', error);
      return content;
    }
  }, []);

  const detectPythonError = useCallback((content: string): boolean => {
    if (!content) return false;
    const errorPatterns = [
      /Traceback \(most recent call last\):/i, /Error:/i, /Exception:/i, /SyntaxError:/i,
      /NameError:/i, /TypeError:/i, /ValueError:/i, /IndexError:/i, /KeyError:/i,
      /AttributeError:/i, /ImportError:/i, /ModuleNotFoundError:/i, /FileNotFoundError:/i,
      /ZeroDivisionError:/i, /RuntimeError:/i, /IndentationError:/i, /TabError:/i,
      /UnboundLocalError:/i, /RecursionError:/i, /MemoryError:/i, /OverflowError:/i,
      /FloatingPointError:/i, /AssertionError:/i, /SystemError:/i, /EOFError:/i,
      /KeyboardInterrupt:/i, /GeneratorExit:/i, /StopIteration:/i, /StopAsyncIteration:/i,
      /ArithmeticError:/i, /LookupError:/i, /EnvironmentError:/i, /OSError:/i, /WindowsError:/i,
      /BlockingIOError:/i, /ChildProcessError:/i, /ConnectionError:/i, /BrokenPipeError:/i,
      /ConnectionAbortedError:/i, /ConnectionRefusedError:/i, /ConnectionResetError:/i,
      /FileExistsError:/i, /IsADirectoryError:/i, /NotADirectoryError:/i, /PermissionError:/i,
      /ProcessLookupError:/i, /TimeoutError:/i, /UnicodeError:/i, /UnicodeDecodeError:/i,
      /UnicodeEncodeError:/i, /UnicodeTranslateError:/i, /Warning:/i, /UserWarning:/i,
      /DeprecationWarning:/i, /PendingDeprecationWarning:/i, /SyntaxWarning:/i,
      /RuntimeWarning:/i, /FutureWarning:/i, /ImportWarning:/i, /UnicodeWarning:/i,
      /BytesWarning:/i, /ResourceWarning:/i, /execution failed/i, /failed to execute/i,
      /execution error/i, /code execution failed/i, /\[ERROR\]/i, /ERROR:/i, /FAILED:/i, /FAILURE:/i
    ];
    return errorPatterns.some(pattern => pattern.test(content));
  }, []);
  const renderReportButton = useCallback((message: any) => {
    // 更精确的分析结果检测逻辑
    if (message.role === 'assistant' && message.content) {
      const content = message.content.toLowerCase();
      
      // 多维度检测分析结果
      const hasAnalysisKeywords = (
        // 关键词检测
        content.includes('分析结果') || 
        content.includes('数据分析') ||
        content.includes('统计结果') ||
        content.includes('分析报告') ||
        content.includes('数据统计') ||
        content.includes('分析完成') ||
        (content.includes('数据') && (content.includes('分析') || content.includes('统计'))) ||
        
        // 数据表格检测
        message.files?.some((file: any) => 
          file.mime_type === 'antd' || 
          file.type === 'table' ||
          file.name?.includes('分析') ||
          file.name?.includes('统计') ||
          file.name?.endsWith('.csv') ||
          file.name?.endsWith('.xlsx')
        ) ||
        
        // 数据预览检测
        message.dataPreview ||
        
        // 图表检测
        content.includes('图表') ||
        content.includes('可视化') ||
        content.includes('chart') ||
        
        // 模板分析检测
        message.template_id ||
        
        // 数值统计检测
        /\d+.*?%/.test(content) || // 百分比
        /平均.*?\d+/.test(content) || // 平均值
        /总计.*?\d+/.test(content) || // 总计
        /最大.*?\d+/.test(content) || // 最大值
        /最小.*?\d+/.test(content)    // 最小值
      );
    
      // 排除非分析内容
      const isNotAnalysis = (
        content.includes('请提供') ||
        content.includes('需要更多信息') ||
        content.includes('无法分析') ||
        content.includes('数据格式错误') ||
        content.includes('文件上传失败')
      );
    
      if (hasAnalysisKeywords && !isNotAnalysis) {
        return (
          <div style={{ marginTop: '12px', textAlign: 'right' }}>
            <Button
              type="primary"
              size="small"
              icon={<FileTextOutlined />}
              // 修改报告按钮的onClick事件，简化传递的数据
              onClick={() => onGenerateReport && onGenerateReport({
                message_id: message.id,
                // 从当前会话获取session_id，而不是从message对象
                // 不再传递完整的分析结果，只传递必要的标识信息
                })}
              >
                生成智能报告
              </Button>
            </div>
          );
        }
      }
    return null;
  }, [onGenerateReport]);
  
  const mapThoughtStatus = useMemo(() => (status: string, role?: string, content?: string) => {
    if (role === 'CodeInterpreter' && content) {
      if (detectPythonError(content)) {
        return 'error';
      }
    }
    switch (status) {
      case 'wait':
      case 'process':
        return 'pending';
      case 'finish':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'pending';
    }
  }, [detectPythonError]);

  const hasActiveThinking = useMemo(() => 
    thoughtSteps.some(step => step.status === 'process' || step.status === 'wait'),
    [thoughtSteps]
  );

  const renderFileContent = useCallback((file: FileAttachment): React.ReactElement => {
    try {
      const { name, type, path, content, mime_type } = file;
      if (!content) {
        return (
          <div style={{ padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', margin: '8px 0', display: 'flex', alignItems: 'center', gap: '8px'}}>
            <FileOutlined /> <Text>{name}</Text>
          </div>
        );
      }
      const downloadFile = () => {
        try {
          if (!content) {
            console.warn('文件内容为空，无法下载');
            return;
          }
          let blob: Blob;
          
          // 检查content是否是有效的base64字符串
          const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
          const isValidBase64 = base64Regex.test(content.replace(/\s/g, ''));
          
          if (isValidBase64) {
            // 如果是有效的base64，按原来的方式处理
            try {
              const binaryString = atob(content);
              const bytes = new Uint8Array(binaryString.length);
              for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
              }
              blob = new Blob([bytes], { type: mime_type || 'application/octet-stream' });
            } catch (atobError) {
              // 如果atob失败，尝试使用fetch方式
              const dataUrl = `data:${mime_type || 'application/octet-stream'};base64,${content}`;
              fetch(dataUrl)
                .then(res => res.blob())
                .then(downloadBlob)
                .catch(error => {
                  console.error('Fetch方式下载失败:', error);
                  // 最后的备用方案：直接将内容作为文本处理
                  fallbackTextDownload();
                });
              return;
            }
          } else {
            // 如果不是base64，直接作为文本内容处理
            console.log('内容不是有效的base64，作为文本处理');
            fallbackTextDownload();
            return;
          }
          
          // 下载blob
          downloadBlob(blob);
          
        } catch (error) {
          console.error('文件下载失败:', error);
          handleError(error, '文件下载');
        }
        
        // 辅助函数：下载blob
        function downloadBlob(blob: Blob) {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = name;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }

        function fallbackTextDownload() {
          if (!content) {
            console.warn('文件内容为空，无法下载');
            return;
          }
          const blob = new Blob([content], { 
            type: mime_type || 'text/plain;charset=utf-8' 
          });
          downloadBlob(blob);
        }        
      };
      
      switch (mime_type) {
        case 'image':
          return (
            <div style={{ margin: '8px 0' }}>
              <Image
                src={`data:${mime_type};base64,${content}`}
                alt={name}
                style={{ maxWidth: '100%', maxHeight: '400px' }}
                preview={{ mask: '预览图片' }}
              />
              <div style={{ marginTop: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>{name}</Text>
                <Button size="small" icon={<DownloadOutlined />} onClick={downloadFile}>
                  下载
                </Button>
              </div>
            </div>
          );
        
        case 'gpt_vis':
          try {
            const decodedContent = safeBase64Decode(content);
            
            return (
              <div style={{ margin: '8px 0' }}>
                <GPTVisChart 
                  content={decodedContent}
                />
                <div style={{ marginTop: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>{name}</Text>
                  <Button size="small" icon={<DownloadOutlined />} onClick={downloadFile}>
                    下载
                  </Button>
                </div>
              </div>
            );
          } catch (error) {
            handleError(error, 'GPT-Vis Chart渲染');
            return (
              <div style={{ padding: '12px', border: '1px solid #ff4d4f', borderRadius: '6px', margin: '8px 0', background: '#fff2f0' }}>
                <Text type="danger">无法渲染GPT-Vis图表: {name}。数据格式可能存在问题。</Text>
              </div>
            );
          }
          
        case 'text':
        case 'code':
          // 使用安全的解码函数
          const textContent = safeBase64Decode(content);
          return (
            <div style={{ margin: '8px 0' }}>
              <div style={{
                background: '#f6f8fa',
                border: '1px solid #e1e4e8',
                borderRadius: '6px',
                padding: '12px',
                maxHeight: '300px',
                overflow: 'auto'
              }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                  {textContent}
                </pre>
              </div>
              <div style={{ marginTop: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>{name}</Text>
                <Button size="small" icon={<DownloadOutlined />} onClick={downloadFile}>
                  下载
                </Button>
              </div>
            </div>
          );
          
        case 'csv':
        case 'excel':
        case 'application/vnd.ms-excel': {
          let parsedData: any[] = [];
          let columns: any[] = [];

          try {
            const binaryString = safeBase64Decode(content);
            const MAX_ROWS = 10;

            if (typeof path === 'string' && path.endsWith('.csv')) {
              const result = Papa.parse(binaryString, {
                header: true,
                skipEmptyLines: true,
                transform: (value) => {
                  return value === null || value === undefined || value.trim() === '' ? '-' : value;
                }
              });

              parsedData = result.data
                .filter(row => row && Object.keys(row).length > 0 && Object.values(row).some(val => val !== '-'))
                .slice(0, MAX_ROWS); // 👈 限制前10条

              if (parsedData.length > 0 && result.meta?.fields) {
                columns = result.meta.fields.map(field => ({ title: field, dataIndex: field, key: field }));
              }

            } else if (typeof path === 'string' && (path.endsWith('.xlsx') || path.endsWith('.xls'))) {
              const bytes = Uint8Array.from(binaryString, c => c.charCodeAt(0));
              const workbook = XLSX.read(bytes, { type: 'array' });
              const sheetName = workbook.SheetNames[0];
              const worksheet = workbook.Sheets[sheetName];
              parsedData = XLSX.utils.sheet_to_json(worksheet)
                .filter(row => row && typeof row === 'object' && !Array.isArray(row))
                .slice(0, MAX_ROWS); // 👈 限制前10条

              if (parsedData.length > 0) {
                columns = Object.keys(parsedData[0]).map(key => ({ title: key, dataIndex: key, key }));
              }
            }

            return (
              <div style={{
                padding: '12px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                margin: '8px 0',
                background: '#fafafa'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <FileOutlined style={{ color: '#52c41a' }} />
                  <Text strong>{name}</Text>
                  <Text type="secondary">（预览前 {parsedData.length} 条）</Text>
                </div>
                {parsedData.length > 0 && columns.length > 0 ? (
                  <DataTable
                    sourceName={name}
                    columns={columns}
                    data={parsedData}
                    totalShown={parsedData.length}
                    maxHeight={300}
                  />
                ) : (
                  <Text type="secondary">文件内容为空或无法解析为表格数据。</Text>
                )}
                <div style={{ marginTop: '8px', textAlign: 'right' }}>
                  <Button size="small" icon={<DownloadOutlined />} onClick={downloadFile} type="primary">
                    下载文件
                  </Button>
                </div>
              </div>
            );
          } catch (error) {
            handleError(error, 'CSV/Excel文件解析');
            return (
              <div style={{
                padding: '12px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                margin: '8px 0',
                background: '#fafafa'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <FileOutlined style={{ color: '#ff4d4f' }} />
                  <Text strong>{name}</Text>
                  <Text type="danger">文件解析失败或内容损坏。</Text>
                </div>
                <Button size="small" icon={<DownloadOutlined />} onClick={downloadFile} type="primary">
                  下载文件
                </Button>
              </div>
            );
          }
        }

        default:
          return (
            <div style={{ 
              padding: '12px', 
              border: '1px solid #d9d9d9', 
              borderRadius: '6px',
              margin: '8px 0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <FileOutlined />
                <Text strong>{name}</Text>
              </div>
              <Button size="small" icon={<DownloadOutlined />} onClick={downloadFile}>
                下载文件
              </Button>
            </div>
          );
      }
    } catch (error) {
      handleError(error, 'renderFileContent');
      return (
        <div style={{ padding: '12px', border: '1px solid #ff4d4f', borderRadius: '6px', margin: '8px 0', background: '#fff2f0' }}>
          <Text type="danger">文件渲染失败</Text>
        </div>
      );
    }
  }, [safeBase64Decode, handleError]);

  const renderedMessages = useMemo(() => {
    return messages?.map((msg) => {
      const isAssistant = msg.role === 'assistant';
  
      if (isAssistant) {
        const messageThoughtSteps = msg.thoughtSteps && msg.thoughtSteps.length > 0
          ? msg.thoughtSteps
          : [{
              id: 'default-' + Date.now(),
              title: '分析中',
              description: '正在分析您的问题...',
              content: '',
              status: 'finish' as const,
              timestamp: new Date().toISOString(),
              role: 'assistant'
            }];
  
        return {
          ...msg,
          content: (
            <div>
              <ThoughtChain
                items={mapStepsToThoughtChainItems(messageThoughtSteps, mapThoughtStatus)}
                collapsible={true}
                size="small"
              />
              {msg.content && (
                <div style={{ marginTop: '12px' }}>
                  <GPTVis>{msg.content}</GPTVis>
                </div>
              )}
              {msg.files && msg.files.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  {msg.files.map((file, fileIndex) => (
                    <div key={fileIndex}>{renderFileContent(file)}</div>
                  ))}
                </div>
              )}
              {msg.dataPreview && (
                <div style={{ marginTop: '12px' }}>
                  <DataTable
                    sourceName={msg.dataPreview.source_name}
                    columns={msg.dataPreview.columns}
                    data={msg.dataPreview.data}
                    totalShown={msg.dataPreview.total_shown}
                  />
                </div>
              )}
              {renderReportButton(msg)}
            </div>
          )
        };
      }
      // 用户消息的处理 - 添加文件和数据源信息显示
      return {
        ...msg,
        content: (
          <div>
            {/* 用户消息内容 */}
            <div>{msg.content}</div>
            
            {/* 显示上传的文件信息 */}
            {msg.files && msg.files.length > 0 && (
              <div style={{ 
                marginTop: '8px', 
                padding: '6px 8px', 
                background: 'rgba(255, 255, 255, 0.1)', 
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'rgba(103, 102, 102, 0.8)' }}>
                  <FileOutlined style={{ fontSize: '12px' }} />
                  <span>已上传: {msg.files.map(file => file.name).join(', ')}</span>
                </div>
              </div>
            )}
            
            {/* 显示选择的数据源信息 */}
            {selectedDataSource && (
              <div style={{ 
                marginTop: '8px', 
                padding: '6px 8px', 
                background: 'rgba(255, 255, 255, 0.1)', 
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'rgba(105, 105, 105, 0.8)' }}>
                  <span>数据源: {selectedDataSource.name || selectedDataSource.description}</span>
                </div>
              </div>
            )}
          </div>
        )
      };
    }) || [];
  }, [messages, mapThoughtStatus, renderFileContent, selectedDataSource, renderReportButton]);

  const renderedThoughtChain = useMemo(() => {
    if (thoughtSteps.length === 0) return null;

    return {
      key: 'thinking',
      role: 'assistant',
      content: (
        <div className="thought-chain-container">
          <ThoughtChain
            items={mapStepsToThoughtChainItems(thoughtSteps, mapThoughtStatus)}
            collapsible={true}
            size="small"
          />
          {hasActiveThinking && (
            <div className="thinking-indicator" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
              <Spin size="small" />
              <span style={{ color: '#666', fontSize: '12px' }}>
                AI正在思考中...
              </span>
            </div>
          )}
        </div>
      ),
      classNames: {
        content: hasActiveThinking ? styles?.loadingMessage || '' : '',
      },
      typing: hasActiveThinking
    };
  }, [thoughtSteps, hasActiveThinking, mapThoughtStatus, styles?.loadingMessage]);

  const allBubbleItems = useMemo(() => {
    const bubbleItems = renderedMessages?.map((msg: any, index: number) => ({
      key: msg.id || index,
      role: msg.role,
      content: msg.content,
      classNames: {
        content: isLoading && msg.role === 'assistant' ? styles?.loadingMessage || '' : '',
      },
      typing: msg.role === 'assistant' && isLoading ? { step: 5, interval: 20, suffix: <>💗</> } : false,
    })) || [];
    
    if (renderedThoughtChain) {
      const lastMessage = messages?.[messages.length - 1];
      const isLastAssistantLoading = lastMessage?.role === 'assistant' && isLoading;
      
      if (!isLastAssistantLoading) {
        bubbleItems.push(renderedThoughtChain);
      }
    }
    
    return bubbleItems;
  }, [renderedMessages, renderedThoughtChain, isLoading, messages, styles?.loadingMessage]);
  const handleTopicClick = useCallback((info: any) => { onSubmit(info.data.description as string); }, [onSubmit]);
  const handleGuideClick = useCallback((info: any) => { onSubmit(info.data.description as string); }, [onSubmit]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    if (typeof window !== 'undefined') {
      Prism.highlightAll();
    }
  }, [messages]);

  return (
    <div className={`${styles?.chatList || ''} chat-list-container`}>
      {messages?.length || thoughtSteps.length > 0 ? (
        <Bubble.List
          items={allBubbleItems}
          className="bubble-list-responsive"
          roles={{
            assistant: {
              placement: 'start',
              avatar: (
                <Avatar 
                  size={32} 
                  style={{ backgroundColor: 'transparent' }}
                  icon={<img 
                    src={Robot} 
                    alt="custom-icon" 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                  />}
                />
              ),
              loadingRender: () => (
                <div className="loading-container">
                  <div className="loading-content">
                    <Spin size="small" />
                    <span style={{ color: '#666', fontSize: '12px' }}>
                      正在生成回复...
                    </span>
                  </div>
                </div>
              ),
              variant: "shadow",
            },
            user: { 
              placement: 'end',
              avatar: (
                <Avatar 
                  size={32} 
                  style={{ backgroundColor: '#52c41a' }}
                  icon={<UserOutlined />}
                />
              ),
              variant: "shadow",
            },
          }}
        />
      ) : (
        <div className="welcome-container">
          <Space
            direction="vertical"
            size={16}
            className={`${styles?.placeholder || ''} welcome-content`}
          >
            <Welcome
              variant="borderless"
              icon={<img src={logo} alt="Logo" style={{ width: 64, height: 64 }} />}
              title="你好，我是智能数据分析助手"
              description={selectedDataSource 
                ? `当前数据源: ${selectedDataSource.name || selectedDataSource.description}，开始分析您的数据吧~` 
                : "请先在左侧选择数据源，然后开始智能数据分析之旅~"}
            />
            
            {(dataPreview || filePreview) && (
              <div className="data-preview-container">
                {(() => {
                  const preview = filePreview || dataPreview;
                  const columns = preview?.columns || [];
                  const columnsNames = preview?.columns_names || [];
                  const data = preview?.data || [];
                  
                  // 确保有有效的列和数据才渲染
                  if (columns.length === 0 || data.length === 0) {
                    return (
                      <div style={{ padding: '16px', textAlign: 'center', color: '#666' }}>
                        暂无数据预览
                      </div>
                    );
                  }
                  
                  // 处理数据格式：确保data是对象数组格式
                  const processedData = data.map((row: any, rowIndex: number) => {
                    if (Array.isArray(row)) {
                      // 如果row是数组，转换为对象
                      const rowData: { [key: string]: any } = { key: rowIndex };
                      columns.forEach((col: any, colIndex: number) => {
                        const dataIndex = typeof col === 'string' ? col : col.dataIndex;
                        rowData[dataIndex] = row[colIndex];
                      });
                      return rowData;
                    } else if (typeof row === 'object' && row !== null) {
                      // 如果row已经是对象，直接使用（只添加key）
                      return { ...row, key: row.key ?? rowIndex };
                    } else {
                      // 其他情况，创建空对象
                      return { key: rowIndex };
                    }
                  });
                  
                  // 创建表格列配置，使用中文列名
                  const tableColumns = columns.map((col: any, index: number) => {
                    const dataIndex = typeof col === 'string' ? col : col.dataIndex;
                    const title = columnsNames[index] || dataIndex; // 优先使用中文列名
                    
                    return {
                      title,
                      dataIndex,
                      key: dataIndex,
                      ellipsis: true,
                      width: 150
                    };
                  });
                  
                  return (
                    <DataTable
                      sourceName={preview?.source_name || '未知数据源'}
                      columns={tableColumns}
                      data={processedData}
                      totalShown={preview?.total_shown || preview?.total_rows || data.length}
                      maxHeight={300}
                    />
                  );
                })()}
              </div>
            )}
            
            {!dataPreview && !filePreview && (
              <Flex gap={16} className="prompts-container">
                <Prompts
                  items={hotTopics?.children ? [hotTopics] : []}
                  styles={{
                    list: { height: '100%' },
                    item: {
                      flex: 1,
                      backgroundImage: 'linear-gradient(123deg, #e5f4ff 0%, #efe7ff 100%)',
                      borderRadius: 12,
                      border: 'none',
                    },
                    subItem: { padding: 0, background: 'transparent' },
                  }}
                  onItemClick={handleTopicClick}
                  className={styles?.chatPrompt || ''}
                />
            
                <Prompts
                  items={designGuide?.children ? [designGuide] : []}
                  styles={{
                    item: {
                      flex: 1,
                      backgroundImage: 'linear-gradient(123deg, #e5f4ff 0%, #efe7ff 100%)',
                      borderRadius: 12,
                      border: 'none',
                    },
                    subItem: { background: '#ffffffa6' },
                  }}
                  onItemClick={handleGuideClick}
                  className={styles?.chatPrompt || ''}
                />
              </Flex>
            )}
          </Space>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
});

ChatList.displayName = 'ChatList';

export default ChatList;
