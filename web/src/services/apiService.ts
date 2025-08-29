import axios from 'axios';
import type { DataSource, TaskWeaverConfig } from '../types/appTypes';
import { Template } from '../types/template';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 重要：允许发送 cookies
});

// 统一错误处理函数
const handleAuthError = (status: number) => {
  if (status === 401) {
    window.dispatchEvent(new CustomEvent('auth:expired'));
    sessionStorage.removeItem('user_info');
    sessionStorage.removeItem('app_code');
    sessionStorage.removeItem('user_token');
    throw new Error('登录已过期，请重新登录');
  } else if (status === 403) {
    throw new Error('权限不足，请检查用户权限');
  }
};

// 请求拦截器 - 添加用户认证头
apiClient.interceptors.request.use(
  (config) => {
    // 添加用户认证头
    const appCode = sessionStorage.getItem('app_code');
    const userToken = sessionStorage.getItem('user_token');
    
    if (appCode && userToken) {
      config.headers['X-App-Code'] = appCode;
      config.headers['X-Token'] = userToken;
    }
    
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 添加权限错误处理
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.response?.data);
    
    const status = error.response?.status;
    
    if (status === 401 || status === 403) {
      handleAuthError(status);
    } else if (status === 404) {
      // 检查是否是会话相关的404错误
      const url = error.config?.url || '';
      if (url.includes('/session/') || url.includes('/chat/')) {
        // 触发全局状态重置事件
        window.dispatchEvent(new CustomEvent('session:invalid', { 
          detail: { sessionId: url.match(/\/session\/([^\/]+)/)?.[1] }
        }));
        throw new Error('会话不存在或已过期');
      }
      throw new Error('请求的资源不存在');
    } else if (status >= 500) {
      throw new Error('服务器内部错误，请稍后重试');
    } else {
      throw new Error(error.response?.data?.detail || error.message || '请求失败');
    }
  }
);

// 判断是否是需要管理员权限的请求
function isAdminRequest(url: string, method: string): boolean {
  const adminOperations = [
    { endpoint: '/api/data/sources', methods: ['POST', 'PUT', 'DELETE'] },
    { endpoint: '/api/templates/custom', methods: ['POST', 'PUT', 'DELETE'] }
  ];
  
  return adminOperations.some(op => 
    url.includes(op.endpoint) && op.methods.includes(method.toUpperCase())
  );
}

// 接口定义
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

interface ConfigResponse {
  success: boolean;
  config: TaskWeaverConfig;
}

interface ConfigUpdateResponse {
  success: boolean;
  message: string;
}

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
  session_id: string;
  template_id?: string;
  config?: {
    include_executive_summary?: boolean;
    include_detailed_analysis?: boolean;
    include_recommendations?: boolean;
    include_appendix?: boolean;
    language?: string;
    [key: string]: any;
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

interface UserVerificationRequest {
  app_code: string;
  token: string;
}

interface UserVerificationResponse {
  success: boolean;
  message: string;
  user_id?: string;
  username?: string;
  permissions?: string[];
  expires_at?: string;
}

interface UserInfoResponse {
  success: boolean;
  user_id: string;
  username: string;
  app_code: string;
  permissions: string[];
  timestamp: string;
}

interface UserStatusResponse {
  is_logged_in: boolean;
  user_info?: {
    user_id: string;
    username: string;
    app_code: string;
    permissions: string[];
  };
  timestamp: string;
}

export const apiService = {
  // 健康检查
  healthCheck: (): Promise<any> => apiClient.get('/health'),
  
  // 管理员认证
  adminLogin: (adminKey: string): Promise<{success: boolean, message: string, expires_at: string}> => 
    apiClient.post('/api/system/admin/login', { admin_key: adminKey }),
  
  adminLogout: (): Promise<{success: boolean, message: string}> => 
    apiClient.post('/api/system/admin/logout'),
  
  getAdminStatus: (): Promise<{is_logged_in: boolean, timestamp: string}> => 
    apiClient.get('/api/system/admin/status'),
  
  // 数据源管理
  getDataSources: (): Promise<DataSourcesResponse> => apiClient.get('/api/data/sources'),
  getDataPreview: (sourceName: string, limit: number = 10): Promise<DataPreviewResponse> => 
    apiClient.get(`/api/data/sources/${sourceName}/preview?limit=${limit}`),
  
  // 会话管理
  createSession: (): Promise<SessionResponse> => apiClient.post('/api/session/create'),
  getSession: (sessionId: string): Promise<any> => apiClient.get(`/api/session/${sessionId}`),
  deleteSession: (sessionId: string): Promise<MessageResponse> => apiClient.delete(`/api/session/${sessionId}`),
  sessionHeartbeat: (sessionId: string): Promise<HeartbeatResponse> => 
    apiClient.post(`/api/session/${sessionId}/heartbeat`),
  
  // 聊天消息
  getMessages: (sessionId: string): Promise<any> => 
    apiClient.get(`/api/chat/history/${sessionId}/messages`),
  
  // 文件上传
  uploadFiles: (files: File[]): Promise<any> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    return apiClient.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // 发送聊天消息
  sendChatMessage: (sessionId: string, message: { 
    content: string; 
    selected_table?: string;
    uploaded_files?: any[];
    template_id?: string;
  }): Promise<any> => 
    apiClient.post(`/api/chat/message/${sessionId}`, message),
  
  // 配置管理
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

  getAvailableModelsByApiType: (apiType: string): Promise<{success: boolean, models: string[]}> => 
    apiClient.get(`/api/config/options/models/${apiType}`),

  getAvailableModels: (): Promise<{success: boolean, models: string[]}> => 
    apiClient.get('/api/config/options/models'),
  
  getAvailableRoles: (): Promise<{success: boolean, roles: string[]}> => 
    apiClient.get('/api/config/options/roles'),
  
  getAvailableModules: (): Promise<{success: boolean, modules: string[]}> => 
    apiClient.get('/api/config/options/modules'),
  
  // 数据源CRUD
  createDataSource: (data: DataSourceCreateRequest): Promise<{success: boolean, message: string}> => 
    apiClient.post('/api/data/sources', data),
  
  updateDataSource: (sourceName: string, data: DataSourceUpdateRequest): Promise<{success: boolean, message: string}> => 
    apiClient.put(`/api/data/sources/${sourceName}`, data),
  
  deleteDataSource: (sourceName: string): Promise<{success: boolean, message: string}> => 
    apiClient.delete(`/api/data/sources/${sourceName}`),
  
  // 模板管理
  getAnalysisTemplates: (): Promise<TemplateResponse> => 
    apiClient.get('/api/templates/analysis'),
  
  generateTemplatePrompt: (templateId: string, dataColumns: string[]): Promise<TemplatePromptResponse> => 
    apiClient.post('/api/templates/generate-prompt', {
      template_id: templateId,
      data_columns: dataColumns
    }),
  
  // 自定义模板
  addCustomTemplate: (templateId: string, templateConfig: any): Promise<{success: boolean, message: string}> => 
    apiClient.post('/api/templates/custom', {
      template_id: templateId,
      template_config: templateConfig
    }),
  
  updateCustomTemplate: (templateId: string, templateConfig: any): Promise<{success: boolean, message: string}> => 
    apiClient.put(`/api/templates/custom/${templateId}`, {
      template_config: templateConfig
    }),
  
  deleteCustomTemplate: (templateId: string): Promise<{success: boolean, message: string}> => 
    apiClient.delete(`/api/templates/custom/${templateId}`),
  
  getTemplateDetail: (templateId: string): Promise<TemplateDetailResponse> => 
    apiClient.get(`/api/templates/template/${templateId}`),
  
  // 报告生成
  generateIntelligentReport: (request: ReportGenerationRequest): Promise<ReportResponse> => 
    apiClient.post('/api/reports/generate', request),
  
  // 管理员密钥验证
  verifyAdminKey: (adminKey: string): Promise<{success: boolean, message: string}> => {
    return apiClient.post('/api/system/verify-admin', { admin_key: adminKey })
      .then(response => {
        // 修复：访问 response.data 而不是直接访问 response
        if (response.data.success) {
          return { success: true, message: '管理员密钥验证成功' };
        } else {
          return { success: false, message: response.data.message || '验证失败' };
        }
      })
      .catch(error => {
        return { success: false, message: error.message || '验证请求失败' };
      });
  }, // 修复：添加逗号
  
  // 插件管理
  updateSessionPlugins: (sessionId: string, plugins: string[]): Promise<ConfigUpdateResponse> => 
    apiClient.put(`/api/config/session/${sessionId}/plugins`, { plugins }),

  getAvailablePlugins: (): Promise<{success: boolean, plugins: string[]}> => 
    apiClient.get('/api/config/options/plugins'),
  
  // 用户验证相关
  verifyUser: (appCode: string, token: string): Promise<UserVerificationResponse> => 
    apiClient.post('/api/system/verify-user', { app_code: appCode, token }),

  getUserInfo: (): Promise<UserInfoResponse> => 
    apiClient.get('/api/system/user-info'),

  getUserStatus: (): Promise<UserStatusResponse> => 
    apiClient.get('/api/system/user-status'),

  userLogout: (): Promise<{success: boolean, message: string}> => 
    apiClient.post('/api/system/user/logout'),

  getSystemStatus: (): Promise<{user_verification_enabled: boolean}> => 
    apiClient.get('/api/system/status'),
};
