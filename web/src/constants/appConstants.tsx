import {
  AppstoreAddOutlined,
  LineChartOutlined,
  FileSearchOutlined,
  FundProjectionScreenOutlined,
  FileDoneOutlined,
  ProductOutlined,
  ScheduleOutlined,
  FunnelPlotOutlined,
} from '@ant-design/icons';
import { type GetProp } from 'antd';
import { Prompts } from '@ant-design/x';

// 扩展 Prompts 的类型定义，添加自定义字段
export type ExtendedPromptItem = GetProp<typeof Prompts, 'items'>[0] & {
  prompt?: string;
  category?: string;
  level?: string;
  tags?: string[];
};

export const DEFAULT_CONVERSATIONS_ITEMS = [
  // 移除默认项，让应用启动时自动创建
];

export const HOT_TOPICS = {
  key: '1',
  label: '快速开始',
  children: [
    {
      key: '1-1',
      description: '选择数据源开始分析',
      icon: <span style={{ color: '#1677ff', fontWeight: 700 }}>1</span>,
      action: 'select_datasource'
    },
    {
      key: '1-2', 
      description: '上传文件进行分析',
      icon: <span style={{ color: '#52c41a', fontWeight: 700 }}>2</span>,
      action: 'upload_file'
    },
    {
      key: '1-3',
      description: '查看数据源管理',
      icon: <span style={{ color: '#ff8f1f', fontWeight: 700 }}>3</span>,
      action: 'manage_datasource'
    },
    {
      key: '1-4',
      description: '使用分析模板',
      icon: <span style={{ color: '#f93a4a', fontWeight: 700 }}>4</span>,
      action: 'select_template'
    },
    {
      key: '1-5',
      description: '查看分析指南',
      icon: <span style={{ color: '#722ed1', fontWeight: 700 }}>5</span>,
      action: 'show_guide'
    },
  ],
};
export const DESIGN_GUIDE = {
  key: '2',
  label: '分析指南',
  children: [
    {
      key: '2-1',
      icon: <ScheduleOutlined />,
      label: '数据概览与诊断',
      description: '全面了解数据现状并诊断问题，回答"发生了什么？为什么会发生？"',
    },
    {
      key: '2-2',
      icon: <ProductOutlined />,
      label: '关系与相关性分析',
      description: '探索变量间的关系和相关性，回答"变量间是什么关系？"',
    },
    {
      key: '2-3',
      icon: <LineChartOutlined />,
      label: '趋势与对比分析',
      description: '分析时间趋势和对比模式，回答"如何变化？"',
    },
    {
      key: '2-4',
      icon: <AppstoreAddOutlined />,
      label: '预测性分析',
      description: '基于数据预测未来趋势，回答"将要发生什么？"',
    },
    {
      key: '2-5',
      icon: <FundProjectionScreenOutlined />,
      label: '决策建议与可视化',
      description: '提供决策建议和可视化展示，回答"应该做什么？"',
    },
  ],
};

export const SENDER_PROMPTS: ExtendedPromptItem[] = [
  {
    key: '1',
    description: '数据概览与诊断',
    icon: <ScheduleOutlined />,
    prompt: '请对当前数据集进行全面的概览分析和诊断，回答"发生了什么？为什么会发生？"包括：1）数据维度、数据类型、缺失值情况、基本统计信息；2）识别数据中的异常模式和问题；3）分析可能的影响因素和驱动因素。'
  },
  {
    key: '2',
    description: '关系与相关性分析',
    icon: <ProductOutlined />,
    prompt: '请进行变量关系分析，回答"变量间是什么关系？"包括：1）计算变量间的相关系数和显著性检验；2）识别强相关和弱相关关系；3）通过回归分析等方法探索因果关系；4）构建变量关系图谱。'
  },
  {
    key: '3',
    description: '趋势与对比分析',
    icon: <LineChartOutlined />,
    prompt: '请进行趋势与对比分析，回答"如何变化？"包括：1）时间序列趋势分析，识别上升、下降或周期性模式；2）不同时期、不同群体或不同条件下的对比分析；3）季节性和周期性特征识别；4）变化率和增长率计算。'
  },
  {
    key: '4',
    description: '预测性分析',
    icon: <AppstoreAddOutlined />,
    prompt: '请进行预测性分析，回答"将要发生什么？"包括：1）基于历史数据构建预测模型（时间序列、回归、机器学习等）；2）预测未来趋势和可能的结果；3）评估预测模型的准确性和可靠性；4）提供不同情景下的预测结果。'
  },
  {
    key: '5',
    description: '决策建议与可视化',
    icon: <FundProjectionScreenOutlined />,
    prompt: '请基于分析结果提供决策建议和可视化展示，回答"应该做什么？"包括：1）提供具体的行动建议和决策方案；2）制定优化策略和改进措施；3）创建合适的可视化图表展示关键发现；4）评估不同方案的成本效益和风险。'
  },
];

export const UI_CONSTANTS = {
  SIDER_WIDTH: 280,
  MAX_SENDER_WIDTH: 1800,
  DEFAULT_TABLE_HEIGHT: 400,
  SCROLL_DELAY: 100,
  RETRY_DELAY: 1000
};