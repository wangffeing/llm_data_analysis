import React from 'react';
import { Table, Card, Typography, Space, Tag } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface DataTableProps {
  sourceName: string;
  columns: { title: string; dataIndex: string; key: string; ellipsis?: boolean; width?: number; render?: (text: any) => React.ReactNode }[];
  data: any[];
  totalShown: number;
  maxHeight?: number;
}

const DataTable: React.FC<DataTableProps> = ({ 
  sourceName, 
  columns, 
  data, 
  totalShown, 
  maxHeight = 400 
}) => {
  // 为列添加默认的render函数，以美化显示
  const tableColumns = columns.map(col => ({
    ellipsis: true,
    width: 150,
    ...col,
    render: col.render ? col.render : (text: any) => {
      if (text === null || text === undefined || text === '-') {
        return <Text type="secondary">-</Text>;
      }
      return String(text);
    }
  }));

  const tableData = data.map((row, index) =>
  (typeof row === 'object' && row !== null && !Array.isArray(row))
  ? { ...row, key: row.key ?? index }
  : { key: index } // 如果不是对象，至少提供key
  );

  return (
    <Card 
      size="small" 
      style={{ 
        margin: '8px 0',
        border: '1px solid #e8f4fd',
        borderRadius: '8px'
      }}
      styles={{ body: { padding: '12px' } }}  // 修改这里
    >
      <Space direction="vertical" size={8} style={{ width: '100%' }}>
        <Space align="center">
          <DatabaseOutlined style={{ color: '#1890ff' }} />
          <Title level={5} style={{ margin: 0 }}>
            {sourceName} 数据预览
          </Title>
          <Tag color="blue">前 {totalShown} 条</Tag>
        </Space>
        
        <Table
          columns={tableColumns}
          dataSource={tableData}
          pagination={false}
          scroll={{ 
            x: columns.length * 150,
            y: maxHeight 
          }}
          size="small"
          bordered={false}
          style={{
            background: '#fafafa'
          }}
        />
      </Space>
    </Card>
  );
};
export default DataTable;