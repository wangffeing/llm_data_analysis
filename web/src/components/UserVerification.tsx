import React, { useState } from 'react';
import { Modal, Form, Input, Button, Alert, Typography, Space } from 'antd';
import { UserOutlined, KeyOutlined, LoginOutlined } from '@ant-design/icons';
import { apiService } from '../services/apiService';

const { Title, Text } = Typography;

interface UserVerificationProps {
  onVerificationSuccess: (userInfo: any) => void;
  visible?: boolean;
  onCancel?: () => void;
}

interface VerificationState {
  isVerifying: boolean;
  error: string | null;
}

const UserVerification: React.FC<UserVerificationProps> = ({ 
  onVerificationSuccess, 
  visible = true, 
  onCancel 
}) => {
  const [form] = Form.useForm();
  const [verificationState, setVerificationState] = useState<VerificationState>({
    isVerifying: false,
    error: null
  });

  const handleVerify = async (values: { appCode: string; token: string }) => {
    try {
      setVerificationState({ isVerifying: true, error: null });
      
      const response = await apiService.verifyUser(values.appCode.trim(), values.token.trim());
      
      if (response.success) {
        // 保存用户信息到 sessionStorage
        const userInfo = {
          user_id: response.user_id,
          username: response.username,
          app_code: values.appCode.trim(),
          permissions: response.permissions || [],
          expires_at: response.expires_at
        };
        
        sessionStorage.setItem('user_info', JSON.stringify(userInfo));
        sessionStorage.setItem('app_code', values.appCode.trim());
        sessionStorage.setItem('user_token', values.token.trim());
        
        onVerificationSuccess(userInfo);
      } else {
        setVerificationState({
          isVerifying: false,
          error: response.message || '验证失败'
        });
      }
    } catch (error) {
      let errorMessage = '验证失败，请重试';
      
      if (error instanceof Error) {
        if (error.message.includes('timeout')) {
          errorMessage = '验证超时，请检查网络连接';
        } else if (error.message.includes('Network') || error.message.includes('网络')) {
          errorMessage = '网络连接失败，请检查网络';
        } else if (error.message.includes('401') || error.message.includes('权限')) {
          errorMessage = '应用代码或令牌无效';
        } else if (error.message.includes('500')) {
          errorMessage = '服务器错误，请稍后重试';
        } else {
          errorMessage = error.message;
        }
      }
      
      setVerificationState({
        isVerifying: false,
        error: errorMessage
      });
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setVerificationState({ isVerifying: false, error: null });
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <Modal
      title={
        <Space>
          <LoginOutlined />
          <span>用户验证</span>
        </Space>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={480}
      centered
      maskClosable={false}
      destroyOnClose
    >
      <div style={{ padding: '20px 0' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Text type="secondary">请输入您的应用代码和访问令牌</Text>
        </div>
        
        {verificationState.error && (
          <Alert
            message={verificationState.error}
            type="error"
            showIcon
            style={{ marginBottom: '16px' }}
          />
        )}
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleVerify}
          autoComplete="off"
        >
          <Form.Item
            label="应用代码"
            name="appCode"
            rules={[
              { required: true, message: '请输入应用代码' },
              { whitespace: true, message: '应用代码不能为空' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入应用代码"
              size="large"
              disabled={verificationState.isVerifying}
            />
          </Form.Item>
          
          <Form.Item
            label="访问令牌"
            name="token"
            rules={[
              { required: true, message: '请输入访问令牌' },
              { whitespace: true, message: '访问令牌不能为空' }
            ]}
          >
            <Input.Password
              prefix={<KeyOutlined />}
              placeholder="请输入访问令牌"
              size="large"
              disabled={verificationState.isVerifying}
            />
          </Form.Item>
          
          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              {onCancel && (
                <Button
                  onClick={handleCancel}
                  disabled={verificationState.isVerifying}
                  size="large"
                >
                  取消
                </Button>
              )}
              <Button
                type="primary"
                htmlType="submit"
                loading={verificationState.isVerifying}
                size="large"
                style={{ minWidth: '120px' }}
              >
                {verificationState.isVerifying ? '验证中...' : '验证'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
        
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            请联系管理员获取您的应用代码和访问令牌
          </Text>
        </div>
      </div>
    </Modal>
  );
};

export default UserVerification;
