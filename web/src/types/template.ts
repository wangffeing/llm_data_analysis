export interface TemplateMetadata {
  id: string;
  name: string;
  summary: string;
}

export interface DataColumn {
  name: string;
  type: string;
  description: string;
}

export interface DataSchema {
  required_columns: DataColumn[];
  optional_columns: DataColumn[];
}

export interface ExecutionStep {
  prompt: string;
  save_to_variable?: string;
}

export interface ExecutionPlan {
  analysis_goal: string;
  steps: ExecutionStep[];
}

// 修复：支持后端的实际数据结构
export interface OutputFile {
  type: string;
  title: string;
  source_variable: string;
  tool: string;
}

export interface OutputSpecification {
  insights_template: string | string[]; // 支持字符串或字符串数组
  files: (string | OutputFile)[]; // 支持字符串或对象数组
}

export interface Template {
  template_metadata: TemplateMetadata;
  data_schema: DataSchema;
  execution_plan: ExecutionPlan;
  output_specification: OutputSpecification;
}