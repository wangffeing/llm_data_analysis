import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Select,
  Switch,
  InputNumber,
  Button,
  Tabs,
  Card,
  Space,
  Tag,
  Divider,
  App
} from 'antd';
import { apiService } from '../services/apiService';
import type { TaskWeaverConfig, ConfigOptions } from '../types/appTypes';

const { Option } = Select;

interface ConfigModalProps {
  visible: boolean;
  onClose: () => void;
  sessionId: string;
}

const ConfigModal: React.FC<ConfigModalProps> = ({ visible, onClose, sessionId }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<TaskWeaverConfig | null>(null);
  const [options, setOptions] = useState<ConfigOptions>({ models: [], roles: [], modules: [], plugins: [] });
  const [selectedModules, setSelectedModules] = useState<string[]>([]);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [selectedPlugins, setSelectedPlugins] = useState<string[]>([]); // 新增插件状态

  useEffect(() => {
    if (visible) {
      loadConfig();
      loadOptions();
    }
  }, [visible]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await apiService.getSessionConfig(sessionId);
      if (response.success) {
        setConfig(response.config);
        setSelectedModules(response.config['code_interpreter.allowed_modules'] || []);
        setSelectedRoles(response.config['session.roles'] || []);
        setSelectedPlugins(response.config['code_generator.allowed_plugins'] || []); // 新增插件初始化
        form.setFieldsValue(response.config);
      }
    } catch (error) {
      console.error('加载配置失败:', error);
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const configUpdate = {
        ...values,
        'code_interpreter.allowed_modules': selectedModules,
        'session.roles': selectedRoles,
        'code_generator.allowed_plugins': selectedPlugins // 新增插件保存
      };

      const response = await apiService.updateSessionConfig(sessionId, configUpdate);
      if (response.success) {
        message.success('会话配置保存成功');
        onClose();
      } else {
        message.error('保存配置失败');
      }
    } catch (error) {
      console.error('保存配置失败:', error);
      message.error('保存配置失败');
    }
  };

  const handleQuickConfig = async (configType: string) => {
    try {
      let roles: string[] = [];
      if (configType === 'code_only') {
        roles = ['code_interpreter'];
      } else if (configType === 'full_mode') {
        roles = ['planner', 'code_interpreter', 'recepta'];
      }

      const response = await apiService.updateSessionRoles(sessionId, roles);
      if (response.success) {
        setSelectedRoles(roles);
        form.setFieldValue('session.roles', roles);
        message.success('模式切换成功');
      }
    } catch (error) {
      console.error('切换模式失败:', error);
      message.error('切换模式失败');
    }
  };

  const loadOptions = async () => {
    try {
      const [modelsRes, rolesRes, modulesRes, pluginsRes] = await Promise.all([
        apiService.getAvailableModels(),
        apiService.getAvailableRoles(),
        apiService.getAvailableModules(),
        apiService.getAvailablePlugins() // 新增插件选项加载
      ]);
      
      setOptions({
        models: modelsRes.success ? modelsRes.models : [],
        roles: rolesRes.success ? rolesRes.roles : [],
        modules: modulesRes.success ? modulesRes.modules : [],
        plugins: pluginsRes.success ? pluginsRes.plugins : [] // 新增插件选项
      });
    } catch (error) {
      message.error('加载选项失败');
    }
  };

  // 使用新的Tabs items API
  const tabItems = [
    {
      key: '1',
      label: '快速配置',
      children: (
        <Card title="工作模式">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              type="primary"
              onClick={() => handleQuickConfig('full_mode')}
            >
              完整模式（规划器+代码解释器+接收器）
            </Button>
            <Button 
              onClick={() => handleQuickConfig('code_only')}
              style={{ marginRight: 8 }}
            >
              纯代码解释器模式（快速执行 | 数据库取数）
            </Button>

            <div style={{ marginTop: 16 }}>
              <strong>当前角色：</strong>
              {selectedRoles.map(role => (
                <Tag key={role} color="blue" style={{ margin: '2px' }}>
                  {role}
                </Tag>
              ))}
            </div>
          </Space>
        </Card>
      )
    },
    {
      key: '2',
      label: 'LLM配置',
      children: (
        <Form form={form} layout="vertical">
          <Form.Item label="模型" name="llm.model">
            <Select placeholder="选择模型">
              {options.models.map(model => (
                <Option key={model} value={model}>{model}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item label="API类型" name="llm.api_type">
            <Select placeholder="选择API类型">
              <Option value="lingyun">LingYun</Option>
              <Option value="qwen">Qwen</Option>
            </Select>
          </Form.Item>
        </Form>
      )
    },
    {
      key: '3',
      label: '会话配置',
      children: (
        <Form form={form} layout="vertical">
          <Form.Item label="会话角色">
            <Select
              mode="multiple"
              placeholder="选择会话角色"
              value={selectedRoles}
              onChange={setSelectedRoles}
            >
              {options.roles.map(role => (
                <Option key={role} value={role}>{role}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item label="最大对话轮数" name="session.max_internal_chat_round_num">
            <InputNumber min={1} max={100} />
          </Form.Item>
        </Form>
      )
    },
    {
      key: '4',
      label: '代码解释器',
      children: (
        <Form form={form} layout="vertical">
          <Form.Item label="允许的Python模块">
            <Select
              mode="multiple"
              placeholder="选择允许的模块"
              value={selectedModules}
              onChange={setSelectedModules}
              style={{ width: '100%' }}
            >
              {options.modules.map(module => (
                <Option key={module} value={module}>{module}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item label="代码验证" name="code_interpreter.code_verification_on" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      )
    },
    {
      key: '5',
      label: '插件配置', // 新增插件配置标签页
      children: (
        <Form form={form} layout="vertical">
          <Form.Item label="允许的插件">
            <Select
              mode="multiple"
              placeholder="选择允许的插件"
              value={selectedPlugins}
              onChange={setSelectedPlugins}
              style={{ width: '100%' }}
            >
              {options.plugins.map(plugin => (
                <Option key={plugin} value={plugin}>{plugin}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <div style={{ marginBottom: 16 }}>
            <strong>当前插件：</strong>
            {selectedPlugins.length === 0 ? (
              <Tag color="default">无插件</Tag>
            ) : (
              selectedPlugins.map(plugin => (
                <Tag key={plugin} color="green" style={{ margin: '2px' }}>
                  {plugin}
                </Tag>
              ))
            )}
          </div>

        </Form>
      )
    },
    {
      key: '6', // 原来的高级配置改为key 6
      label: '高级配置',
      children: (
        <Form form={form} layout="vertical">
          <Form.Item label="规划器提示压缩" name="planner.prompt_compression" valuePropName="checked">
            <Switch />
          </Form.Item>
          
          <Form.Item label="代码生成器提示压缩" name="code_generator.prompt_compression" valuePropName="checked">
            <Switch />
          </Form.Item>
          
          <Form.Item label="日志级别" name="logging.log_level">
            <Select>
              <Option value="DEBUG">DEBUG</Option>
              <Option value="INFO">INFO</Option>
              <Option value="WARNING">WARNING</Option>
              <Option value="ERROR">ERROR</Option>
            </Select>
          </Form.Item>
        </Form>
      )
    }
  ];

  return (
    <Modal
      title="配置管理"
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="save" type="primary" loading={loading} onClick={handleSave}>
          保存配置
        </Button>
      ]}
    >
      <Tabs defaultActiveKey="1" items={tabItems} />
    </Modal>
  );
};

export default ConfigModal;