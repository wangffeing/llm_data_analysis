import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/apiService';

interface AuthState {
  isLoggedIn: boolean;
  loading: boolean;
  error: string | null;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isLoggedIn: false,
    loading: true,
    error: null
  });

  const checkAuthStatus = useCallback(async () => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }));
      const status = await apiService.getAdminStatus();
      setAuthState({
        isLoggedIn: status.is_logged_in,
        loading: false,
        error: null
      });
    } catch (error: any) {
      console.error('检查认证状态失败:', error);
      setAuthState({
        isLoggedIn: false,
        loading: false,
        error: error.message || '检查认证状态失败'
      });
    }
  }, []);

  const login = useCallback(async (adminKey: string) => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }));
      const result = await apiService.adminLogin(adminKey);
      
      if (result.success) {
        setAuthState({
          isLoggedIn: true,
          loading: false,
          error: null
        });
        return { success: true, message: result.message };
      } else {
        throw new Error(result.message || '登录失败');
      }
    } catch (error: any) {
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: error.message || '登录失败'
      }));
      return { success: false, message: error.message || '登录失败' };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      setAuthState(prev => ({ ...prev, loading: true }));
      await apiService.adminLogout();
      setAuthState({
        isLoggedIn: false,
        loading: false,
        error: null
      });
      return { success: true, message: '退出成功' };
    } catch (error: any) {
      console.error('退出失败:', error);
      // 即使退出请求失败，也更新本地状态
      setAuthState({
        isLoggedIn: false,
        loading: false,
        error: null
      });
      return { success: false, message: error.message || '退出失败' };
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();

    // 监听认证过期事件
    const handleAuthExpired = () => {
      setAuthState({
        isLoggedIn: false,
        loading: false,
        error: '登录已过期'
      });
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    
    return () => {
      window.removeEventListener('auth:expired', handleAuthExpired);
    };
  }, [checkAuthStatus]);

  return {
    ...authState,
    login,
    logout,
    refreshAuth: checkAuthStatus
  };
};