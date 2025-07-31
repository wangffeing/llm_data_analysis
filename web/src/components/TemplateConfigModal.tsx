import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Modal,
  Form,
  Input,
  Button,
  Space,
  Card,
  List,
  Tag,
  Divider,
  App,
  Row,
  Col,
  Typography,
  Collapse,
  Select,
  Tooltip
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { useTemplateManagement } from '../hooks/useTemplateManagement';
import { Template } from '../types/template';
import ReactMarkdown from 'react-markdown';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;
const { Option } = Select;

interface TemplateConfigModalProps {
  visible: boolean;
  onClose: () => void;
}

interface ExecutionStepForm {
  prompt: string;
  save_to_variable?: string;
}

interface OutputFileForm {
  type: string;
  title: string;
  source_variable: string;
  tool: string;
}

// 🔧 优化1: 将模板列表项组件提取并使用 React.memo
const TemplateListItem = React.memo<{
  template: Template;
  onView: (template: Template) => void;
  onEdit: (template: Template) => void;
  onDelete: (templateId: string) => void;
}>(({ template, onView, onEdit, onDelete }) => {
  const handleView = useCallback(() => {
    onView(template);
  }, [template, onView]);

  const handleEdit = useCallback(() => {
    onEdit(template);
  }, [template, onEdit]);

  const handleDelete = useCallback(() => {
    onDelete(template.template_metadata.id);
  }, [template.template_metadata.id, onDelete]);

  return (
    <List.Item
      actions={[
        <Button
          key="view"
          type="text"
          icon={<EyeOutlined />}
          onClick={handleView}
        />,
        <Button
          key="edit"
          type="text"
          icon={<EditOutlined />}
          onClick={handleEdit}
        />,
        <Button
          key="delete"
          type="text"
          icon={<DeleteOutlined />}
          danger
          onClick={handleDelete}
        />
      ]}
    >
      <List.Item.Meta
        title={template.template_metadata.name}
        description={
          <div>
            <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0, fontSize: '12px' }}>
              {template.template_metadata.summary}
            </Paragraph>
            <Space size="small" style={{ marginTop: 4 }}>
              <Tag color="blue">
                {template.data_schema.required_columns.length} 必需
              </Tag>
              <Tag color="cyan">
                {template.data_schema.optional_columns.length} 可选
              </Tag>
              <Tag color="green">
                {template.execution_plan.steps.length} 步骤
              </Tag>
            </Space>
          </div>
        }
      />
    </List.Item>
  );
});

const TemplateConfigModal: React.FC<TemplateConfigModalProps> = ({
  visible,
  onClose
}) => {
  const [form] = Form.useForm();
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [viewingTemplate, setViewingTemplate] = useState<Template | null>(null);
  const { message } = App.useApp();
  
  const {
    templates,
    loading,
    loadTemplates,
    addTemplate,
    updateTemplate,
    deleteTemplate
  } = useTemplateManagement();

  // 🔧 优化2: 修复 useEffect 依赖问题
  useEffect(() => {
    if (visible) {
      loadTemplates();
    }
  }, [visible]); // 只依赖 visible

  // 🔧 优化3: 使用 useCallback 优化表单处理函数
  const handleAddTemplate = useCallback(async (values: any) => {
    try {
      const templateConfig = {
        template_metadata: {
          id: values.template_id,
          name: values.name,
          summary: values.summary
        },
        data_schema: {
          required_columns: values.required_columns?.split('\n').filter(Boolean).map((line: string) => {
            const [name, type, description] = line.split('|').map(s => s.trim());
            return { name: name || '', type: type || 'string', description: description || '' };
          }) || [],
          optional_columns: values.optional_columns?.split('\n').filter(Boolean).map((line: string) => {
            const [name, type, description] = line.split('|').map(s => s.trim());
            return { name: name || '', type: type || 'string', description: description || '' };
          }) || []
        },
        execution_plan: {
          analysis_goal: values.analysis_goal,
          steps: values.execution_steps || []
        },
        output_specification: {
          insights_template: values.insights_template || '',
          files: values.output_files || []
        }
      };

      if (editingTemplate) {
        await updateTemplate(editingTemplate.template_metadata.id, templateConfig);
      } else {
        await addTemplate(values.template_id, templateConfig);
      }
      
      form.resetFields();
      setEditingTemplate(null);
    } catch (error) {
      // Error handling is done in the hook
    }
  }, [editingTemplate, form, updateTemplate, addTemplate]);

  const handleEditTemplate = useCallback((template: Template) => {
    setEditingTemplate(template);
    form.setFieldsValue({
      template_id: template.template_metadata.id,
      name: template.template_metadata.name,
      summary: template.template_metadata.summary,
      analysis_goal: template.execution_plan.analysis_goal,
      required_columns: template.data_schema.required_columns
        .map(col => `${col.name}|${col.type}|${col.description}`).join('\n'),
      optional_columns: template.data_schema.optional_columns
        .map(col => `${col.name}|${col.type}|${col.description}`).join('\n'),
      execution_steps: template.execution_plan.steps,
      insights_template: typeof template.output_specification.insights_template === 'string'
        ? template.output_specification.insights_template
        : Array.isArray(template.output_specification.insights_template)
          ? template.output_specification.insights_template.join('\n')
          : '',
      output_files: Array.isArray(template.output_specification.files)
        ? template.output_specification.files.map(file => 
            typeof file === 'string' 
              ? { type: '', title: file, source_variable: '', tool: '' }
              : file
          )
        : []
    });
  }, [form]);

  const handleDeleteTemplate = useCallback(async (templateId: string) => {
    try {
      await deleteTemplate(templateId);
    } catch (error) {
      // Error handling is done in the hook
    }
  }, [deleteTemplate]);

  const handleViewTemplate = useCallback((template: Template) => {
    setViewingTemplate(template);
  }, []);

  // 🔧 优化4: 使用 useMemo 缓存折叠面板数据
  const getCollapseItems = useMemo(() => {
    return (template: Template) => [
      {
        key: '1',
        label: '数据架构',
        children: (
          <div style={{ fontSize: '12px' }}>
            <strong>必需列:</strong>
            {template.data_schema.required_columns.map(col => (
              <div key={col.name} style={{ marginLeft: 8, marginBottom: 4 }}>
                • {col.name} ({col.type}): {col.description}
              </div>
            ))}
            <strong style={{ marginTop: 8, display: 'block' }}>可选列:</strong>
            {template.data_schema.optional_columns.map(col => (
              <div key={col.name} style={{ marginLeft: 8, marginBottom: 4 }}>
                • {col.name} ({col.type}): {col.description}
              </div>
            ))}
          </div>
        )
      },
      {
        key: '2',
        label: '执行计划',
        children: (
          <div style={{ fontSize: '12px' }}>
            <strong>目标:</strong> {template.execution_plan.analysis_goal}
            <strong style={{ marginTop: 8, display: 'block' }}>步骤:</strong>
            {template.execution_plan.steps.map((step, index) => (
              <div key={index} style={{ marginLeft: 8, marginBottom: 4 }}>
                {index + 1}. {step.prompt}
                {step.save_to_variable && (
                  <div style={{ fontSize: '11px', color: '#666', marginLeft: 16 }}>
                    保存到: {step.save_to_variable}
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      },
      {
        key: '3',
        label: '输出规范',
        children: (
          <div style={{ fontSize: '12px' }}>
            <strong>洞察模板:</strong>
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

            <strong style={{ marginTop: 8, display: 'block' }}>输出文件:</strong>
            {Array.isArray(template.output_specification.files) && 
              template.output_specification.files.map((file, index) => (
                <div key={index} style={{ marginLeft: 8, marginBottom: 4 }}>
                  {typeof file === 'string' ? (
                    `• ${file}`
                  ) : (
                    <div>
                      • <strong>{file.title || file.type}</strong>
                      {file.tool && (
                        <Tag color="blue" style={{ marginLeft: 8, fontSize: '10px' }}>
                          {file.tool}
                        </Tag>
                      )}
                      {file.source_variable && (
                        <div style={{ fontSize: '10px', color: '#666', marginLeft: 16 }}>
                          来源: {file.source_variable}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            }
          </div>
        )
      }
    ];
  }, []);

  // 🔧 优化5: 使用 useMemo 缓存当前查看模板的折叠面板数据
  const currentViewingCollapseItems = useMemo(() => {
    if (!viewingTemplate) return [];
    return getCollapseItems(viewingTemplate);
  }, [viewingTemplate, getCollapseItems]);

  return (
    <Modal
      title="模板配置管理"
      open={visible}
      onCancel={onClose}
      width="95%"
      style={{ top: 20 }}
      footer={null}
      destroyOnClose
    >
      <Row gutter={16} style={{ height: '80vh' }}>
        {/* 模板列表 */}
        <Col span={8}>
          <Card title="模板列表" size="small" style={{ height: '100%' }}>
            <List
              size="small"
              loading={loading}
              dataSource={templates}
              style={{ maxHeight: 'calc(80vh - 100px)', overflowY: 'auto' }}
              renderItem={(template) => (
                <TemplateListItem
                  key={template.template_metadata.id}
                  template={template}
                  onView={handleViewTemplate}
                  onEdit={handleEditTemplate}
                  onDelete={handleDeleteTemplate}
                />
              )}
            />
          </Card>
        </Col>

        {/* 模板详情查看 */}
        {viewingTemplate && (
          <Col span={8}>
            <Card title="模板详情" size="small" style={{ height: '100%' }}>
              <div style={{ maxHeight: 'calc(80vh - 100px)', overflowY: 'auto' }}>
                <Title level={5}>{viewingTemplate.template_metadata.name}</Title>
                <Paragraph style={{ fontSize: '12px' }}>{viewingTemplate.template_metadata.summary}</Paragraph>
                
                <Collapse 
                  size="small" 
                  defaultActiveKey={['1']}
                  items={currentViewingCollapseItems}
                />
              </div>
            </Card>
          </Col>
        )}

        {/* 添加/编辑模板表单 */}
        <Col span={viewingTemplate ? 8 : 16}>
          <Card title={editingTemplate ? '编辑模板' : '添加新模板'} size="small" style={{ height: '100%' }}>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleAddTemplate}
              size="small"
              style={{ maxHeight: 'calc(80vh - 100px)', overflowY: 'auto', paddingRight: 8 }}
            >
              <Form.Item
                name="template_id"
                label="模板ID"
                rules={[{ required: true, message: '请输入模板ID' }]}
              >
                <Input placeholder="例如：sales_analysis" disabled={!!editingTemplate} />
              </Form.Item>

              <Form.Item
                name="name"
                label="模板名称"
                rules={[{ required: true, message: '请输入模板名称' }]}
              >
                <Input placeholder="例如：销售数据分析" />
              </Form.Item>

              <Form.Item
                name="summary"
                label="模板摘要"
                rules={[{ required: true, message: '请输入模板摘要' }]}
              >
                <TextArea rows={2} placeholder="简要描述模板的用途和特点" />
              </Form.Item>

              <Form.Item
                name="analysis_goal"
                label="分析目标"
                rules={[{ required: true, message: '请输入分析目标' }]}
              >
                <TextArea rows={2} placeholder="描述分析的主要目标和预期结果" />
              </Form.Item>

              <Form.Item
                name="required_columns"
                label="必需列"
                extra="格式：列名|类型|描述（每行一个）"
              >
                <TextArea 
                  rows={3} 
                  placeholder="customer_id|string|客户唯一标识符\nsales_amount|number|销售金额" 
                />
              </Form.Item>

              <Form.Item
                name="optional_columns"
                label="可选列"
                extra="格式：列名|类型|描述（每行一个）"
              >
                <TextArea 
                  rows={2} 
                  placeholder="customer_type|string|客户类型\nregion|string|销售区域" 
                />
              </Form.Item>

              {/* 执行步骤动态编辑 */}
              <Form.Item label="执行步骤">
                <Form.List name="execution_steps">
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map(({ key, name, ...restField }) => (
                        <Card key={key} size="small" style={{ marginBottom: 8 }}>
                          <Row gutter={8} align="middle">
                            <Col span={20}>
                              <Form.Item
                                {...restField}
                                name={[name, 'prompt']}
                                label="步骤描述"
                                rules={[{ required: true, message: '请输入步骤描述' }]}
                                style={{ marginBottom: 8 }}
                              >
                                <TextArea rows={2} placeholder="描述这个分析步骤" />
                              </Form.Item>
                              <Form.Item
                                {...restField}
                                name={[name, 'save_to_variable']}
                                label="保存变量名（可选）"
                                style={{ marginBottom: 0 }}
                              >
                                <Input placeholder="例如：analysis_result" />
                              </Form.Item>
                            </Col>
                            <Col span={4}>
                              <Button 
                                type="text" 
                                icon={<MinusCircleOutlined />} 
                                onClick={() => remove(name)}
                                danger
                              />
                            </Col>
                          </Row>
                        </Card>
                      ))}
                      <Button 
                        type="dashed" 
                        onClick={() => add()} 
                        block 
                        icon={<PlusOutlined />}
                      >
                        添加执行步骤
                      </Button>
                    </>
                  )}
                </Form.List>
              </Form.Item>

              <Form.Item
                name="insights_template"
                label="洞察模板"
                extra="使用Markdown格式描述分析结果的展示模板"
              >
                <TextArea 
                  rows={4} 
                  placeholder="## 分析结果\n\n### 关键发现\n- 发现1\n- 发现2\n\n### 建议\n- 建议1\n- 建议2" 
                />
              </Form.Item>

              {/* 输出文件动态编辑 */}
              <Form.Item label="输出文件">
                <Form.List name="output_files">
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map(({ key, name, ...restField }) => (
                        <Card key={key} size="small" style={{ marginBottom: 8 }}>
                          <Row gutter={8} align="middle">
                            <Col span={20}>
                              <Row gutter={8}>
                                <Col span={12}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'type']}
                                    label="文件类型"
                                    rules={[{ required: true, message: '请选择文件类型' }]}
                                    style={{ marginBottom: 8 }}
                                  >
                                    <Select placeholder="选择文件类型">
                                      <Option value="chart">图表</Option>
                                      <Option value="table">数据表</Option>
                                      <Option value="report">报告</Option>
                                      <Option value="data">数据文件</Option>
                                    </Select>
                                  </Form.Item>
                                </Col>
                                <Col span={12}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'title']}
                                    label="文件标题"
                                    rules={[{ required: true, message: '请输入文件标题' }]}
                                    style={{ marginBottom: 8 }}
                                  >
                                    <Input placeholder="例如：销售趋势图" />
                                  </Form.Item>
                                </Col>
                              </Row>
                              <Row gutter={8}>
                                <Col span={12}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'source_variable']}
                                    label="数据源变量"
                                    style={{ marginBottom: 0 }}
                                  >
                                    <Input placeholder="例如：sales_data" />
                                  </Form.Item>
                                </Col>
                                <Col span={12}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'tool']}
                                    label="生成工具"
                                    style={{ marginBottom: 0 }}
                                  >
                                    <Select placeholder="选择生成工具">
                                      <Option value="matplotlib">Matplotlib</Option>
                                      <Option value="gpt_vis_chart">Gpt_Vis_Chart</Option>
                                      <Option value="seaborn">Seaborn</Option>
                                      <Option value="pandas">Pandas</Option>
                                    </Select>
                                  </Form.Item>
                                </Col>
                              </Row>
                            </Col>
                            <Col span={4}>
                              <Button 
                                type="text" 
                                icon={<MinusCircleOutlined />} 
                                onClick={() => remove(name)}
                                danger
                              />
                            </Col>
                          </Row>
                        </Card>
                      ))}
                      <Button 
                        type="dashed" 
                        onClick={() => add()} 
                        block 
                        icon={<PlusOutlined />}
                      >
                        添加输出文件
                      </Button>
                    </>
                  )}
                </Form.List>
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    {editingTemplate ? '更新模板' : '添加模板'}
                  </Button>
                  <Button onClick={() => {
                    form.resetFields();
                    setEditingTemplate(null);
                  }}>
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </Modal>
  );
};

export default TemplateConfigModal;