export type BubbleDataType = {
  role: string;
  content: string;
};

// 将所有接口统一到这里
export interface DataSource {
  name: string;
  type: string;
  description?: string;
  table_name?: string;
  table_des?: string;
  table_columns?: string[];
  table_columns_names?: string[];
  table_order?: string;
}

export interface ThoughtStep {
  id: string;
  title: string;
  description?: string;
  content?: string;
  status: 'wait' | 'process' | 'finish' | 'error'; // 确保包含 'error' 状态
  timestamp: string;
  role?: string;
  attachments?: Array<{
    id: string;
    type: string;
    content: string;
    is_complete: boolean;
  }>;
}

export interface FileAttachment {
  id: string;    // 添加必需的 id 字段
  name: string;
  path?: string;
  type: string;
  content?: string;
  mime_type?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  status: 'sending' | 'sent' | 'delivered' | 'error' | 'streaming';
  thoughtSteps?: ThoughtStep[];
  attachments?: any[];
  dataPreview?: any;
  files?: FileAttachment[];
}

export interface AppState {
  messageHistory: Record<string, any>;
  conversations: any[];
  curConversation: string;
  attachmentsOpen: boolean;
  attachedFiles: any[];
  inputValue: string;
  dataSources: DataSource[];
  loading: boolean;
  selectedDataSource: DataSource | null;
  currentSession: string | null;
}


// 添加更严格的类型定义
export interface SSEConnectionStatus {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastConnected?: string;
  retryCount: number;
}

export interface ChatSenderProps {
  id: string;
  isLoading: boolean; // 改为必需属性
  connectionStatus: SSEConnectionStatus; // 使用更严格的类型
}


// 新增配置相关类型
export interface TaskWeaverConfig {
  "llm.api_type": string;
  "llm.model": string;
  "execution_service.kernel_mode": string;
  "code_generator.enable_auto_plugin_selection": string;
  "code_generator.allowed_plugins": string[]; // 新增插件配置
  "code_interpreter.code_verification_on": string;
  "code_interpreter.allowed_modules": string[];
  "logging.log_file": string;
  "logging.log_folder": string;
  "logging.log_level": string;
  "planner.prompt_compression": string;
  "code_generator.prompt_compression": string;
  "session.max_internal_chat_round_num": number;
  "session.roles": string[];
}

export interface ConfigOptions {
  models: string[];
  roles: string[];
  modules: string[];
  plugins: string[]; // 新增插件选项
}

export interface ConfigUpdateRequest {
  config: Partial<TaskWeaverConfig>;
}