import React, { useState, useEffect } from 'react';
import { Modal, Button, Spin, message, Tabs, Card, Typography, Space, Divider } from 'antd';
import { DownloadOutlined, PrinterOutlined, ReloadOutlined, CloseOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { apiService } from '../services/apiService';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface ReportViewerProps {
  visible: boolean;
  onClose: () => void;
  analysisResults: any;
  templateId?: string;
}

interface ReportData {
  success: boolean;
  report: string;
  metadata: {
    generated_at: string;
    analysis_type: string;
    data_range: string;
  };
}

const ReportViewer: React.FC<ReportViewerProps> = ({
  visible,
  onClose,
  analysisResults,
  templateId = 'telecom_analysis'
}) => {
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generateReport = async () => {
    if (!analysisResults) {
      message.error('分析结果数据不可用');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      // 从 analysisResults 中提取 session_id
      const sessionId = analysisResults.metadata?.session_id || 
                       analysisResults.session_id || 
                       localStorage.getItem('currentSessionId') || 
                       'default-session';

      // 构建请求数据，符合 ReportGenerationRequest 接口
      const requestData = {
        session_id: sessionId,  // 必需的 session_id
        template_id: templateId,
        config: {
          include_executive_summary: true,
          include_detailed_analysis: true,
          include_recommendations: true,
          language: 'zh-CN'
        }
      };

      console.log('发送报告生成请求:', requestData);
      
      const response = await apiService.generateIntelligentReport(requestData);
      
      if (response.success) {
        setReportData(response);
        message.success('报告生成成功！');
      } else {
        throw new Error('报告生成失败');
      }
    } catch (error: any) {
      console.error('生成报告失败:', error);
      const errorMessage = error.response?.data?.detail || error.message || '生成报告时发生未知错误';
      setError(errorMessage);
      message.error(`生成报告失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    generateReport();
  };

  const handleDownload = () => {
    if (!reportData?.report) return;
    
    const blob = new Blob([reportData.report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `智能分析报告_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success('报告下载成功！');
  };

  const handlePrint = () => {
    if (!reportData?.report) return;
    
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>智能分析报告</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20px; }
              h1, h2, h3 { color: #1890ff; }
              table { border-collapse: collapse; width: 100%; }
              th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
              th { background-color: #f2f2f2; }
            </style>
          </head>
          <body>
            ${reportData.report.replace(/\n/g, '<br>')}
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  useEffect(() => {
    if (visible && analysisResults) {
      generateReport();
    }
  }, [visible, analysisResults, templateId]);

  return (
    <Modal
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>智能分析报告</Title>
          {reportData?.metadata && (
            <Text type="secondary">
              {reportData.metadata.analysis_type} | {new Date(reportData.metadata.generated_at).toLocaleString()}
            </Text>
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width="90%"
      style={{ top: 20 }}
      footer={
        <Space>
          {error && (
            <Button 
              icon={<ReloadOutlined />} 
              onClick={handleRetry}
              type="primary"
            >
              重新生成
            </Button>
          )}
          {reportData && (
            <>
              <Button 
                icon={<DownloadOutlined />} 
                onClick={handleDownload}
              >
                下载报告
              </Button>
              <Button 
                icon={<PrinterOutlined />} 
                onClick={handlePrint}
              >
                打印报告
              </Button>
            </>
          )}
          <Button 
            icon={<CloseOutlined />} 
            onClick={onClose}
          >
            关闭
          </Button>
        </Space>
      }
    >
      {loading && (
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>正在生成智能分析报告，请稍候...</Text>
          </div>
        </div>
      )}

      {error && (
        <Card>
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Text type="danger">❌ {error}</Text>
            <div style={{ marginTop: 16 }}>
              <Button 
                type="primary" 
                icon={<ReloadOutlined />} 
                onClick={handleRetry}
              >
                重新生成报告
              </Button>
            </div>
          </div>
        </Card>
      )}

      {reportData && !loading && (
        <Tabs defaultActiveKey="report">
          <TabPane tab="报告内容" key="report">
            <Card>
              <div style={{ 
                maxHeight: '70vh', 
                overflow: 'auto',
                padding: '16px',
                backgroundColor: '#fafafa',
                border: '1px solid #d9d9d9',
                borderRadius: '6px'
              }}>
                <ReactMarkdown>{reportData.report}</ReactMarkdown>
              </div>
            </Card>
          </TabPane>
          
          <TabPane tab="报告信息" key="metadata">
            <Card title="报告元数据">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>生成时间：</Text>
                  <Text>{new Date(reportData.metadata.generated_at).toLocaleString()}</Text>
                </div>
                <Divider />
                <div>
                  <Text strong>分析类型：</Text>
                  <Text>{reportData.metadata.analysis_type}</Text>
                </div>
                <Divider />
                <div>
                  <Text strong>数据范围：</Text>
                  <Text>{reportData.metadata.data_range}</Text>
                </div>
                <Divider />
                <div>
                  <Text strong>模板ID：</Text>
                  <Text>{templateId}</Text>
                </div>
              </Space>
            </Card>
          </TabPane>
        </Tabs>
      )}
    </Modal>
  );
};

export default ReportViewer;