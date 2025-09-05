import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Card, Button, Tag, Space, Modal, 
  Drawer, Typography, Divider, Row, Col, Steps, Badge,
  List, Collapse
} from 'antd';
import { 
  FileTextOutlined, SettingOutlined, EyeOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined
} from '@ant-design/icons';
import { apiService } from '../services/apiService';
import { useTemplateManagement } from '../hooks/useTemplateManagement';
import { Template } from '../types/template';
import TemplateConfigModal from './TemplateConfigModal';
import ReactMarkdown from 'react-markdown';

const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

interface TemplateSelectorProps {
  visible: boolean;
  onClose: () => void;
  onSelect: (templateId: string, prompt: string) => void;
  dataColumns?: string[];
}

const TemplateCard = React.memo<{
  template: Template;
  compatibility: any;
  isSelected: boolean;
  onSelect: (template: Template) => void;
  onView: (template: Template) => void;
}>(({ template, compatibility, isSelected, onSelect, onView }) => {
  const handleCardClick = useCallback(() => {
    onSelect(template);
  }, [template, onSelect]);

  const handleViewClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onView(template);
  }, [template, onView]);

  return (
    <Card
      hoverable
      className={isSelected ? 'selected-template' : ''}
      onClick={handleCardClick}
      style={{
        border: isSelected ? '2px solid #1890ff' : '1px solid #d9d9d9',
        height: '100%'
      }}
      actions={[
        <Button
          key="view"
          type="text"
          icon={<EyeOutlined />}
          onClick={handleViewClick}
        >
          查看详情
        </Button>
      ]}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
            <FileTextOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            <Title level={5} style={{ margin: 0 }}>
              {template.template_metadata.name}
            </Title>
            {compatibility.compatible ? (
              <Tag color="green" style={{ marginLeft: 8 }}>
                <CheckCircleOutlined /> 兼容
              </Tag>
            ) : (
              <Tag color="orange" style={{ marginLeft: 8 }}>
                <ExclamationCircleOutlined /> 需调整
              </Tag>
            )}
          </div>
          
          <Paragraph 
            style={{ color: '#666', marginBottom: 12, fontSize: '12px' }}
            ellipsis={{ rows: 2 }}
          >
            {template.template_metadata.summary}
          </Paragraph>
          
          <Space wrap>
            <Tag color="blue">
              {template.data_schema.required_columns.length} 必需列
            </Tag>
            <Tag color="cyan">
              {template.data_schema.optional_columns.length} 可选列
            </Tag>
            <Tag color="green">
              {template.execution_plan.steps.length} 步骤
            </Tag>
          </Space>
          
          {!compatibility.compatible && (
            <div style={{ marginTop: 8 }}>
              <div style={{ 
                padding: '8px', 
                backgroundColor: '#f6f9ff', 
                borderRadius: '4px', 
                fontSize: '12px', 
                marginBottom: '8px' 
              }}>
                <Text type="warning">缺少: {compatibility.missingRequired.join(', ')}</Text>
              </div>
            </div>
          )}
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <Badge 
            count={Math.round(compatibility.compatibilityScore * 100)} 
            style={{ 
              backgroundColor: compatibility.compatible ? '#52c41a' : '#faad14',
              fontSize: '12px'
            }}
          />
          <div style={{ fontSize: '10px', color: '#999', marginTop: 4 }}>匹配度</div>
        </div>
      </div>
    </Card>
  );
});

const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  visible,
  onClose,
  onSelect,
  dataColumns = []
}) => {
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(false);
  
  // 模板管理相关状态
  const [manageModalVisible, setManageModalVisible] = useState(false);
  const [viewDrawerVisible, setViewDrawerVisible] = useState(false);
  const [viewingTemplate, setViewingTemplate] = useState<Template | null>(null);
  
  const { templates, loadTemplates } = useTemplateManagement();

  // 🔧 优化2: 修复 useEffect 依赖问题，避免无限循环
  useEffect(() => {
    if (visible) {
      loadTemplates();
    }
  }, [visible]); // 只依赖 visible，移除 loadTemplates 依赖

  // 🔧 优化3: 使用 useMemo 优化兼容性检查计算
  const checkColumnCompatibility = useCallback((template: Template) => {
    const requiredColumns = template.data_schema.required_columns.map(col => col.name);
    const optionalColumns = template.data_schema.optional_columns.map(col => col.name);
    
    const missingRequired = requiredColumns.filter(
      col => !dataColumns.includes(col)
    );
    const availableOptional = optionalColumns.filter(
      col => dataColumns.includes(col)
    );
    
    // 修复：避免除零错误
    const totalColumns = requiredColumns.length + optionalColumns.length;
    const compatibilityScore = totalColumns > 0 
      ? ((requiredColumns.length - missingRequired.length) + availableOptional.length) / totalColumns
      : 0;
    
    return {
      compatible: missingRequired.length === 0,
      missingRequired,
      availableOptional,
      compatibilityScore: Math.max(0, Math.min(1, compatibilityScore)) // 确保在0-1范围内
    };
  }, [dataColumns]);

  // 🔧 优化4: 使用 useMemo 缓存模板兼容性计算结果
  const templatesWithCompatibility = useMemo(() => {
    return templates.map(template => ({
      template,
      compatibility: checkColumnCompatibility(template)
    }));
  }, [templates, checkColumnCompatibility]);

  // 🔧 优化5: 使用 useCallback 优化事件处理函数
  const handleTemplateSelect = useCallback(async () => {
    if (!selectedTemplate) return;
    
    try {
      setLoading(true);
      const response = await apiService.generateTemplatePrompt(
        selectedTemplate.template_metadata.id,
        dataColumns
      );
      onSelect(selectedTemplate.template_metadata.id, response.prompt);
      onClose();
    } catch (error) {
      console.error('生成模板提示失败:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedTemplate, dataColumns, onSelect, onClose]);

  const handleViewTemplate = useCallback((template: Template) => {
    setViewingTemplate(template);
    setViewDrawerVisible(true);
  }, []);

  const handleManageModalClose = useCallback(() => {
    setManageModalVisible(false);
    loadTemplates(); // 重新加载模板列表
  }, [loadTemplates]);

  const handleTemplateCardSelect = useCallback((template: Template) => {
    setSelectedTemplate(template);
  }, []);

  // 🔧 优化6: 使用 useMemo 缓存折叠面板数据
  const getCollapseItems = useMemo(() => {
    return (template: Template) => [
      {
        key: '1',
        label: '数据架构',
        children: (
          <div>
            <Title level={5}>必需列</Title>
            <List
              size="small"
              dataSource={template.data_schema.required_columns}
              renderItem={(col) => (
                <List.Item>
                  <List.Item.Meta
                    title={<Text strong>{col.name}</Text>}
                    description={`类型: ${col.type} | ${col.description}`}
                  />
                </List.Item>
              )}
            />
            
            <Title level={5} style={{ marginTop: 16 }}>可选列</Title>
            <List
              size="small"
              dataSource={template.data_schema.optional_columns}
              renderItem={(col) => (
                <List.Item>
                  <List.Item.Meta
                    title={<Text>{col.name}</Text>}
                    description={`类型: ${col.type} | ${col.description}`}
                  />
                </List.Item>
              )}
            />
          </div>
        )
      },
      {
        key: '2',
        label: '执行计划',
        children: (
          <div>
            <Title level={5}>分析目标</Title>
            <Paragraph>{template.execution_plan.analysis_goal}</Paragraph>
            
            <Title level={5}>执行步骤</Title>
            <Steps direction="vertical" size="small">
              {template.execution_plan.steps.map((step, index) => (
                <Step
                  key={index}
                  title={`步骤 ${index + 1}`}
                  description={
                    <div>
                      <Paragraph style={{ fontSize: '12px' }}>{step.prompt}</Paragraph>
                      {step.save_to_variable && (
                        <Text type="secondary" style={{ fontSize: '11px' }}>
                          保存到: {step.save_to_variable}
                        </Text>
                      )}
                    </div>
                  }
                />
              ))}
            </Steps>
          </div>
        )
      },
      {
        key: '3',
        label: '输出规范',
        children: (
          <div>
            <Title level={5}>洞察模板</Title>
            <div style={{ 
              backgroundColor: '#f9f9f9', 
              padding: '8px', 
              marginTop: '4px',
              borderRadius: '4px',
            }}>
              <ReactMarkdown>
                {typeof template.output_specification.insights_template === 'string' 
                  ? template.output_specification.insights_template 
                  : Array.isArray(template.output_specification.insights_template) 
                    ? template.output_specification.insights_template.join('\n') 
                    : '无模板内容'}
              </ReactMarkdown>
            </div>
            
            <Title level={5} style={{ marginTop: 16 }}>输出文件</Title>
            <List
              size="small"
              dataSource={Array.isArray(template.output_specification.files) 
                ? template.output_specification.files 
                : []
              }
              renderItem={(item) => (
                <List.Item>
                  {typeof item === 'string' ? (
                    <Text>{item}</Text>
                  ) : (
                    <div>
                      <Text strong>{item.title || item.type}</Text>
                      {item.tool && (
                        <Tag color="blue" style={{ marginLeft: 8 }}>
                          {item.tool}
                        </Tag>
                      )}
                      {item.source_variable && (
                        <div style={{ fontSize: '11px', color: '#666' }}>
                          数据源: {item.source_variable}
                        </div>
                      )}
                    </div>
                  )}
                </List.Item>
              )}
            />
          </div>
        )
      }
    ];
  }, []);

  return (
    <>
      <Modal
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>选择分析模板</span>
            <Space>
              <Button 
                icon={<SettingOutlined />} 
                onClick={() => setManageModalVisible(true)}
                type="text"
              >
                管理模板
              </Button>
            </Space>
          </div>
        }
        open={visible}
        onCancel={onClose}
        width={1000}
        footer={[
          <Button key="cancel" onClick={onClose}>
            取消
          </Button>,
          <Button
            key="select"
            type="primary"
            disabled={!selectedTemplate}
            loading={loading}
            onClick={handleTemplateSelect}
          >
            使用此模板
          </Button>
        ]}
      >
        <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          <Row gutter={[16, 16]}>
            {templatesWithCompatibility.map(({ template, compatibility }) => {
              const isSelected = selectedTemplate?.template_metadata.id === template.template_metadata.id;
              
              return (
                <Col span={12} key={template.template_metadata.id}>
                  <TemplateCard
                    template={template}
                    compatibility={compatibility}
                    isSelected={isSelected}
                    onSelect={handleTemplateCardSelect}
                    onView={handleViewTemplate}
                  />
                </Col>
              );
            })}
          </Row>
        </div>
      </Modal>

      {/* 模板详情查看抽屉 */}
      <Drawer
        title="模板详情"
        open={viewDrawerVisible}
        onClose={() => {
          setViewDrawerVisible(false);
          setViewingTemplate(null);
        }}
        width={800}
      >
        {viewingTemplate && (
          <div>
            <Title level={4}>{viewingTemplate.template_metadata.name}</Title>
            <Paragraph>{viewingTemplate.template_metadata.summary}</Paragraph>
            
            <Divider />
            
            <Collapse 
              defaultActiveKey={['1', '2', '3']}
              items={getCollapseItems(viewingTemplate)}
            />
          </div>
        )}
      </Drawer>

      {/* 模板配置管理模态框 */}
      <TemplateConfigModal
        visible={manageModalVisible}
        onClose={handleManageModalClose}
      />
    </>
  );
};

export default TemplateSelector;