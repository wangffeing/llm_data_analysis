import React, { useState, useEffect } from 'react';
import { GPTVis } from '@antv/gpt-vis';
import { Typography, Alert, Spin } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface GPTVisChartProps {
  content: string;
  title?: string;
  loading?: boolean;
  showBorder?: boolean;
  style?: React.CSSProperties;
}

const GPTVisChart: React.FC<GPTVisChartProps> = ({ 
  content, 
  title, 
  loading = false,
  showBorder = true,
  style = {}
}) => {
  const [renderError, setRenderError] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(false);

  useEffect(() => {
    if (content) {
      setRenderError(null);
      setIsRendering(true);
      
      // 模拟渲染过程
      const timer = setTimeout(() => {
        setIsRendering(false);
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [content]);

  const containerStyle: React.CSSProperties = {
    border: showBorder ? '1px solid #e1e4e8' : 'none',
    borderRadius: '6px',
    padding: '12px',
    background: '#fff',
    margin: '8px 0',
    position: 'relative',
    ...style
  };

  const renderContent = () => {
    if (loading || isRendering) {
      return (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '200px' 
        }}>
          <Spin size="large" tip="正在渲染图表..." />
        </div>
      );
    }

    if (!content || content.trim() === '') {
      return (
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '200px',
          color: '#999',
          textAlign: 'center'
        }}>
          <FileTextOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <Text type="secondary">暂无图表内容</Text>
        </div>
      );
    }

    if (renderError) {
      return (
        <Alert
          message="图表渲染失败"
          description={renderError}
          type="error"
          showIcon
          style={{ margin: '16px 0' }}
        />
      );
    }

    try {
      return <GPTVis>{content}</GPTVis>;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      setRenderError(`GPT-Vis 渲染错误: ${errorMessage}`);
      return (
        <Alert
          message="图表渲染失败"
          description={`GPT-Vis 渲染错误: ${errorMessage}`}
          type="error"
          showIcon
          style={{ margin: '16px 0' }}
        />
      );
    }
  };

  return (
    <div style={containerStyle}>
      {title && (
        <div style={{ 
          marginBottom: '12px',
          borderBottom: '1px solid #f0f0f0',
          paddingBottom: '8px'
        }}>
          <Text strong style={{ fontSize: '14px' }}>{title}</Text>
        </div>
      )}
      
      <div style={{ minHeight: '100px' }}>
        {renderContent()}
      </div>
      
    </div>
  );
};

export default GPTVisChart;