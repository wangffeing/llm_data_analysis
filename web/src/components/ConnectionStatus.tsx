import React from 'react';
import { Badge, Tooltip } from 'antd';
import { WifiOutlined } from '@ant-design/icons';

// 改为显示SSE连接状态
interface ConnectionStatusProps {
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  isConnected: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ 
  connectionStatus, 
  isConnected 
}) => {
  const getStatus = () => {
    switch (connectionStatus) {
      case 'connected':
        return { status: 'success', text: '已连接' };
      case 'connecting':
        return { status: 'processing', text: '连接中' };
      case 'disconnected':
        return { status: 'default', text: '未连接' };
      case 'error':
        return { status: 'error', text: '连接错误' };
      default:
        return { status: 'default', text: '未知状态' };
    }
  };
  
  const { status, text } = getStatus();
  
  return (
    <Tooltip title={`连接状态: ${text}`}>
      <Badge status={status as any} />
      <WifiOutlined style={{ marginLeft: 4 }} />
      <span style={{ marginLeft: 4, fontSize: '12px' }}>{text}</span>
    </Tooltip>
  );
};

export default ConnectionStatus;