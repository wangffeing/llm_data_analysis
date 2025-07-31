import React, { useState, useMemo, useCallback } from 'react';
import { 
  Modal, List, Typography, Space, Input, Button, Form, 
  Popconfirm, Drawer, Row, Col, Tag, App 
} from 'antd';
import { 
  DatabaseOutlined, SearchOutlined, PlusOutlined, 
  EditOutlined, DeleteOutlined, SettingOutlined 
} from '@ant-design/icons';
import { createStyles } from 'antd-style';
import { apiService } from '../services/apiService';

const { Text } = Typography;
const { TextArea } = Input;

interface DataSource {
  name: string;
  description?: string;
  type?: string;
  table_name?: string;
  table_columns?: string[];
  table_columns_names?: string[];
  table_order?: string;
}

interface DataSourceModalProps {
  visible: boolean;
  dataSources: DataSource[];
  selectedDataSource: DataSource | null;
  onSelect: (dataSource: DataSource) => void;
  onCancel: () => void;
  onDataSourcesChange?: () => void; // 新增：数据源变更回调
}

const useStyles = createStyles(({ token, css }) => ({
  dataSourceItem: css`
    cursor: pointer;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    border: 1px solid #f0f0f0;
    background-color: #fff;
    transition: all 0.2s ease;
    
    &:hover {
      border-color: #1677ff !important;
      box-shadow: 0 2px 8px rgba(22, 119, 255, 0.15) !important;
    }
  `,
  selectedItem: css`
    border: 2px solid #1677ff !important;
    background-image: linear-gradient(123deg, #e5f4ff 0%, #efe7ff 100%); 
  `,
  searchInput: css`
    margin-bottom: 16px;
  `,
  actionButtons: css`
    display: flex;
    gap: 8px;
    margin-top: 8px;
  `,
  manageButton: css`
    margin-bottom: 16px;
  `
}));

const DataSourceModal: React.FC<DataSourceModalProps> = ({
  visible,
  dataSources,
  selectedDataSource,
  onSelect,
  onCancel,
  onDataSourcesChange
}) => {
  const { message } = App.useApp(); // 使用Hook方式获取message
  const { styles } = useStyles();
  const [searchText, setSearchText] = useState('');
  const [manageDrawerVisible, setManageDrawerVisible] = useState(false);
  const [editingDataSource, setEditingDataSource] = useState<DataSource | null>(null);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  
  // 添加刷新数据源函数
  const refreshDataSources = useCallback(async () => {
    if (onDataSourcesChange) {
      await onDataSourcesChange();
    }
  }, [onDataSourcesChange]);
  
  // 过滤数据源
  const filteredDataSources = useMemo(() => {
    if (!searchText.trim()) {
      return dataSources;
    }
    
    const searchLower = searchText.toLowerCase();
    return dataSources.filter(item => 
      item.name.toLowerCase().includes(searchLower) ||
      (item.description && item.description.toLowerCase().includes(searchLower)) ||
      (item.type && item.type.toLowerCase().includes(searchLower))
    );
  }, [dataSources, searchText]);
  
  const handleSelect = (dataSource: DataSource) => {
    onSelect(dataSource);
    onCancel();
  };

  const handleCancel = () => {
    setSearchText('');
    onCancel();
  };

  const handleManageDataSources = () => {
    setManageDrawerVisible(true);
  };

  const handleAddDataSource = () => {
    setEditingDataSource(null);
    form.resetFields();
  };

  const handleEditDataSource = (dataSource: DataSource) => {
    setEditingDataSource(dataSource);
    form.setFieldsValue({
      name: dataSource.name,
      table_name: dataSource.table_name,
      table_des: dataSource.description,
      table_order: dataSource.table_order,
      table_columns: dataSource.table_columns?.join(', '),
      table_columns_names: dataSource.table_columns_names?.join(', ')
    });
  };

  const handleDeleteDataSource = async (name: string) => {
    setLoading(true);
    try {
      await apiService.deleteDataSource(name);
      message.success('数据源删除成功');
      await refreshDataSources(); // 调用刷新
    } catch (error) {
      console.error('删除数据源失败:', error);
      message.error('删除数据源失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDataSource = async (values: any) => {
    setLoading(true);
    try {
      const requestData = {
        table_name: values.table_name,
        table_des: values.table_des,
        table_order: values.table_order,
        table_columns: values.table_columns.split(',').map((col: string) => col.trim()),
        table_columns_names: values.table_columns_names.split(',').map((col: string) => col.trim())
      };
      
      if (editingDataSource) {
        await apiService.updateDataSource(editingDataSource.name, requestData);
        message.success('数据源更新成功');
      } else {
        await apiService.createDataSource({
          name: values.name,
          ...requestData
        });
        message.success('数据源创建成功');
      }
      
      form.resetFields();
      setEditingDataSource(null);
      await refreshDataSources(); // 调用刷新
    } catch (error) {
      console.error('保存数据源失败:', error);
      message.error(editingDataSource ? '更新数据源失败' : '创建数据源失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Modal
        title="选择数据源"
        open={visible}
        onCancel={handleCancel}
        footer={null}
        width={600}
        styles={{
          body: { padding: '20px 24px' }
        }}
      >
        {/* 管理按钮 */}
        <Button 
          type="dashed" 
          icon={<SettingOutlined />}
          onClick={handleManageDataSources}
          className={styles.manageButton}
          block
        >
          管理数据源
        </Button>
        
        {/* 搜索框 */}
        <Input
          className={styles.searchInput}
          placeholder="搜索数据源名称、描述或类型..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />
        
        {/* 数据源列表 */}
        <List
          dataSource={filteredDataSources}
          locale={{
            emptyText: searchText ? '未找到匹配的数据源' : '暂无数据源'
          }}
          renderItem={(item) => {
            const isSelected = selectedDataSource?.name === item.name;
            return (
              <List.Item
                onClick={() => handleSelect(item)}
                className={`${styles.dataSourceItem} ${isSelected ? styles.selectedItem : ''}`}
              >
                <List.Item.Meta
                  avatar={
                    <DatabaseOutlined 
                      style={{ 
                        fontSize: '20px', 
                        color: isSelected ? '#1677ff' : '#666' 
                      }} 
                    />
                  }
                  title={
                    <Space>
                      <Text strong style={{ fontSize: '16px' }}>
                        {item.name}
                      </Text>
                      {item.type && (
                        <Tag color="blue">{item.type}</Tag>
                      )}
                    </Space>
                  }
                  description={
                    item.description && (
                      <Text type="secondary" style={{ fontSize: '14px' }}>
                        {item.description}
                      </Text>
                    )
                  }
                />
              </List.Item>
            );
          }}
        />
      </Modal>

      {/* 数据源管理抽屉 */}
      <Drawer
        title="数据源管理"
        open={manageDrawerVisible}
        onClose={() => setManageDrawerVisible(false)}
        width={800}
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleAddDataSource}
          >
            新增数据源
          </Button>
        }
      >
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <div style={{ height: '600px', overflowY: 'auto', paddingRight: '8px' }}>
              <List
                dataSource={dataSources}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button 
                        type="text" 
                        icon={<EditOutlined />}
                        onClick={() => handleEditDataSource(item)}
                      />,
                      <Popconfirm
                        title="确定删除此数据源？"
                        onConfirm={() => handleDeleteDataSource(item.name)}
                        okText="确定"
                        cancelText="取消"
                      >
                        <Button 
                          type="text" 
                          danger 
                          icon={<DeleteOutlined />}
                        />
                      </Popconfirm>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<DatabaseOutlined />}
                      title={item.name}
                      description={item.description}
                    />
                  </List.Item>
                )}
              />
            </div>
          </Col>
          <Col span={12}>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSaveDataSource}
            >
              <Form.Item
                label="数据源名称"
                name="name"
                rules={[{ required: true, message: '请输入数据源名称' }]}
              >
                <Input disabled={!!editingDataSource} />
              </Form.Item>
              
              <Form.Item
                label="表名"
                name="table_name"
                rules={[{ required: true, message: '请输入表名' }]}
              >
                <Input />
              </Form.Item>
              
              <Form.Item
                label="描述"
                name="table_des"
                rules={[{ required: true, message: '请输入描述' }]}
              >
                <TextArea rows={3} />
              </Form.Item>
              
              <Form.Item
                label="排序字段"
                name="table_order"
                rules={[{ required: true, message: '请输入排序字段' }]}
              >
                <Input />
              </Form.Item>
              
              <Form.Item
                label="表字段（逗号分隔）"
                name="table_columns"
                rules={[{ required: true, message: '请输入表字段' }]}
              >
                <TextArea rows={3} placeholder="例如：field1, field2, field3" />
              </Form.Item>
              
              <Form.Item
                label="字段中文名（逗号分隔）"
                name="table_columns_names"
                rules={[{ required: true, message: '请输入字段中文名' }]}
              >
                <TextArea rows={3} placeholder="例如：字段1, 字段2, 字段3" />
              </Form.Item>
              
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    {editingDataSource ? '更新' : '创建'}
                  </Button>
                  <Button onClick={() => {
                    form.resetFields();
                    setEditingDataSource(null);
                  }}>
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Col>
        </Row>
      </Drawer>
    </>
  );
};

export default DataSourceModal;