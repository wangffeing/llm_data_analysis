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
  label: '客服数据分析热点',
  children: [
    {
      key: '1-1',
      description: '机器学习模型选择指南',
      icon: <span style={{ color: '#f93a4a', fontWeight: 700 }}>1</span>,
    },
    {
      key: '1-2',
      description: '客户投诉分类与根因挖掘',
      icon: <span style={{ color: '#ff6565', fontWeight: 700 }}>2</span>,
    },
    {
      key: '1-3',
      description: '服务质量评估与客户满意度分析',
      icon: <span style={{ color: '#ff8f1f', fontWeight: 700 }}>3</span>,
    },
    {
      key: '1-4',
      description: '客户流失预警与挽留策略',
      icon: <span style={{ color: '#52c41a', fontWeight: 700 }}>4</span>,
    },
    {
      key: '1-5',
      description: '服务质量趋势预测与改进建议',
      icon: <span style={{ color: '#1890ff', fontWeight: 700 }}>5</span>,
    },
  ],
};

export const DESIGN_GUIDE = {
  key: '2',
  label: '分析指南',
  children: [
    {
      key: '2-1',
      icon: <FundProjectionScreenOutlined />,
      label: '数据探索',
      description: '了解数据结构和特征分布',
    },
    {
      key: '2-2',
      icon: <FunnelPlotOutlined />,
      label: '客户行为洞察',
      description: '分析客户服务偏好、投诉模式、满意度影响因素等行为特征',
    },
    {
      key: '2-3',
      icon: <LineChartOutlined />,
      label: '服务质量预测',
      description: '基于历史客服数据预测服务质量趋势、客户满意度变化',
    },
    {
      key: '2-4',
      icon: <FileDoneOutlined />,
      label: '报告生成',
      description: '自动生成专业的运营分析报告和可视化仪表板',
    },
  ],
};

export const SENDER_PROMPTS: ExtendedPromptItem[] = [
  {
    key: '1',
    description: '数据概览',
    icon: <ScheduleOutlined />,
    prompt: '请对当前数据集进行全面的概览分析，包括数据维度、数据类型、缺失值情况、基本统计信息等。'
  },
  {
    key: '2',
    description: '统计分析',
    icon: <ProductOutlined />,
    prompt: '请对数据进行详细的统计分析，包括描述性统计、相关性分析、分布特征等，并提供专业的解读。'
  },
  {
    key: '3',
    description: '可视化',
    icon: <FileSearchOutlined />,
    prompt: '请为当前数据创建合适的可视化图表，包括但不限于柱状图、折线图、散点图、热力图等，帮助理解数据特征和趋势。'
  },
  {
    key: '4',
    description: '预测模型',
    icon: <AppstoreAddOutlined />,
    prompt: '请基于当前数据构建预测模型，分析可能的预测变量，推荐合适的机器学习算法，并评估模型性能。'
  },
];

export const UI_CONSTANTS = {
  SIDER_WIDTH: 280,
  MAX_SENDER_WIDTH: 1800,
  DEFAULT_TABLE_HEIGHT: 400,
  SCROLL_DELAY: 100,
  RETRY_DELAY: 1000
};