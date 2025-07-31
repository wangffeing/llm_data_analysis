import React, { useState, useRef, useEffect } from 'react';
import {
  Drawer,
  Typography,
  Collapse,
  Card,
  Steps,
  Space,
  List,
  Divider,
} from 'antd';
import {
  QuestionCircleOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  UploadOutlined,
  MessageOutlined,
  SettingOutlined,
  PlusOutlined,
  BulbOutlined,
  LineChartOutlined,
  SyncOutlined,
  SearchOutlined,
  EyeOutlined,
  RocketOutlined,
  NodeIndexOutlined,
  ExclamationCircleOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import { Welcome } from '@ant-design/x';
import logo from '../resource/logo1.png';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;

// 1. [优化] 为帮助数据定义清晰的 TypeScript 类型，增强代码健壮性
interface HelpContent {
  category: string;
  icon: React.ReactNode;
  items: string[];
}

interface HelpSection {
  title: string;
  icon: React.ReactNode;
  description: string;
  content: HelpContent[];
  tips: string[];
}

interface HelpGuideProps {
  visible: boolean;
  onClose: () => void;
}

const HelpGuide: React.FC<HelpGuideProps> = ({ visible, onClose }) => {
  const [activeStep, setActiveStep] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);

  // 功能介绍与帮助数据 (保持在组件内部)
  const helpSections: HelpSection[] = [
    {
      title: '快速开始',
      icon: <RocketOutlined />,
      description: '了解如何快速开始使用数据分析助手。',
      content: [
        {
          category: '第一步：选择数据源',
          icon: <DatabaseOutlined />,
          items: [
            '点击左侧边栏底部的"选择数据源"按钮。',
            '在弹出的对话框中选择已有数据源，或点击"管理数据源"创建新的数据源。',
            '选择后，数据源信息会显示在按钮上。',
          ],
        },
        {
          category: '第二步：开始分析',
          icon: <MessageOutlined />,
          items: [
            '在底部输入框中描述您的分析需求。',
            '或点击"选择分析模板"使用预定义模板。',
            '也可以直接上传文件进行分析。',
            '点击发送按钮开始AI分析。',
          ],
        },
        {
          category: '第三步：查看结果',
          icon: <LineChartOutlined />,
          items: [
            'AI会实时显示分析思维过程。',
            '查看生成的图表和数据表格。',
            '可以继续提问进行深入分析。',
            '点击"生成报告"获取完整分析报告。',
          ],
        },
      ],
      tips: [
        '建议先熟悉数据源的结构和字段含义。',
        '可以从简单的描述性分析开始。',
        '善用分析模板可以快速获得专业分析。',
      ],
    },
    {
      title: '数据源管理',
      icon: <DatabaseOutlined />,
      description: '学习如何管理和配置您的数据源。',
      content: [
        {
          category: '选择与管理',
          icon: <SettingOutlined />,
          items: [
            '在"选择数据源"对话框中，可以搜索、查看和选择已有的数据源。',
            '点击"管理数据源"进入管理界面，可以编辑或删除现有数据源。',
          ],
        },
        {
          category: '创建新数据源',
          icon: <PlusOutlined />,
          items: [
            '在管理界面点击"新增数据源"按钮。',
            '填写数据源名称、表名和详细描述。',
            '配置表字段和其中文名称的映射关系，这对于AI理解至关重要。',
          ],
        },
      ],
      tips: [
        '数据源名称要简洁明了，便于识别。',
        '详细的描述信息有助于AI更准确地理解数据。',
        '字段映射要准确，直接影响分析质量。',
      ],
    },
    {
      title: '文件上传',
      icon: <UploadOutlined />,
      description: '了解如何上传本地文件并进行快速分析。',
      content: [
        {
          category: '支持的文件格式',
          icon: <FileTextOutlined />,
          items: [
            'CSV格式文件（逗号分隔值）。',
            'Excel格式文件（.xlsx, .xls）。',
            'JSON格式文件（结构化数据）。',
            '提示：文件大小限制为 10MB。',
          ],
        },
        {
          category: '上传与预览',
          icon: <UploadOutlined />,
          items: [
            '点击输入框左侧的附件图标，或直接拖拽文件到输入区。',
            '上传后系统会自动预览文件的前几行数据。',
            '检查列名和数据类型，确认无误后即可开始分析对话。',
          ],
        },
      ],
      tips: [
        '请确保文件编码为UTF-8，以避免中文乱码。',
        '文件的第一行应该是列名（表头）。',
        '数据内容应规整，尽量避免空行和合并单元格。',
      ],
    },
    // // 2. [补全] 将缺失的“分析模板”模块重新添加回来
    // {
    //   title: '分析模板',
    //   icon: <BookOutlined />,
    //   description: '使用预定义模板快速开始专业分析。',
    //   content: [
    //     {
    //       category: '选择模板',
    //       icon: <FileTextOutlined />,
    //       items: [
    //         '点击"选择分析模板"按钮。',
    //         '浏览可用的分析模板列表，如“用户行为分析”、“销售趋势分析”等。',
    //         '系统会根据您当前选择的数据源，计算模板的兼容性。',
    //       ],
    //     },
    //     {
    //       category: '模板兼容性',
    //       icon: <BulbOutlined />,
    //       items: [
    //         '绿色"兼容"标签表示数据源包含模板所需的所有关键字段。',
    //         '橙色"需调整"表示部分匹配，会提示缺少的必需字段。',
    //         '匹配度百分比直观显示模板的适用程度。',
    //       ],
    //     },
    //     {
    //       category: '使用模板',
    //       icon: <RocketOutlined />,
    //       items: [
    //         '选择模板后会自动生成一段专业的分析提示语。',
    //         '该提示语会根据您的数据进行定制。',
    //         '您可以在生成的提示基础上进行修改，然后点击发送开始模板化分析。',
    //       ],
    //     },
    //   ],
    //   tips: [
    //     '选择与数据最匹配的模板效果最好。',
    //     '模板是高效分析的起点，您可以随时在对话中自由扩展分析范围。',
    //   ],
    // },
    {
      title: '智能对话',
      icon: <MessageOutlined />,
      description: '掌握与AI进行有效数据分析对话的技巧。',
      content: [
        {
          category: '提问技巧示例 (正反对比)',
          icon: <QuestionCircleOutlined />,
          items: [
            '❌ (模糊): "分析一下我的数据。"',
            '✅ (清晰): "使用柱状图，按月度分析2024年每个产品的销售总额。"',
            '❌ (宽泛): "用户怎么样？"',
            '✅ (具体): "找出上个季度流失用户的共同特征，并分析他们主要集中在哪些城市。"',
            '✅ (指定图表): "绘制散点图，分析广告投入和收入之间的关系。"',
          ],
        },
        {
          category: '提问技巧进阶',
          icon: <BulbOutlined />,
          items: [
            '🎯 **SMART原则**: 提问要具体(Specific)、可衡量(Measurable)、可实现(Achievable)',
            '📝 **背景信息**: 提供业务背景，如"数据是通信行业客服接通率数据，想分析接通率变化"',
            '🔍 **分层提问**: 先整体概览，再深入细节，最后总结洞察',
            '📊 **指定输出**: 明确要求图表类型、数据格式或分析维度',
            '🔄 **迭代优化**: 基于初步结果继续追问，逐步深入',
          ],
        },
        {
          category: '提出好问题的艺术',
          icon: <QuestionCircleOutlined />,
          items: [
            '🎯 **从业务目标出发**："我们想提升客户满意度" → "哪些因素影响客户满意度？"',
            '📊 **可量化的问题**："销售不好" → "哪个产品线销售下降最多？"',
            '⏰ **时间维度思考**："对比去年同期" "分析最近3个月趋势"',
            '🔍 **细分维度思考**："按地区分析" "按客户类型分析"'
          ]
        },
        {
          category: '数据解读技巧',
          icon: <EyeOutlined />,
          items: [
            '📈 **看趋势不看绝对值**：关注变化方向和幅度',
            '🔄 **寻找异常和拐点**：数据突变往往有业务原因',
            '⚖️ **对比才有意义**：同比、环比、行业对比',
            '🎯 **关注业务指标**：转化率比访问量更重要'
          ]
        },
        {
          category: '高级技巧',
          icon: <RocketOutlined />,
          items: [
            '分步骤提问，引导AI逐步深入分析。',
            '可以要求AI解释它的分析方法或代码。',
            '善用追问来深入挖掘数据背后的洞察。',
          ],
        },
      ],
      tips: [
        '问题越具体，得到的答案越准确。',
        '像与真人分析师对话一样提供背景信息。',
        '如果结果不理想，尝试换一种方式提问。',
      ],
    },
    {
      title: '会话配置',
      icon: <SettingOutlined />,
      description: '了解如何配置和管理您的分析会话。',
      content: [
        {
          category: '会话管理',
          icon: <PlusOutlined />,
          items: [
            '点击"新建会话"按钮创建新对话，每个会话都有独立的上下文记忆。',
          ],
        },
        {
          category: '思维链模式',
          icon: <NodeIndexOutlined />,
          items: [
            '🧠 **完整思维链**: 显示AI的完整分析思路和代码执行过程，更好地理解AI的分析逻辑。',
            '⚡ **简化模式**: 只显示最终步骤，适合快速查看结果',
            '📊 **可视化思维**: 以流程图形式展示分析逻辑',
          ],
        },
        {
          category: '高级配置',
          icon: <SyncOutlined />,
          items: [
            '在"会话配置"中，可以选择不同的工作模式，如完整模式或纯代码模式。',
            '可以配置使用的大语言模型（LLM）及其参数。',
            '可以配置允许的Python模块，来完成特定的任务。# 数据处理 [pandas, numpy, scipy]\# 可视化[matplotlib, seaborn, plotly, bokeh]、# 机器学习[sklearn, statsmodels]、# 文件处理[openpyxl, xlrd, json]、# 其他工具[datetime, typing, requests]',
          ],
        },
      ],
      tips: [
        '建议为不同的分析任务使用独立的会话。',
        '复杂的分析任务建议使用"完整模式"。',
        '保留思维链有助于学习和复现分析方法。',
      ],
    },
    // 在helpSections数组中添加新的分析实例章节
    {
      title: '分析实例',
      icon: <LineChartOutlined />,
      description: '通过具体实例学习如何进行各种类型的数据分析。',
      content: [
        {
          category: '数据库取数实例',
          icon: <DatabaseOutlined />,
          items: [
            '🔄 **快速取数**: 在"会话配置"中，选择"纯代码解释器"工作模式，描述取数任务来完成快速取数。"',
            '📊 **基础取数**: "请查询2024年1-6月所有产品的销售数据，按月份和产品类别分组"',
            '🔍 **条件筛选**: "筛选出销售额大于10万且客户满意度高于4分的订单记录"',
            '📈 **排序取数**: "按销售额降序排列，显示前20名销售人员的业绩数据"',
            '🎯 **聚合统计**: "计算每个地区的平均客单价、订单总数和客户留存率"',
            '⏰ **时间范围**: "提取最近30天内新注册用户的基本信息和行为数据"',
          ],
        },
        {
          category: '上传数据准备最佳实践',
          icon: <DatabaseOutlined />,
          items: [
            '📋 **数据清洗**: 上传前检查数据完整性，处理缺失值和异常值',
            '📝 **字段命名**: 使用有意义的列名，避免特殊字符和空格',
            '📊 **数据格式**: 确保日期、数字格式统一，便于AI理解',
            '🏷️ **数据标注**: 为关键字段添加清晰的中文描述',
            '📈 **数据量**: 建议单次分析数据量控制在合理范围（<10M）',
          ],
        },
        {
          category: '分析方法速查:我想了解现状',
          icon: <EyeOutlined />,
          items: [
            '📊 **描述性分析**："当前销售额是多少？" "客户分布如何？"',
            '📈 **趋势分析**："销售额如何变化？" "用户增长趋势？"',
            '🔍 **对比分析**："哪个地区表现最好？" "产品间差异？"'
          ]
        },
        {
          category: '分析方法速查:我想知道原因',
          icon: <SearchOutlined />,
          items: [
            '🎯 **归因分析**："销售下降的原因？" "客户流失的原因？"',
            '📊 **相关性分析**："广告投入与销售的关系？"',
            '🔄 **漏斗分析**："用户在哪个环节流失最多？"'
          ]
        },
        {
          category: '数据波动分析',
          icon: <LineChartOutlined />,
          items: [
            '📉 **趋势分析**: "绘制折线图分析过去12个月的月度销售趋势，识别季节性规律"',
            '⚡ **异常检测**: "找出销售数据中的异常波动点，分析可能的原因"',
            '📊 **同比环比**: "计算各产品线的同比增长率和环比变化率"',
            '🎢 **波动幅度**: "分析股价/销量的波动幅度，计算标准差和变异系数"',
            '🔄 **周期性分析**: "识别数据中的周期性模式，如周、月、季度规律"',
          ],
        },
        {
          category: '归因分析',
          icon: <BulbOutlined />,
          items: [
            '🎯 **销售下滑归因**: "分析Q3销售额下降15%的主要原因，从产品、渠道、地区等维度分解"',
            '👥 **用户流失归因**: "找出导致用户流失率上升的关键因素，分析用户行为路径"',
            '💰 **成本上升归因**: "分析运营成本增加的具体原因，识别主要成本驱动因素"',
            '📱 **转化率下降归因**: "从流量来源、页面表现、用户特征等角度分析转化率下降原因"',
            '⭐ **满意度变化归因**: "分析客户满意度评分变化的影响因素和改进建议"',
          ],
        },
        {
          category: '对比分析',
          icon: <SyncOutlined />,
          items: [
            '🏆 **产品对比**: "对比不同产品线的盈利能力、市场份额和增长潜力"',
            '🌍 **地区对比**: "比较华北、华南、华东三个大区的销售表现和客户特征"',
            '📅 **时期对比**: "对比疫情前后的业务数据变化，识别影响和机会"',
            '👥 **群体对比**: "分析新老客户在购买行为、偏好和价值方面的差异"',
            '📊 **渠道对比**: "比较线上线下渠道的效率、成本和客户满意度"',
          ],
        },
        {
          category: '预测分析',
          icon: <RocketOutlined />,
          items: [
            '📈 **销售预测**: "基于历史数据预测下季度各产品的销售额，并给出置信区间"',
            '👤 **客户预测**: "预测哪些客户在未来30天内可能流失，计算流失概率"',
            '📦 **库存预测**: "根据销售趋势和季节性因素预测各商品的库存需求"',
            '💹 **趋势预测**: "预测关键业务指标的未来走势，识别潜在风险和机会"',
            '🎯 **目标预测**: "基于当前进度预测是否能完成年度销售目标"',
          ],
        },
      ],
      tips: [
        '实际分析时，建议先从简单的任务开始，逐步深入到复杂分析，好的数据分析是一个迭代过程，不要期望一次就得到完美结果。',
        '每种分析类型都可以结合多个维度，获得更全面的洞察。',
        '善用可视化图表，让分析结果更直观易懂。',
        '始终保持对数据的敏感性，质疑异常的分析结果。',
        '分析完成后，记得总结关键发现和行动建议，将技术分析转化为业务洞察是数据分析的最终目标。',
      ],
    },
    {
      title: '常见问题',
      icon: <QuestionCircleOutlined />,
      description: '解决您在使用过程中可能遇到的常见问题。',
      content: [
        {
          category: '文件上传失败|文件分析错误怎么办？',
          icon: <UploadOutlined />,
          items: [
            '请检查文件格式是否为支持的 CSV, XLSX  或 JSON.',
            '请确认文件大小没有超过 10MB 的限制。',
            '如果文件包含中文，请确保其编码为 UTF-8。如有中文乱码， 请检查字符集设置、是否存在特殊字符',
            '尝试清理数据，对EXCEL文件，请确保**移除文件中的空行或拆分合并的单元格，保证第一行为列名**。',
          ],
        },
        {
          category: 'AI 分析结果不理想|分析报错？',
          icon: <BulbOutlined />,
          items: [
            '分析步骤中显示"代码执行失败"为正常现象，“数据问题|AI生成的代码问题"都可能会导致代码执行失败，系统会自动读取失败报错并重新生成。',
            '尝试更具体、更明确地描述您的分析需求（参考“智能对话”、“分析实例”、“数据分析方法与模型”中的技巧）。',
            '请检查在数据源管理中，字段的描述和映射是否准确。',
            '可以尝试分步骤提问，引导 AI 进行更深入的探索。',
            '在“会话配置”中，您可以尝试更换 LLM 模型或调整参数。',
          ],
        },
        {
          category: '数据问题',
          icon: <ExclamationCircleOutlined />,
          items: [
            '❌ **数据格式错误**: 检查CSV分隔符、Excel工作表、JSON结构',
            '❌ **sql取数错误**: 检查“数据源管理”中表字段设置是否正确，表字段和字段中文名是否一致，表的描述是否清晰',
            '🔤 **中文乱码**: 确保文件编码为UTF-8、检查字符集设置',
            '📊 **图表显示异常**: 检查数据类型、代码执行和报错，如无问题请尝试在提示中添加"不使用antd插件，直接使用seaborn生成图表",当前AI自动生成的图表可能会有问题。',
            '🔍 **查询结果为空**: 检查筛选条件、数据范围、字段名称',
          ],
        },
        {
          category: '性能问题',
          icon: <DashboardOutlined />,
          items: [
            '🐌 **分析速度慢**: 数据分析助手有大量上下文提示和多智能体交互，分析速度慢为正常现象，可尝试选择更快的模型|限制会话角色来尝试加速',
          ],
        },
      ],
      tips: [
        'AI生成的結果不稳定，遇到问题时，请先尝试刷新页面或新建会话。',
        '保存重要的分析结果，避免意外丢失。',
        '详细的数据描述和清晰的提问是获得高质量分析结果的关键。',],
    },
  ];

  const handleStepClick = (stepIndex: number) => {
    setActiveStep(stepIndex);
  };

  useEffect(() => {
    if (visible && contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [activeStep, visible]);

  const currentSection = helpSections[activeStep];

  return (
    <Drawer
      title={
        <Space>
          <QuestionCircleOutlined style={{ color: '#1677ff' }} />
          <span>功能帮助指南</span>
        </Space>
      }
      open={visible}
      onClose={onClose}
      width={900}
      styles={{
        body: { padding: '16px', backgroundColor: '#f7f8fa' },
      }}
    >
      <div style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#fff', borderRadius: '8px' }}>
        <Welcome
          variant="borderless"
          icon={<img src={logo} alt="Logo" style={{ width: 64, height: 64 }} />}
          title="欢迎使用智能数据分析助手"
          description="本指南将帮助您快速掌握各项功能，让您的数据分析工作更加高效、智能。"
        />
      </div>

      <Card title="功能导航" bordered={false} style={{ marginBottom: '6px' }}>
        <Steps
          current={activeStep}
          type="navigation"
          size="small"
          onChange={handleStepClick}
          items={helpSections.map((section) => ({
            key: section.title,
            title: section.title,
            icon: section.icon,
          }))}
        />
      </Card>

      <div ref={contentRef}>
        <Card
          bordered={false}
          title={
            <Space size="middle">
              {currentSection.icon}
              <Title level={5} style={{ margin: 0 }}>
                {currentSection.title}
              </Title>
            </Space>
          }
        >
          <Paragraph type="secondary">{currentSection.description}</Paragraph>

          <Collapse defaultActiveKey={[0]} accordion ghost>
            {currentSection.content.map((item, index) => (
              <Panel
                key={index}
                header={
                  <Space>
                    {item.icon}
                    <Text strong>{item.category}</Text>
                  </Space>
                }
              >
                <List
                  size="small"
                  dataSource={item.items}
                  renderItem={(listItem) => (
                    <List.Item style={{ border: 'none', padding: '4px 0' }}>
                      <List.Item.Meta
                        avatar={
                          <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#1677ff', marginTop: '9px' }} />
                        }
                        title={<Typography.Paragraph style={{ margin: 0, fontWeight: 'normal' }}>{listItem}</Typography.Paragraph>}

                        // title={<Text>{listItem}</Text>}
                      />
                    </List.Item>
                  )}
                />
              </Panel>
            ))}
          </Collapse>

          <Divider orientation="left" dashed style={{ marginTop: '16px' }}>
            <Space>
              <BulbOutlined style={{ color: '#faad14' }} />
              <Text strong>小贴士</Text>
            </Space>
          </Divider>

          <Space direction="vertical" size="small">
            {currentSection.tips.map((tip, index) => (
              <Text key={index} type="secondary">
                • {tip}
              </Text>
            ))}
          </Space>
        </Card>
      </div>
    </Drawer>
  );
};

export default HelpGuide;