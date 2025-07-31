import axios from 'axios';
import type { DataSource, TaskWeaverConfig, ConfigOptions, ConfigUpdateRequest } from '../types/appTypes';
import { Template } from '../types/template';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.response?.data);
    
    if (error.response?.status === 404) {
      throw new Error('请求的资源不存在 (404)');
    } else if (error.response?.status === 500) {
      throw new Error('服务器内部错误 (500)');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('请求超时');
    } else {
      throw new Error(error.response?.data?.detail || '网络或未知错误');
    }
  }
);


interface SessionResponse {
  session_id: string;
  created_at: string;
  conversation_id: string;
}

interface MessageResponse {
  success: boolean;
  message: string;
  data?: any;
}

interface DataSourcesResponse {
  data_sources: DataSource[];
}

interface DataPreviewResponse {
  source_name: string;
  columns: string[];
  data: any[][];
  total_shown: number;
}

interface HeartbeatResponse {
  status: string;
  session_id: string;
  timestamp: string;
}

// ==================== API Service ====================
// 添加配置相关的响应类型
interface ConfigResponse {
  success: boolean;
  config: TaskWeaverConfig;
}

interface ConfigUpdateResponse {
  success: boolean;
  message: string;
}

// 更新 API 方法的返回类型
// 添加数据源管理相关的接口
interface DataSourceCreateRequest {
  name: string;
  table_name: string;
  table_des: string;
  table_order: string;
  table_columns: string[];
  table_columns_names: string[];
}

interface DataSourceUpdateRequest {
  table_name: string;
  table_des: string;
  table_order: string;
  table_columns: string[];
  table_columns_names: string[];
}


interface TemplatePromptResponse {
  success: boolean;
  prompt: string;
}


interface TemplateResponse {
  templates: Template[];
}

interface TemplateDetailResponse {
  success: boolean;
  template: Template;
}



interface ReportGenerationRequest {
  analysis_results: any;
  template_id?: string;
  config: {
    include_executive_summary: boolean;
    include_detailed_analysis: boolean;
    include_recommendations: boolean;
    language: string;
  };
}

interface ReportResponse {
  success: boolean;
  report: string;
  metadata: {
    generated_at: string;
    analysis_type: string;
    data_range: string;
  };
}

export const apiService = {
  
  // 健康检查
  healthCheck: (): Promise<any> => apiClient.get('/health'),
  
  // 数据源相关
  getDataSources: (): Promise<DataSourcesResponse> => apiClient.get('/api/data/sources'),
  getDataPreview: (sourceName: string, limit: number = 10): Promise<DataPreviewResponse> => 
    apiClient.get(`/api/data/sources/${sourceName}/preview?limit=${limit}`),

  // 会话相关
  createSession: (): Promise<SessionResponse> => apiClient.post('/api/session/create'),
  getSession: (sessionId: string): Promise<any> => apiClient.get(`/api/session/${sessionId}`),
  deleteSession: (sessionId: string): Promise<MessageResponse> => apiClient.delete(`/api/session/${sessionId}`),
  sessionHeartbeat: (sessionId: string): Promise<HeartbeatResponse> => 
    apiClient.post(`/api/session/${sessionId}/heartbeat`),
  
  // 消息相关
  getMessages: (sessionId: string): Promise<any> => 
    apiClient.get(`/api/chat/history/${sessionId}/messages`),

  // 文件上传相关
  uploadFiles: (files: File[]): Promise<any> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    return axios.post(`${API_BASE_URL}/api/files/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    }).then(response => response.data); // ✅ 确保返回正确的数据结构
  },
  
  // 发送聊天消息
  sendChatMessage: (sessionId: string, message: { 
    content: string; 
    selected_table?: string;
    uploaded_files?: any[];
    template_id?: string;
  }): Promise<any> => 
    apiClient.post(`/api/chat/message/${sessionId}`, message),

  // 配置相关API - 添加明确的返回类型
  getSessionConfig: (sessionId: string): Promise<ConfigResponse> => 
    apiClient.get(`/api/config/session/${sessionId}`),
  
  updateSessionConfig: (sessionId: string, config: any): Promise<ConfigUpdateResponse> => 
    apiClient.put(`/api/config/session/${sessionId}`, config),
  
  updateSessionRoles: (sessionId: string, roles: string[]): Promise<ConfigUpdateResponse> => 
    apiClient.put(`/api/config/session/${sessionId}/roles`, { roles }),
  
  updateSessionLLM: (sessionId: string, llmConfig: any): Promise<ConfigUpdateResponse> => 
    apiClient.put(`/api/config/session/${sessionId}/llm`, llmConfig),
  
  updateSessionModules: (sessionId: string, modules: string[]): Promise<ConfigUpdateResponse> => 
    apiClient.put(`/api/config/session/${sessionId}/modules`, { modules }),

  getAvailableModels: (): Promise<{success: boolean, models: string[]}> => 
    apiClient.get('/api/config/options/models'),
  
  getAvailableRoles: (): Promise<{success: boolean, roles: string[]}> => 
    apiClient.get('/api/config/options/roles'),
  
  getAvailableModules: (): Promise<{success: boolean, modules: string[]}> => 
    apiClient.get('/api/config/options/modules'),

  // 数据源管理相关
  createDataSource: (data: DataSourceCreateRequest): Promise<{success: boolean, message: string}> => 
    apiClient.post('/api/data/sources', data),
  
  updateDataSource: (sourceName: string, data: DataSourceUpdateRequest): Promise<{success: boolean, message: string}> => 
    apiClient.put(`/api/data/sources/${sourceName}`, data),
  
  deleteDataSource: (sourceName: string): Promise<{success: boolean, message: string}> => 
    apiClient.delete(`/api/data/sources/${sourceName}`),
  
  // 模板相关API
  getAnalysisTemplates: (): Promise<TemplateResponse> => 
    apiClient.get('/api/templates/analysis'),
  
  generateTemplatePrompt: (templateId: string, dataColumns: string[]): Promise<TemplatePromptResponse> => 
    apiClient.post('/api/templates/generate-prompt', {
      template_id: templateId,
      data_columns: dataColumns
    }),
  
  // 添加自定义模板
  addCustomTemplate: (templateId: string, templateConfig: any): Promise<{success: boolean, message: string}> => 
    apiClient.post('/api/templates/custom', {
      template_id: templateId,
      template_config: templateConfig
    }),

  // 更新自定义模板
  updateCustomTemplate: (templateId: string, templateConfig: any): Promise<{success: boolean, message: string}> => 
    apiClient.put(`/api/templates/custom/${templateId}`, {
      template_config: templateConfig
    }),
  
  // 删除自定义模板
  deleteCustomTemplate: (templateId: string): Promise<{success: boolean, message: string}> => 
    apiClient.delete(`/api/templates/custom/${templateId}`),
  
  // 获取模板详情
  getTemplateDetail: (templateId: string): Promise<TemplateDetailResponse> => 
    apiClient.get(`/api/templates/template/${templateId}`),
  
  // 智能报告生成API
  generateIntelligentReport: (request: ReportGenerationRequest): Promise<ReportResponse> => 
    apiClient.post('/api/reports/generate', request),
  
};