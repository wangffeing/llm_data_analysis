import React, { useState, useEffect } from 'react';
import { Input, Button, Modal, message, Space } from 'antd';
import { KeyOutlined, EyeInvisibleOutlined, EyeTwoTone } from '@ant-design/icons';

interface AdminKeyManagerProps {
  visible: boolean;
  onClose: () => void;
}

const AdminKeyManager: React.FC<AdminKeyManagerProps> = ({ visible, onClose }) => {
  const [adminKey, setAdminKey] = useState<string>('');
  const [isKeySet, setIsKeySet] = useState<boolean>(false);

  useEffect(() => {
    // 检查是否已设置管理员密钥
    const savedKey = localStorage.getItem('adminKey');
    if (savedKey) {
      setAdminKey(savedKey);
      setIsKeySet(true);
    }
  }, [visible]); // 当Modal打开时重新检查

  const handleSaveKey = () => {
    if (!adminKey.trim()) {
      message.error('请输入管理员密钥');
      return;
    }
    
    localStorage.setItem('adminKey', adminKey);
    setIsKeySet(true);
    message.success('管理员密钥已保存');
  };

  const handleClearKey = () => {
    localStorage.removeItem('adminKey');
    setAdminKey('');
    setIsKeySet(false);
    message.success('管理员密钥已清除');
  };

  const handleCancel = () => {
    // 如果正在编辑但未保存，恢复原始状态
    const savedKey = localStorage.getItem('adminKey');
    if (savedKey) {
      setAdminKey(savedKey);
      setIsKeySet(true);
    } else {
      setAdminKey('');
      setIsKeySet(false);
    }
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
      width={400}
    >
      <div style={{ padding: '16px 0' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ marginBottom: 8, fontSize: '14px', color: '#666' }}>
            设置管理员密钥后，可以执行数据源和模板的增删改操作
          </div>
          
          <Input.Password
            placeholder="请输入管理员密钥"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
            disabled={isKeySet}
            onPressEnter={!isKeySet ? handleSaveKey : undefined}
          />
          
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            {!isKeySet ? (
              <Button type="primary" onClick={handleSaveKey} style={{ flex: 1 }}>
                保存密钥
              </Button>
            ) : (
              <>
                <Button type="default" onClick={handleClearKey}>
                  清除密钥
                </Button>
                <span style={{ color: '#52c41a', fontSize: '14px' }}>
                  ✓ 管理员权限已启用
                </span>
              </>
            )}
          </Space>
          
          {isKeySet && (
            <div style={{ 
              marginTop: 12, 
              padding: 8, 
              backgroundColor: '#f6ffed', 
              border: '1px solid #b7eb8f',
              borderRadius: 4,
              fontSize: '12px',
              color: '#389e0d'
            }}>
              <strong>权限说明：</strong>
              <br />• 可以创建、修改、删除数据源
              <br />• 可以创建、修改、删除自定义模板
              <br />• 其他用户只能查看和使用现有资源
            </div>
          )}
        </Space>
      </div>
    </Modal>
  );
};

export default AdminKeyManager;