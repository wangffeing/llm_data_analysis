import React, { useState, useEffect } from 'react';
import { Card, Button, Spin, Tabs, Space, Tag, Progress, Divider } from 'antd';
import { DownloadOutlined, PrinterOutlined, ShareAltOutlined, FileTextOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { apiService } from '../services/apiService';

interface ReportData {
  success: boolean;
  report: string;
  metadata: {
    generated_at: string;
    analysis_type: string;
    data_range: string;
  };
}

interface ReportViewerProps {
  analysisResults: any;
  templateId?: string;
  visible: boolean;
  onClose: () => void;
}

const ReportViewer: React.FC<ReportViewerProps> = ({
  analysisResults,
  templateId,
  visible,
  onClose
}) => {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('report');

  useEffect(() => {
    if (visible && analysisResults) {
      generateReport();
    }
  }, [visible, analysisResults]);

  const generateReport = async () => {
    try {
      setLoading(true);
      const response = await apiService.generateIntelligentReport({
        analysis_results: analysisResults,
        template_id: templateId,
        config: {
          include_executive_summary: true,
          include_detailed_analysis: true,
          include_recommendations: true,
          language: 'zh-CN'
        }
      });
      setReportData(response);
    } catch (error) {
      console.error('生成报告失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!reportData) return;
    
    const blob = new Blob([reportData.report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `分析报告_${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const printReport = () => {
    window.print();
  };

  if (!visible) return null;

  return (
    <div style={{ 
      position: 'fixed', 
      top: 0, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.5)', 
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Card
        style={{ 
          width: '90vw', 
          height: '90vh', 
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              <FileTextOutlined style={{ marginRight: 8 }} />
              智能分析报告
            </span>
            <Space>
              <Button icon={<DownloadOutlined />} onClick={downloadReport}>
                下载报告
              </Button>
              <Button icon={<PrinterOutlined />} onClick={printReport}>
                打印报告
              </Button>
              <Button onClick={onClose}>
                关闭
              </Button>
            </Space>
          </div>
        }
      >
        {loading ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '400px',
            flexDirection: 'column'
          }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>正在生成智能报告...</div>
            <Progress percent={75} style={{ width: 300, marginTop: 16 }} />
          </div>
        ) : reportData ? (
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            style={{ flex: 1, overflow: 'hidden' }}
            items={[
              {
                key: 'report',
                label: '完整报告',
                children: (
                  <div style={{ 
                    height: 'calc(90vh - 200px)', 
                    overflow: 'auto',
                    padding: '20px',
                    backgroundColor: '#fafafa'
                  }}>
                    <ReactMarkdown>{reportData.report}</ReactMarkdown>
                  </div>
                )
              },
              {
                key: 'metadata',
                label: '报告信息',
                children: (
                  <div style={{ padding: '20px' }}>
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                      <Card size="small" title="基本信息">
                        <p><strong>生成时间:</strong> {reportData.metadata.generated_at}</p>
                        <p><strong>分析类型:</strong> {reportData.metadata.analysis_type}</p>
                        <p><strong>数据范围:</strong> {reportData.metadata.data_range}</p>
                      </Card>
                      
                      <Card size="small" title="报告统计">
                        <p><strong>字符数:</strong> {reportData.report.length.toLocaleString()}</p>
                        <p><strong>段落数:</strong> {reportData.report.split('\n\n').length}</p>
                        <p><strong>图表数:</strong> {(reportData.report.match(/!\[.*?\]/g) || []).length}</p>
                      </Card>
                    </Space>
                  </div>
                )
              }
            ]}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p>暂无报告数据</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ReportViewer;