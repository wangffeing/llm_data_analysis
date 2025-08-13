import React, { useState, useEffect } from 'react';
import { Input, Button, Modal, Space, App, Alert } from 'antd';
import { KeyOutlined, EyeInvisibleOutlined, EyeTwoTone, LogoutOutlined } from '@ant-design/icons';
import { apiService } from '../services/apiService';

interface AdminKeyManagerProps {
  visible: boolean;
  onClose: () => void;
}

const AdminKeyManager: React.FC<AdminKeyManagerProps> = ({ visible, onClose }) => {
  const { message } = App.useApp();
  const [adminKey, setAdminKey] = useState<string>('');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [checkingStatus, setCheckingStatus] = useState<boolean>(true);

  // 检查登录状态
  const checkLoginStatus = async () => {
    try {
      setCheckingStatus(true);
      const status = await apiService.getAdminStatus();
      setIsLoggedIn(status.is_logged_in);
    } catch (error) {
      console.error('检查登录状态失败:', error);
      setIsLoggedIn(false);
    } finally {
      setCheckingStatus(false);
    }
  };

  useEffect(() => {
    if (visible) {
      checkLoginStatus();
      setAdminKey(''); // 清空输入框
    }
  }, [visible]);

  // 监听认证过期事件
  useEffect(() => {
    const handleAuthExpired = () => {
      setIsLoggedIn(false);
      message.warning('登录已过期，请重新登录');
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => {
      window.removeEventListener('auth:expired', handleAuthExpired);
    };
  }, [message]);

  const handleLogin = async () => {
    if (!adminKey.trim()) {
      message.error('请输入管理员密钥');
      return;
    }
    
    try {
      setLoading(true);
      const result = await apiService.adminLogin(adminKey);
      
      if (result.success) {
        setIsLoggedIn(true);
        setAdminKey(''); // 清空密钥输入
        message.success('管理员登录成功');
      }
    } catch (error: any) {
      console.error('登录失败:', error);
      
      if (error.message.includes('无效的管理员密钥')) {
        message.error({
          content: '管理员密钥无效！请检查密钥是否正确，或联系系统管理员获取正确的密钥。',
          duration: 5
        });
      } else if (error.message.includes('403')) {
        message.error('管理员密钥无效，请检查输入');
      } else {
        message.error('登录失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      setLoading(true);
      await apiService.adminLogout();
      setIsLoggedIn(false);
      message.success('已退出管理员权限');
    } catch (error) {
      console.error('登出失败:', error);
      message.error('登出失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setAdminKey('');
    onClose();
  };

  return (
    <Modal
      title={
        <Space>
          <KeyOutlined />
          管理员权限设置
        </Space>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={420}
    >
      <div style={{ padding: '16px 0' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {checkingStatus ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              检查登录状态中...
            </div>
          ) : (
            <>
              <Alert
                message="安全提示"
                description="请确保配置的数据源中不包含涉密、敏感信息。
                如果数据源中包含涉密、敏感信息，请及时删除。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              
              {!isLoggedIn ? (
                <>
                  <div style={{ marginBottom: 8, fontSize: '14px', color: '#666' }}>
                    请输入管理员密钥以获取管理员权限
                  </div>
                  
                  <Input.Password
                    placeholder="请输入管理员密钥"
                    value={adminKey}
                    onChange={(e) => setAdminKey(e.target.value)}
                    iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                    onPressEnter={handleLogin}
                    disabled={loading}
                  />
                  
                  <div style={{ marginTop: 8, color: '#666', fontSize: '12px' }}>
                    💡 提示：管理员密钥由系统管理员提供，登录状态将保持24小时
                  </div>
                  
                  <Button 
                    type="primary" 
                    onClick={handleLogin} 
                    loading={loading}
                    style={{ width: '100%' }}
                  >
                    安全登录
                  </Button>
                </>
              ) : (
                <>
                  <Alert
                    message="管理员权限已激活"
                    description="您当前拥有管理员权限，可以执行数据源和模板的增删改操作。"
                    type="success"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  
                  <div style={{ 
                    padding: 12, 
                    backgroundColor: '#f6ffed', 
                    border: '1px solid #b7eb8f',
                    borderRadius: 6,
                    fontSize: '12px',
                    color: '#389e0d',
                    marginBottom: 16
                  }}>
                    <strong>当前权限：</strong>
                    <br />• 可以创建、修改、删除数据源
                    <br />• 可以创建、修改、删除自定义模板
                    <br />• 可以上传和管理文件
                    <br />• 登录状态将在24小时后自动过期
                  </div>
                  
                  <Button 
                    type="default" 
                    icon={<LogoutOutlined />}
                    onClick={handleLogout} 
                    loading={loading}
                    style={{ width: '100%' }}
                    danger
                  >
                    退出管理员权限
                  </Button>
                </>
              )}
            </>
          )}
        </Space>
      </div>
    </Modal>
  );
};

export default AdminKeyManager;