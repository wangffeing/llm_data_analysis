import React, { useState } from 'react';
import { 
  Drawer, 
  Collapse, 
  Card, 
  Steps, 
  Tag, 
  Space, 
  Typography, 
  Button,
  List,
  theme
} from 'antd';
import {
  BookOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  BulbOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  SearchOutlined,
  LineChartOutlined,
  BranchesOutlined,
  AlertOutlined,
  ToolOutlined,
  CodeOutlined,
  CheckOutlined,
  FileTextOutlined,
  BulbFilled,
  MessageOutlined,
  PhoneOutlined,
  StarOutlined,
  TeamOutlined,
  FundProjectionScreenOutlined,
  SmileOutlined,
  RobotOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { Welcome } from '@ant-design/x';
import logo from '../resource/logo1.png';
import Robot from '../resource/role2.png';
import DataAnalysisKnowledge from './DataAnalysisKnowledge';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;
const { Step } = Steps;

interface AnalysisGuideProps {
  visible: boolean;
  onClose: () => void;
  selectedDataSource?: any;
  onSubmit?: (value: string) => void;
}

const AnalysisGuide: React.FC<AnalysisGuideProps> = ({
  visible,
  onClose,
  selectedDataSource,
  onSubmit
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [knowledgeDrawerVisible, setKnowledgeDrawerVisible] = useState(false);

  const generateIntelligentPrompt = (step: any) => {
    const { title, description, detailedTasks, keyPoints, examplePrompt, expectedOutcome } = step;
    
    // 提取详细任务项
    const taskItems = detailedTasks.flatMap((task: any) => 
      task.items.map((item: string) => `- ${item}`)
    ).join('\n');
    
    // 构建智能提示
        const prompt = `请基于当前数据源进行「${title}」分析。
        **分析目标：** ${examplePrompt}
        请结合数据源的特点，制定详细的分析计划并开始执行。`;
  //   const prompt = `请基于当前数据源进行「${title}」分析。

  // **分析目标：** ${description}

  // **具体任务要求：**
  // ${taskItems}

  // **关键要点：**
  // ${keyPoints.map((point: string) => `• ${point}`).join('\n')}

  // **预期产出：** ${expectedOutcome}

  // **参考示例：** ${examplePrompt}

  // 请结合数据源的特点，制定详细的分析计划并开始执行。`;
    
    return prompt;
  };
  const handleIntelligentAnalysis = (step: any) => {
    if (!onSubmit || !selectedDataSource) {
      // message.warning('请确保已选择数据源');
      return;
    }
    
    const intelligentPrompt = generateIntelligentPrompt(step);
    onSubmit(intelligentPrompt);
    onClose(); // 关闭指引窗口
    // message.success(`已发起${step.title}的智能分析请求`);
  };

  const analysisSteps = [
    {
      title: '数据理解与准备',
      icon: <BookOutlined />,
      description: '全面了解数据的基本结构、业务背景和数据质量状况。',
      detailedTasks: [
        {
          category: '数据概览',
          icon: <DatabaseOutlined />,
          items: [
            '查看数据集的基本信息：行数、列数、文件大小',
            '了解数据的来源、收集时间和业务背景',
            '识别数据类型：数值型、分类型、时间型、文本型',
            '检查字段命名规范和含义'
          ]
        },
        {
            category: '数据清洗',
            icon: <ToolOutlined />,
            items: [
                '处理缺失值：删除、填充（均值、中位数、众数、模型预测）',
                '处理异常值：删除、替换、或作为特殊特征处理',
                '处理重复记录：根据业务规则去重',
                '修正数据格式和类型不一致的问题'
            ]
        },
        {
          category: '数据质量检查',
          icon: <SearchOutlined />,
          items: [
            '统计缺失值的数量和分布模式',
            '识别重复记录和异常值',
            '检查数据的一致性和完整性',
            '评估数据的时效性和准确性'
          ]
        },
        {
          category: '字段分析',
          icon: <BranchesOutlined />,
          items: [
            '分析每个字段的业务含义和重要性',
            '确定关键字段和目标变量',
            '了解字段间的逻辑关系',
            '识别可能需要转换的字段'
          ]
        }
      ],
      keyPoints: [
        '数据理解是分析的基础，不可忽视。',
        '关注业务背景，理解数据产生的场景。',
        '数据质量直接影响分析结果的可靠性。',
        '建议建立数据字典，记录重要发现。'
      ],
      examplePrompt: '请对当前数据集进行全面的数据理解与准备。请提供数据的基本信息（行数、列数、数据类型），进行数据质量检查（缺失值、重复项、异常值），并分析各字段的业务含义，最后总结数据整体质量。',
      expectedOutcome: '对数据有全面清晰的认识，为后续分析奠定基础。'
    },
    {
      title: '探索性数据分析',
      icon: <ExperimentOutlined />,
      description: '通过统计分析和可视化深入探索数据的分布特征和内在规律。',
      detailedTasks: [
        {
          category: '描述性统计',
          icon: <LineChartOutlined />,
          items: [
            '计算数值型变量的均值、中位数、标准差等统计量',
            '分析分类变量的频数分布和占比',
            '识别数据的分布形态：正态、偏态、多峰等'
          ]
        },
        {
          category: '数据分布分析',
          icon: <BarChartOutlined />,
          items: [
            '绘制直方图观察数值变量的分布',
            '使用箱线图识别异常值和四分位数',
            '创建饼图和柱状图展示分类变量分布',
            '分析时间序列数据的趋势和季节性'
          ]
        },
        {
          category: '关联性分析',
          icon: <BranchesOutlined />,
          items: [
            '计算变量间的相关系数矩阵',
            '使用散点图矩阵或高级可视化方法探索非线性关系',
            '使用热力图可视化相关性强度',
            '识别多重共线性问题'
          ]
        },
        {
          category: '异常值检测',
          icon: <AlertOutlined />,
          items: [
            '使用统计方法识别异常值（如3σ原则）',
            '应用箱线图方法检测离群点',
            '分析异常值的业务合理性',
            '决定异常值的处理策略'
          ]
        }
      ],
      keyPoints: [
        '可视化是理解数据的有效手段。',
        '关注数据的分布特征和异常情况。',
        '相关性不等于因果性。',
        '异常值可能包含重要信息，需谨慎处理。'
      ],
      examplePrompt: '请对该数据集进行全面的探索性数据分析（EDA）。请对核心变量进行描述性统计和分布可视化（如直方图、箱线图），计算并可视化变量间的相关性矩阵，并识别出需要关注的异常值或特殊模式。',
      expectedOutcome: '深入理解数据特征，发现潜在的模式和问题。'
    },
    {
      title: '深度业务分析',
      icon: <BarChartOutlined />,
      description: '结合业务目标进行针对性的深度分析，挖掘业务洞察。',
      detailedTasks: [
        {
          category: '趋势分析',
          icon: <LineChartOutlined />,
          items: [
            '分析关键指标的时间趋势变化',
            '识别周期性模式和季节性特征',
            '检测趋势的转折点和异常波动',
            '预测短期趋势发展方向'
          ]
        },
        {
          category: '分组对比分析',
          icon: <BranchesOutlined />,
          items: [ '按关键维度对数据进行分组', '比较不同组别的指标差异', '分析组间差异的统计显著性', '进行同期群分析（Cohort Analysis）' ]
        },
        {
          category: '细分市场分析',
          icon: <DatabaseOutlined />,
          items: [
            '基于客户特征进行市场细分',
            '分析不同细分市场的特点',
            '评估各细分市场的价值和潜力',
            '制定针对性的策略建议'
          ]
        },
        {
          category: '影响因素分析',
          icon: <SearchOutlined />,
          items: [
            '识别影响关键指标的主要因素',
            '量化各因素的影响程度',
            '分析因素间的交互作用',
            '构建因果关系假设'
          ]
        },
        {
            category: '用户行为分析',
            icon: <RocketOutlined />, // 或其他合适的图标
            items: [
                '构建用户画像，理解不同用户群体的特征',
                '分析用户路径和转化漏斗，识别流失关键节点',
                '使用 RFM 模型评估用户价值',
                '进行购物篮分析，发现商品间的关联规则'
            ]
        }
      ],
      keyPoints: [
        '始终围绕业务目标进行分析。',
        '注重分析结果的业务可解释性。',
        '寻找可操作的业务洞察。',
        '多使用对比、细分、溯源等分析方法。'
      ],
      // [新增] 示例提问
      examplePrompt: '请结合业务目标进行深度分析。请分析关键指标随时间的变化趋势，对比不同维度（如地区、产品）下的性能差异，识别出最有价值的客户群体，并初步探究影响核心业务指标的关键驱动因素。',
      expectedOutcome: '获得有价值的业务洞察，为决策提供数据支撑。'
    },
    {
      title: '预测建模与机器学习',
      icon: <RocketOutlined />,
      description: '构建预测模型，利用机器学习技术解决业务问题。',
      detailedTasks: [
        {
          category: '特征工程',
          icon: <ToolOutlined />,
          items: [
            '选择与目标变量相关的特征',
            '创建新的衍生特征和交互特征',
            '处理分类变量编码（独热编码、标签编码）',
            '进行特征缩放和标准化'
          ]
        },
        {
          category: '模型选择',
          icon: <CodeOutlined />,
          items: [
            '根据问题类型选择合适的算法',
            '比较线性模型、树模型、集成模型等',
            '考虑模型的可解释性要求',
            '评估计算复杂度和实施难度',
            '可建立一个简单的基线模型作为性能比较的起点'
          ]
        },
        {
          category: '模型训练与调优',
          icon: <ToolOutlined />,
          items: [
            '划分训练集、验证集和测试集',
            '使用交叉验证评估模型性能',
            '调整超参数优化模型效果',
            '防止过拟合和欠拟合'
          ]
        },
        {
          category: '模型评估',
          icon: <CheckOutlined />,
          items: [
            '选择合适的评估指标（准确率、召回率、F1等）',
            '分析模型的混淆矩阵和ROC曲线',
            '评估模型在不同数据子集上的表现',
            '进行模型的稳定性测试',
            '结合业务场景，分析不同模型错误（如假阳性/假阴性）带来的业务成本'
          ]
        }
      ],
      keyPoints: [
        '特征工程往往比算法选择更重要。',
        '避免数据泄露，确保模型的泛化能力。',
        '平衡模型复杂度和可解释性。',
        '持续监控模型在生产环境中的表现。'
      ],
      // [新增] 示例提问
      examplePrompt: '请构建一个预测模型，以[指定目标变量，如：客户是否流失]为目标。请执行完整的机器学习流程，包括特征工程、选择合适的算法、划分数据集、模型训练，并使用交叉验证和关键评估指标（如AUC、F1分数）来评估模型性能。',
      expectedOutcome: '构建可靠的预测模型，提升业务决策的科学性。'
    },
    {
      title: '结果解释与报告',
      icon: <BulbOutlined />,
      description: '解释分析结果，提供可操作的业务建议和专业报告。',
      detailedTasks: [
        {
          category: '结果总结',
          icon: <FileTextOutlined />,
          items: [
            '总结分析的主要发现和关键洞察',
            '量化分析结果的业务价值',
            '识别分析中的局限性和不确定性',
            '验证结果与业务常识的一致性'
          ]
        },
        {
          category: '业务建议',
          icon: <BulbFilled />,
          items: [
            '基于分析结果提出具体的行动建议',
            '建议通过 A/B 测试来验证关键假设和策略的有效性',
            '评估建议的可行性和实施难度',
            '预估建议实施后的预期效果',
            '制定实施计划和监控指标'
          ]
        },
        {
          category: '可视化报告',
          icon: <BarChartOutlined />,
          items: [
            '设计清晰直观的图表展示关键结果',
            '创建交互式仪表板便于持续监控',
            '编写面向不同受众的分析报告',
            '准备汇报材料和演示文稿'
          ]
        },
        {
          category: '后续行动',
          icon: <CheckCircleOutlined />,
          items: [
            '制定分析结果的跟踪和验证计划',
            '建立定期更新分析的机制',
            '培训相关人员理解和使用分析结果',
            '收集反馈，持续改进分析方法'
          ]
        }
      ],
      keyPoints: [
        '用业务语言解释技术结果',
        '提供具体可操作的建议',
        '量化预期效果和风险',
        '建立长期的分析和监控机制'
      ],
      examplePrompt: '请根据以上所有分析，生成一份完整的分析报告。报告需用清晰的业务语言总结核心发现，提出3-5条具体、可执行的业务建议并量化其预期影响，并创建关键的可视化图表来支撑结论。',
      expectedOutcome: '形成完整的分析报告，推动业务决策和改进。'
    }
  ];
  
  // 在文件顶部添加类型定义
  interface BusinessScenario {
    scenario: string;
    description: string;
    icon: React.ReactElement;
  }
  
  interface BusinessScenarios {
    [key: string]: BusinessScenario[];
  }

  // 修改businessScenarios对象的定义
  const businessScenarios: BusinessScenarios = {
    "数据理解与准备": [
      {
        scenario: "客服通话数据分析",
        description: "分析客服通话记录前，需要了解：通话时长单位（秒/分钟）？接通率如何计算？是否区分人工和智能客服？",
        icon: <PhoneOutlined />
      },
      {
        scenario: "工单处理数据分析",
        description: "分析工单数据前，需要确认：工单状态有哪些？处理时长如何定义？是否有工单优先级分类？",
        icon: <FileTextOutlined />
      },
      {
        scenario: "客户满意度数据分析",
        description: "分析满意度数据前，需要了解：评分范围（1-5分还是1-10分）？评价渠道有哪些？是否有无效评价？",
        icon: <StarOutlined />
      }
    ],
    "探索性数据分析": [
      {
        scenario: "呼叫中心话务量分析",
        description: "探索每日话务量分布，识别高峰时段，分析不同时间段的接通率和平均等待时长变化规律。",
        icon: <LineChartOutlined />
      },
      {
        scenario: "客服人员绩效分析",
        description: "分析各客服代表的通话量、平均通话时长、客户满意度分布，识别绩效异常和优秀表现。",
        icon: <TeamOutlined />
      }
      ],
      "深度业务分析": [
      {
        scenario: "客户流失预警分析",
        description: "分析投诉频次、通话时长、问题解决率等指标，识别高风险流失客户的行为特征。",
        icon: <AlertOutlined />
      },
      {
        scenario: "服务质量趋势分析",
        description: "按月度分析接通率、首次解决率、客户满意度变化趋势，识别服务质量波动原因。",
        icon: <HeartOutlined />
      }
      ],
      "预测建模与机器学习": [
      {
        scenario: "话务量预测模型",
        description: "基于历史通话数据、节假日、促销活动等因素，预测未来7-30天的话务量需求。",
        icon: <FundProjectionScreenOutlined />
      },
      {
        scenario: "客户满意度预测",
        description: "根据通话时长、问题类型、处理时间等特征，预测客户对本次服务的满意度评分。",
        icon: <SmileOutlined />
      }
    ],
    "结果解释与报告": [
      {
        scenario: "客服中心运营报告",
        description: "生成月度客服运营报告，包含关键指标趋势、问题热点分析和改进建议。",
        icon: <FileTextOutlined />
      },
      {
        scenario: "服务质量改进建议",
        description: "基于数据分析结果，提出具体的人员配置、培训重点、流程优化建议。",
        icon: <BulbOutlined />
      }
    ]
  };

  const handleStepClick = (stepIndex: number) => {
    setActiveStep(stepIndex);
  };

  const handleStepComplete = (stepIndex: number) => {
    if (!completedSteps.includes(stepIndex)) {
      setCompletedSteps([...completedSteps, stepIndex]);
    }
  };

  const currentStepData = analysisSteps[activeStep];

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOutlined style={{ color: '#1677ff' }} />
          <span>数据分析流程指引</span>
          {selectedDataSource && (
            <Tag color="blue">{selectedDataSource.name}</Tag>
          )}
        </div>
      }
      placement="right"
      width={520}
      open={visible}
      onClose={onClose}
      bodyStyle={{ padding: '16px' }}
    >


      <div style={{ height: '100%', overflow: 'auto' }}>

        <div style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#fff', borderRadius: '12px' }}>
          <Welcome
            // variant="borderless"
            icon={<img src={Robot} alt="Logo" style={{ width: 64, height: 64 }} />}
            title="数据分析流程指引"
            description="这里为您规划了从数据理解到结果报告的每个关键环节，助您系统高效地完成数据分析。"
            style={{
              backgroundImage: 'linear-gradient(97deg, #f2f9fe 0%, #f7f3ff 100%)',
            }}
          />
        </div>
        <Steps
          direction="vertical"
          size="small"
          current={activeStep}
          style={{ marginBottom: '20px' }}
          onChange={handleStepClick}
        >
          {analysisSteps.map((step, index) => (
            <Step
              key={index}
              title={
                <div 
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    cursor: 'pointer'
                  }}
                >
                  {step.icon}
                  <span>{step.title}</span>
                  {completedSteps.includes(index) && (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  )}
                </div>
              }
              description={step.description}
              status={completedSteps.includes(index) ? 'finish' : 
                      index === activeStep ? 'process' : 'wait'}
            />
          ))}
        </Steps>

        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>{currentStepData.title}</span>
              <Space>
                {selectedDataSource && onSubmit && (
                  <Button 
                    type="primary"
                    size="small"
                    icon={<RocketOutlined />}
                    onClick={() => handleIntelligentAnalysis(currentStepData)}
                    style={{ 
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none'
                    }}
                  >
                    AI智能分析
                  </Button>
                )}
                <Tag 
                  color={completedSteps.includes(activeStep) ? 'green' : 'blue'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleStepComplete(activeStep)}
                  icon={<CheckCircleOutlined />}
                >
                  {completedSteps.includes(activeStep) ? '已完成' : '标记完成'}
                </Tag>
                <Button 
                  type="default"
                  size="small"
                  icon={<BookOutlined />}
                  onClick={() => setKnowledgeDrawerVisible(true)}
                  style={{ 
                    background: 'linear-gradient(135deg,rgb(235, 245, 248) 0%,rgb(237, 223, 250) 100%)',
                    border: 'none',
                    color: 'rgb(66, 143, 166)'
                  }}
                >
                  专业知识库
                </Button>
              </Space>
            </div>
          }
          size="small"
        >
          <Paragraph style={{ fontSize: '14px', marginBottom: '16px', color: '#666' }}>
            {currentStepData.description}
          </Paragraph>
          
          <Collapse 
            size="small" 
            style={{ marginBottom: '16px' }}
            defaultActiveKey={['0']}
          >
            {currentStepData.detailedTasks.map((taskGroup, groupIndex) => (
              <Panel 
                key={groupIndex}
                header={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {taskGroup.icon}
                    <span style={{ fontWeight: '500' }}>{taskGroup.category}</span>
                  </div>
                }
              >
                <List
                  size="small"
                  dataSource={taskGroup.items}
                  renderItem={(item, index) => (
                    <List.Item style={{ padding: '4px 0', border: 'none' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                        <span style={{ 
                          color: '#1677ff', 
                          fontSize: '12px', 
                          marginTop: '2px',
                          minWidth: '16px'
                        }}>
                          {index + 1}.
                        </span>
                        <Text style={{ fontSize: '13px', lineHeight: '1.5' }}>
                          {item}
                        </Text>
                      </div>
                    </List.Item>
                  )}
                />
              </Panel>
            ))}
          </Collapse>

          <div style={{ marginBottom: '16px' }}>
            <Title level={5} style={{ fontSize: '14px', marginBottom: '8px', color: '#1677ff' }}>
              <Space>
                <BulbOutlined />
                <span>关键要点</span>
              </Space>

            </Title>
            <div style={{ 
              backgroundColor: '#f6f9ff', 
              padding: '12px', 
              borderRadius: '6px',
              border: '1px solid #e6f4ff'
            }}>
              {currentStepData.keyPoints.map((point, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  gap: '8px',
                  marginBottom: index < analysisSteps[activeStep].keyPoints.length - 1 ? '8px' : '0'
                }}>
                  <span style={{ color: '#1677ff', fontSize: '12px', marginTop: '2px' }}>•</span>
                  <Text style={{ fontSize: '13px', lineHeight: '1.4' }}>{point}</Text>
                </div>
              ))}
            </div>
          </div>

          <div>
            <Title level={5} style={{ fontSize: '14px', marginBottom: '8px', color: '#52c41a' }}>
              <Space>
                <CheckOutlined />
                <span>预期成果</span>
              </Space>

            </Title>
            <div style={{ 
              backgroundColor: '#f6ffed', 
              padding: '12px', 
              borderRadius: '6px',
              border: '1px solid #d9f7be'
            }}>
              <Text style={{ fontSize: '13px', lineHeight: '1.4', color: '#389e0d' }}>
                {currentStepData.expectedOutcome}
              </Text>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <Title level={5} style={{ fontSize: '14px', marginBottom: '8px', color: '#fa8c16' }}>
              <Space>
                <MessageOutlined />
                <span>示例提问</span>
              </Space>
            </Title>
            <div style={{ backgroundColor: '#fffbe6', padding: '12px', borderRadius: '6px', border: '1px solid #ffe58f' }}>
              <Text style={{ fontSize: '13px', lineHeight: '1.5', color: '#d46b08' }}>
                {currentStepData.examplePrompt}
              </Text>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <Title level={5} style={{ fontSize: '14px', marginBottom: '8px', color: '#52c41a' }}>
              <Space>
                <BulbOutlined />
                <span>业务场景示例</span>
              </Space>
            </Title>
            <div style={{ 
              backgroundColor: '#f6ffed', 
              padding: '12px', 
              borderRadius: '6px',
              border: '1px solid #d9f7be'
            }}>
              {businessScenarios[currentStepData.title]?.map((scenario: BusinessScenario, index: number) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  gap: '8px',
                  marginBottom: index < (businessScenarios[currentStepData.title]?.length || 0) - 1 ? '12px' : '0'
                }}>
                  <div style={{ color: '#52c41a', marginTop: '2px' }}>
                    {scenario.icon}
                  </div>
                  <div>
                    <Text strong style={{ fontSize: '13px', color: '#389e0d' }}>
                      {scenario.scenario}
                    </Text>
                    <br />
                    <Text style={{ fontSize: '12px', lineHeight: '1.4', color: '#666' }}>
                      {scenario.description}
                    </Text>
                  </div>
                </div>
              ))}
            </div>
          </div>        
        </Card>

        {/* 进度指示器 */}
        <div style={{ 
          marginTop: '20px',
          padding: '12px',
          backgroundColor: '#fafafa',
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <Text style={{ fontSize: '12px', color: '#666' }}>
            进度：{completedSteps.length} / {analysisSteps.length} 步骤已完成
          </Text>
          <div style={{ 
            width: '100%', 
            height: '4px', 
            backgroundColor: '#f0f0f0', 
            borderRadius: '2px',
            marginTop: '8px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${(completedSteps.length / analysisSteps.length) * 100}%`,
              height: '100%',
              backgroundColor: '#52c41a',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      </div>
      <DataAnalysisKnowledge
        visible={knowledgeDrawerVisible}
        onClose={() => setKnowledgeDrawerVisible(false)}
      />
    </Drawer>
  );
};

export default AnalysisGuide;
