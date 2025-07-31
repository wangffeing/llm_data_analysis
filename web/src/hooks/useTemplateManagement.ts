import { useState, useCallback } from 'react';
import { App } from 'antd';
import { apiService } from '../services/apiService';
import { Template } from '../types/template';

export const useTemplateManagement = () => {
  const { message } = App.useApp();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);

  // 使用 useCallback 防止无限循环
  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getAnalysisTemplates();
      setTemplates(response.templates);
    } catch (error) {
      message.error('加载模板失败');
    } finally {
      setLoading(false);
    }
  }, [message]);

  const addTemplate = async (templateId: string, templateConfig: any) => {
    try {
      await apiService.addCustomTemplate(templateId, templateConfig);
      message.success('模板添加成功');
      await loadTemplates();
    } catch (error) {
      message.error('添加模板失败');
      throw error;
    }
  };

  const updateTemplate = async (templateId: string, templateConfig: any) => {
    try {
      await apiService.updateCustomTemplate(templateId, templateConfig);
      message.success('模板更新成功');
      await loadTemplates();
    } catch (error) {
      message.error('更新模板失败');
      throw error;
    }
  };

  const deleteTemplate = async (templateId: string) => {
    try {
      await apiService.deleteCustomTemplate(templateId);
      message.success('模板删除成功');
      await loadTemplates();
    } catch (error) {
      message.error('删除模板失败');
      throw error;
    }
  };

  return {
    templates,
    loading,
    loadTemplates,
    addTemplate,
    updateTemplate,
    deleteTemplate
  };
};