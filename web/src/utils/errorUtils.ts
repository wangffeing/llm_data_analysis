// 移除直接导入message
// import { message } from 'antd';

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  PERMISSION = 'PERMISSION',
  SERVER = 'SERVER',
  UNKNOWN = 'UNKNOWN'
}

/**
 * 自定义错误类
 */
export class AppError extends Error {
  public type: ErrorType;
  public code?: string;
  public details?: any;

  constructor(
    message: string, 
    type: ErrorType = ErrorType.UNKNOWN, 
    code?: string, 
    details?: any
  ) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.code = code;
    this.details = details;
  }
}

/**
 * 错误处理函数
 * @param error 错误对象
 * @param context 错误上下文
 * @param messageApi message API实例
 */
export const handleError = (error: any, context?: string, messageApi?: any) => {
  console.error(`Error in ${context || 'Unknown'}:`, error);
  
  let errorMessage = '发生未知错误';
  
  if (error instanceof AppError) {
    errorMessage = error.message;
  } else if (error?.response?.data?.detail) {
    errorMessage = error.response.data.detail;
  } else if (error?.message) {
    errorMessage = error.message;
  }
  
  // 只有在提供了messageApi时才显示提示
  if (messageApi) {
    // 根据错误类型显示不同的提示
    if (error instanceof AppError) {
      switch (error.type) {
        case ErrorType.NETWORK:
          messageApi.error('网络连接失败，请检查网络设置');
          break;
        case ErrorType.PERMISSION:
          messageApi.error('权限不足，请联系管理员');
          break;
        case ErrorType.VALIDATION:
          messageApi.warning(errorMessage);
          break;
        case ErrorType.SERVER:
          messageApi.error('服务器错误，请稍后重试');
          break;
        default:
          messageApi.error(errorMessage);
      }
    } else {
      messageApi.error(errorMessage);
    }
  }
};

/**
 * 异步函数错误包装器
 * @param fn 异步函数
 * @param context 错误上下文
 * @param messageApi message API实例
 * @returns 包装后的函数
 */
export const withErrorHandling = <T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  context?: string,
  messageApi?: any
) => {
  return async (...args: T): Promise<R | undefined> => {
    try {
      return await fn(...args);
    } catch (error) {
      handleError(error, context, messageApi);
      return undefined;
    }
  };
};

/**
 * 创建网络错误
 * @param message 错误消息
 * @param code 错误代码
 * @returns AppError实例
 */
export const createNetworkError = (message: string, code?: string): AppError => {
  return new AppError(message, ErrorType.NETWORK, code);
};

/**
 * 创建验证错误
 * @param message 错误消息
 * @param details 错误详情
 * @returns AppError实例
 */
export const createValidationError = (message: string, details?: any): AppError => {
  return new AppError(message, ErrorType.VALIDATION, undefined, details);
};