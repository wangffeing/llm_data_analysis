import React, { useState, useMemo, useCallback } from 'react';
import {
  Drawer,
  Tabs,
  Card,
  Typography,
  List,
  Space,
  Tag,
  Collapse,
  Input,
  Empty,
  Divider,
  Radio
} from 'antd';
import {
  BookOutlined,
  BulbOutlined,
  SearchOutlined,
  PhoneOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
// 从数据文件导入所有知识库常量和类型
import {
  analysisMethodsKnowledge,
  allTerms,
  bestPracticesData,
  telecomBusinessScenarios,
  TermDefinition,
  MethodDetail,
  PracticeDetail,
  ModelDetail
} from '../constants/knowledgeData'; // 确保路径正确
import { useDebounceValue } from '../hooks/useDebounce';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;
const { TabPane } = Tabs;
const { Search } = Input;

interface DataAnalysisKnowledgeProps {
  visible: boolean;
  onClose: () => void;
}

// 将renderTerm提取为独立组件并使用React.memo
const TermCard = React.memo<{ term: TermDefinition; index: number }>(({ term, index }) => (
  <Card key={index} size="small" hoverable>
    <Text strong style={{ color: '#1677ff', fontSize: '16px' }}>{term.term}</Text>
    <Paragraph style={{ marginTop: '8px', lineHeight: '1.5' }}>{term.definition}</Paragraph>
    {term.formula && (
      <div style={{ marginBottom: '8px' }}>
        <Text code keyboard>{term.formula}</Text>
      </div>
    )}
    {term.example && (
      <div style={{ 
        padding: '8px', 
        backgroundColor: '#f6f9ff', 
        borderRadius: '4px', 
        fontSize: '12px', 
        marginBottom: '8px' 
      }}>
        <Text type="secondary"><strong>示例：</strong>{term.example}</Text>
      </div>
    )}
    {term.caution && (
      <div style={{
        backgroundColor: '#fffbe6',
        border: '1px solid #ffe58f',
        borderRadius: '2px',
        padding: '4px 8px',
        margin: '4px 0',
        fontSize: '12px',
        color: '#ad6800',
        wordWrap: 'break-word',
        wordBreak: 'break-word',
      }}>
        <strong>注意：</strong> {term.caution}
      </div>
    )}
  </Card>
));

// 提取方法列表项组件
const MethodListItem = React.memo<{ item: MethodDetail }>(({ item }) => (
  <List.Item>
    <List.Item.Meta
      title={<Text strong>{item.name}</Text>}
      description={
        <>
          <Text type="secondary">{item.description}</Text>
          {item.scenarios && (
            <div style={{marginTop: '4px'}}>
              <Tag color="geekblue">适用场景</Tag> {item.scenarios}
            </div>
          )}
        </>
      }
    />
    {item.models && (
      <div style={{ maxWidth: '60%' }}>
        <Space direction="vertical" style={{width: '100%'}}>
          {(item.models as ModelDetail[]).map((m, i) => (
            <Tag 
              key={i} 
              color="cyan" 
              style={{
                height: 'auto', 
                whiteSpace: 'normal', 
                padding: '4px 8px'
              }}
            >
              <b>{m.name}:</b> {m.desc}
            </Tag>
          ))}
        </Space>
      </div>
    )}
  </List.Item>
));

const DataAnalysisKnowledge: React.FC<DataAnalysisKnowledgeProps> = ({
  visible,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState('methods');
  const [termDictionary, setTermDictionary] = useState<'general' | 'telecom'>('general');
  const [searchTerm, setSearchTerm] = useState('');

  // 修复：使用 useDebounceValue 而不是 useDebounce
  const debouncedSearchTerm = useDebounceValue(searchTerm, 300);

  // 优化搜索过滤逻辑
  const filteredTerms = useMemo(() => {
    const sourceTerms = allTerms[termDictionary];
    if (!debouncedSearchTerm) return sourceTerms;

    const lowercasedSearchTerm = debouncedSearchTerm.toLowerCase();
    const result: Record<string, TermDefinition[]> = {};

    Object.entries(sourceTerms).forEach(([category, terms]) => {
      const filtered = terms.filter(
        (term) =>
          term.term.toLowerCase().includes(lowercasedSearchTerm) ||
          term.definition.toLowerCase().includes(lowercasedSearchTerm)
      );
      if (filtered.length > 0) {
        result[category] = filtered;
      }
    });
    return result;
  }, [debouncedSearchTerm, termDictionary]);

  // 使用useCallback优化事件处理
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);

  const handleTabChange = useCallback((key: string) => {
    setActiveTab(key);
  }, []);

  const handleDictionaryChange = useCallback((e: any) => {
    setTermDictionary(e.target.value as 'general' | 'telecom');
    setSearchTerm(''); // 清空搜索
  }, []);

  // 使用useMemo缓存术语渲染
  const termsContent = useMemo(() => {
    if (Object.keys(filteredTerms).length === 0) {
      return <Empty description="未找到相关术语" />;
    }

    return Object.entries(filteredTerms).map(([category, terms]) => (
      <div key={category}>
        <Divider orientation="left" style={{ textTransform: 'capitalize' }}>
          {category}
        </Divider>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '16px' 
        }}>
          {terms.map((term, index) => (
            <TermCard key={`${category}-${index}`} term={term} index={index} />
          ))}
        </div>
      </div>
    ));
  }, [filteredTerms]);

  // 使用useMemo缓存方法内容
  const methodsContent = useMemo(() => (
    <Collapse accordion>
      {Object.entries(analysisMethodsKnowledge).map(([key, method]) => (
        <Panel 
          header={<Space>{method.icon}<Text strong>{method.title}</Text></Space>} 
          key={key}
        >
          <div onClick={(e: React.MouseEvent) => e.stopPropagation()}>
            <Paragraph>{method.Descriptions}</Paragraph>
            <Collapse size="small" ghost defaultActiveKey={['details']} >
              <Panel header="方法详情" key="details">
                <List
                  dataSource={method.methods}
                  renderItem={(item: MethodDetail) => (
                    <MethodListItem key={item.name} item={item} />
                  )}
                />
              </Panel>
            </Collapse>
          </div>
        </Panel>
      ))}
    </Collapse>
  ), []);

  return (
    <Drawer
      title={
        <Space>
          <BookOutlined style={{ color: '#1677ff' }} />
          <span>数据分析专业知识库</span>
        </Space>
      }
      open={visible}
      onClose={onClose}
      width={1000}
      styles={{ body: { padding: '16px', backgroundColor: '#f7f8fa' } }}
    >
      <Tabs activeKey={activeTab} onChange={handleTabChange} size="large">
        <TabPane tab={<Space><BarChartOutlined />分析方法与模型</Space>} key="methods">
          <Title level={4}>数据分析方法与模型</Title>
          <Paragraph type="secondary">
            从描述到预测的全链路分析方法，包括高级统计分析和机器学习模型选择指南，帮助您选择最适合的分析方法。
          </Paragraph>
          {methodsContent}
        </TabPane>

        <TabPane tab={<Space><BulbOutlined />术语解释</Space>} key="terms">
          <Title level={4}>数据分析术语词典</Title>
          <Radio.Group 
            value={termDictionary} 
            onChange={handleDictionaryChange} 
            style={{ marginBottom: 16 }}
          >
            <Radio.Button value="general">通用分析术语</Radio.Button>
            <Radio.Button value="telecom">通信行业术语</Radio.Button>
          </Radio.Group>
          <Search
            placeholder="在当前词典中搜索术语或定义..."
            value={searchTerm}
            onChange={handleSearchChange}
            style={{ marginBottom: '16px' }}
            allowClear
          />
          {termsContent}
        </TabPane>
        
        <TabPane tab={<Space><PhoneOutlined />业务场景</Space>} key="scenarios">
          <div style={{ marginBottom: '16px' }}>
            <Title level={4}>通信行业业务场景</Title>
            <Paragraph type="secondary">了解典型的业务分析场景，快速上手实际项目。</Paragraph>
          </div>
          {Object.entries(telecomBusinessScenarios).map(([key, category]) => (
            <Card key={key} title={<Space>{category.icon}<span>{category.title}</span></Space>} style={{ marginBottom: '16px' }}>
              {category.scenarios.map((scenario, index) => (
                <Card key={index} type="inner" title={scenario.name} style={{ marginBottom: '12px' }}>
                  <Paragraph>{scenario.description}</Paragraph>
                  <div style={{ marginBottom: '12px' }}>
                    <Text strong>关键指标：</Text>
                    <Space wrap style={{ marginTop: '4px' }}>
                      {scenario.keyMetrics.map((metric, metricIndex) => <Tag key={metricIndex} color="blue">{metric}</Tag>)}
                    </Space>
                  </div>
                  <Collapse size="small">
                    <Panel header="分析步骤" key="steps">
                      <List
                        size="small"
                        dataSource={scenario.analysisSteps}
                        renderItem={(step, stepIndex) => (
                          <List.Item>
                            <Text>
                              <span style={{ color: '#1677ff', fontWeight: 'bold' }}>{stepIndex + 1}.</span>{' '}{step}
                            </Text>
                          </List.Item>
                        )}
                      />
                    </Panel>
                  </Collapse>
                </Card>
              ))}
            </Card>
          ))}
        </TabPane>


      </Tabs>
    </Drawer>
  );
};

export default React.memo(DataAnalysisKnowledge);