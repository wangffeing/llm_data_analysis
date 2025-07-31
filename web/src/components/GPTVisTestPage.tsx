import React, { useState } from 'react';
import { Modal, Card, Button, Space, Alert, Typography, Input, Row, Col } from 'antd';
import { ExperimentOutlined, PlayCircleOutlined, EditOutlined, CopyOutlined } from '@ant-design/icons';
import { GPTVis } from '@antv/gpt-vis';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface GPTVisTestPageProps {
  visible: boolean;
  onClose: () => void;
}

const GPTVisTestPage: React.FC<GPTVisTestPageProps> = ({ visible, onClose }) => {
  // 默认测试数据 - 使用 markdown 格式
  const defaultMarkdownContent = `# GPT-VIS 测试

这是一个测试页面，用于验证 GPT-Vis 组件的渲染效果。

## 折线图示例

以下是海底捞外卖收入从2013年到2022年的可视化图表：

\`\`\`vis-chart
{
  "type": "line",
  "data": [
    { "time": 2013, "value": 59.3 },
    { "time": 2014, "value": 64.4 },
    { "time": 2015, "value": 68.9 },
    { "time": 2016, "value": 74.4 },
    { "time": 2017, "value": 82.7 },
    { "time": 2018, "value": 91.9 },
    { "time": 2019, "value": 99.1 },
    { "time": 2020, "value": 101.6 },
    { "time": 2021, "value": 114.4 },
    { "time": 2022, "value": 121.0 }
  ]
}
\`\`\`
`;

  const [markdownInput, setMarkdownInput] = useState<string>(defaultMarkdownContent);
  const [currentContent, setCurrentContent] = useState<string>('');

  // 预设示例模板
  const exampleTemplates = {
    'line-chart': {
      name: '折线图',
      content: `# 折线图示例

\`\`\`vis-chart
{
  "type": "line",
  "data": [
    { "time": 2018, "value": 91.9 },
    { "time": 2019, "value": 99.1 },
    { "time": 2020, "value": 101.6 },
    { "time": 2021, "value": 114.4 },
    { "time": 2022, "value": 121.0 }
  ]
}
\`\`\`
`
    },
    'bar-chart': {
      name: '柱状图',
      content: `# 柱状图示例

\`\`\`vis-chart
{
  "type": "column",
  "data": [
    { "category": "产品A", "value": 320 },
    { "category": "产品B", "value": 280 },
    { "category": "产品C", "value": 220 },
    { "category": "产品D", "value": 180 }
  ]
}
\`\`\`
`
    },
    'pie-chart': {
      name: '饼图',
      content: `# 饼图示例

\`\`\`vis-chart
{
  "type": "pie",
  "data": [
    { "category": "移动端", "value": 45 },
    { "category": "PC端", "value": 30 },
    { "category": "平板端", "value": 15 },
    { "category": "其他", "value": 10 }
  ],
  "angleField": "value",
  "colorField": "category"
}
\`\`\`
`
    }
  };

  // 渲染图表
  const handleRenderChart = () => {
    setCurrentContent(markdownInput);
  };

  // 加载示例模板
  const loadTemplate = (templateKey: string) => {
    const template = exampleTemplates[templateKey as keyof typeof exampleTemplates];
    if (template) {
      setMarkdownInput(template.content);
    }
  };

  // 复制内容
  const copyContent = () => {
    navigator.clipboard.writeText(markdownInput);
  };

  return (
    <Modal
      title={
        <Space>
          <ExperimentOutlined />
          <span>GPT-Vis 测试页面</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={1200}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>
      ]}
      style={{ top: 20 }}
    >
      <div style={{ padding: '0 0 20px 0' }}>
        <Alert
          message="GPT-Vis 可视化测试环境"
          description="在这里您可以编辑 Markdown 内容，使用 vis-chart 代码块来定义图表，实时预览 GPT-Vis 的渲染效果。"
          type="info"
          showIcon
          style={{ marginBottom: '20px' }}
        />
        
        <Row gutter={16}>
          {/* 左侧：Markdown 编辑区 */}
          <Col span={12}>
            <Card 
              title={
                <Space>
                  <EditOutlined />
                  <span>Markdown 编辑器</span>
                </Space>
              }
              extra={
                <Space>
                  <Button 
                    icon={<CopyOutlined />}
                    onClick={copyContent}
                  >
                    复制
                  </Button>
                  <Button 
                    type="primary" 
                    icon={<PlayCircleOutlined />}
                    onClick={handleRenderChart}
                  >
                    渲染图表
                  </Button>
                </Space>
              }
            >
              <TextArea
                value={markdownInput}
                onChange={(e) => setMarkdownInput(e.target.value)}
                placeholder="请输入包含 vis-chart 代码块的 Markdown 内容..."
                rows={15}
                style={{ 
                  fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                  fontSize: '12px'
                }}
              />
              
              <div style={{ marginTop: '12px' }}>
                <Text strong style={{ marginBottom: '8px', display: 'block' }}>快速模板：</Text>
                <Space wrap>
                  {Object.entries(exampleTemplates).map(([key, template]) => (
                    <Button
                      key={key}
                      size="small"
                      onClick={() => loadTemplate(key)}
                    >
                      {template.name}
                    </Button>
                  ))}
                </Space>
              </div>
            </Card>
          </Col>
          
          {/* 右侧：图表预览区 */}
          <Col span={12}>
            <Card 
              title="图表预览"
              size="small"
            >
              <div style={{ 
                minHeight: '400px', 
                padding: '20px',
                border: '1px solid #f0f0f0',
                borderRadius: '8px',
                backgroundColor: '#fff'
              }}>
                {currentContent ? (
                  <GPTVis>{currentContent}</GPTVis>
                ) : (
                  <div style={{ 
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: '#999',
                    textAlign: 'center'
                  }}>
                    <div>
                      <PlayCircleOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                      <div>点击 "渲染图表" 按钮查看效果</div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </Col>
        </Row>
        
        {/* 底部：使用说明 */}
        <Card 
          title="使用说明" 
          size="small" 
          style={{ marginTop: '16px' }}
        >
          <div style={{ fontSize: '12px', color: '#666' }}>
            <p><strong>Markdown 格式：</strong></p>
            <ul>
              <li>使用标准 Markdown 语法编写内容</li>
              <li>在代码块中使用 <code>vis-chart</code> 标识符来定义图表</li>
              <li>图表数据使用 JSON 格式</li>
            </ul>
            <p><strong>支持的图表类型：</strong></p>
            <ul>
              <li><code>"type": "line"</code> - 折线图</li>
              <li><code>"type": "column"</code> - 柱状图</li>
              <li><code>"type": "pie"</code> - 饼图</li>
              <li><code>"type": "area"</code> - 面积图</li>
              <li><code>"type": "scatter"</code> - 散点图</li>
            </ul>
            <p><strong>示例格式：</strong></p>
            <pre style={{ background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
{`\`\`\`vis-chart
{
  "type": "line",
  "data": [
    { "time": 2020, "value": 100 },
    { "time": 2021, "value": 120 }
  ]
}
\`\`\``}
            </pre>
          </div>
        </Card>
      </div>
    </Modal>
  );
};

export default GPTVisTestPage;