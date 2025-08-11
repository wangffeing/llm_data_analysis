import React, { memo } from 'react';
import { Button, Flex, App } from 'antd';
// 移除message导入，改用App.useApp()
// import { message } from 'antd';
import { Sender, Prompts, Attachments } from '@ant-design/x';
import { PaperClipOutlined, CloudUploadOutlined, FileTextOutlined } from '@ant-design/icons';
import { type GetProp } from 'antd';
import { type ExtendedPromptItem } from '../constants/appConstants';
import * as XLSX from 'xlsx';
import Papa from 'papaparse';

type AttachmentType = GetProp<typeof Attachments, 'items'>[0];

interface ChatSenderProps {
  inputValue: string;
  attachmentsOpen: boolean;
  attachedFiles: AttachmentType[];
  selectedDataSource: any;
  styles: any;
  senderPrompts: ExtendedPromptItem[];
  abortController: React.MutableRefObject<AbortController | null>;
  onSubmit: (value: string) => void;
  setInputValue: (value: string) => void;
  setAttachmentsOpen: (open: boolean) => void;
  setAttachedFiles: (files: AttachmentType[]) => void;
  isLoading?: boolean;
  connectionStatus?: string;
  setFilePreview?: (preview: any) => void;
  onOpenTemplateSelector?: () => void;
  messages?: any[]; // 新增
}

const ChatSender: React.FC<ChatSenderProps> = ({
  inputValue,
  attachmentsOpen,
  attachedFiles,
  selectedDataSource,
  styles,
  senderPrompts,
  abortController,
  onSubmit,
  setInputValue,
  setAttachmentsOpen,
  setAttachedFiles,
  setFilePreview,
  isLoading = false,
  connectionStatus = 'connected',
  onOpenTemplateSelector,
  messages = [], // 新增
}) => {
  const { message } = App.useApp();
  
  // 检查会话中是否已经有过文件上传的历史
  const hasUploadedFiles = messages.some(msg => msg.files && msg.files.length > 0);
  
  const handleFilePreview = async (file: File) => {
    if (!setFilePreview) return;
    
    try {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        let text;
        try {
          text = await file.text();
          if (text.includes('�')) {
            throw new Error('UTF-8 encoding failed');
          }
        } catch {
          const arrayBuffer = await file.arrayBuffer();
          const decoder = new TextDecoder('gbk');
          text = decoder.decode(arrayBuffer);
        }
        
        // 使用Papa Parse处理CSV，更好地处理引号和逗号
        const result = Papa.parse(text, {
          header: false,
          skipEmptyLines: true
        });
        
        const data = result.data as string[][];
        const previewData = data.slice(0, 6); // 前6行数据
        const headers = previewData[0] || [];
        const rows = previewData.slice(1, 6);

        setFilePreview({
          source_name: file.name,
          columns: headers,
          data: rows,
          total_shown: Math.min(5, rows.length),
          type: 'csv'
        });
      } else if (file.type.includes('sheet') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        try {
          const arrayBuffer = await file.arrayBuffer();
          const workbook = XLSX.read(arrayBuffer, { type: 'array' });
          
          // 获取第一个工作表
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];
          
          // 转换为JSON格式
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
          
          // 取前6行数据
          const data = jsonData.slice(0, 6);
          const headers = data[0] || [];
          const rows = data.slice(1, 6);
          
          setFilePreview({
            source_name: file.name,
            columns: headers,
            data: rows,
            total_shown: Math.min(5, rows.length),
            type: 'excel'
          });
        } catch (error) {
          console.error('Excel文件预览失败:', error);
          setFilePreview({
            source_name: file.name,
            columns: ['预览失败'],
            data: [['Excel文件格式错误或损坏']],
            total_shown: 1,
            type: 'excel'
          });
        }
      } else if (file.type === 'application/json') {
        const text = await file.text();
        const jsonData = JSON.parse(text);
        const preview = JSON.stringify(jsonData, null, 2).slice(0, 500);
        
        setFilePreview({
          source_name: file.name,
          columns: ['JSON内容'],
          data: [[preview]],
          total_shown: 1,
          type: 'json'
        });
      }
    } catch (error) {
      console.error('文件预览失败:', error);
      message.error('文件预览失败，请检查文件格式');
    }
  };
  
  // 修改文件上传处理
  const beforeUpload = (file: File) => {
    const isValidType = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/json'
    ].includes(file.type);
    
    if (!isValidType) {
      message.error('只支持 CSV、Excel、JSON 格式的文件');
      return false;
    }
    
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('文件大小不能超过 10MB');
      return false;
    }

    // 生成文件预览
    handleFilePreview(file);
    
    return true;
  };

  const senderHeader = (
    <Sender.Header
      title="上传文件"
      open={attachmentsOpen}
      onOpenChange={setAttachmentsOpen}
      styles={{ content: { padding: 0 } }}
    >
      <Attachments
        customRequest={() => {}} // 自定义上传请求，实际上不执行任何操作
        beforeUpload={beforeUpload}
        items={attachedFiles}
        onChange={(info) => setAttachedFiles(info.fileList)}
        placeholder={(type) =>
          type === 'drop'
            ? { title: '拖拽文件到此处' }
            : {
                icon: <CloudUploadOutlined />,
                title: '上传文件',
                description: '支持 CSV、Excel、JSON 格式，最大 10MB',
              }
        }
        maxCount={1}
      />
    </Sender.Header>
  );

  return (
    <>
      {/* 提示词 */}
      <Prompts
        items={senderPrompts as any}
        onItemClick={(info) => {
          const promptText = (info.data as ExtendedPromptItem).prompt || String(info.data.description);
          setInputValue(promptText);
        }}
        styles={{
          item: { padding: '6px 12px' },
        }}
        className={styles.senderPrompt}
      />
      {/* 输入框 */}
      <Sender
        value={inputValue}
        header={senderHeader}
        onSubmit={() => {
          onSubmit(inputValue);
          setInputValue('');
        }}
        onChange={setInputValue}
        onCancel={() => {
          abortController.current?.abort();
        }}
        prefix={
          <Flex gap="small">
            <Button
              type="text"
              icon={<PaperClipOutlined />}
              onClick={() => setAttachmentsOpen(!attachmentsOpen)}
              style={{ color: attachmentsOpen ? '#1890ff' : undefined }}
            />
            {/* 新增：模板选择按钮 */}
            {onOpenTemplateSelector && (
              <Button
                type="text"
                icon={<FileTextOutlined />}
                onClick={onOpenTemplateSelector}
                title="选择分析模板"
                style={{ color: '#52c41a' }}
              />
            )}
          </Flex>
        }
        loading={isLoading}
        className={styles.sender}
        actions={(_, info) => {
          const { SendButton } = info.components;
          return (
            <Flex gap={4}>
              <SendButton
                type={
                  connectionStatus === 'connected' ? 'primary' : 'default'
                }
                disabled={isLoading}
              />
            </Flex>
          );
        }}
        placeholder={selectedDataSource
          ? `向AI提问关于 ${selectedDataSource.name} 的数据分析问题...`
          : attachedFiles.length > 0
          ? "请描述您想要对上传文件进行的分析..."
          : hasUploadedFiles
          ? "继续对话..."
          : "请先选择数据源或上传文件..."}
        disabled={isLoading || (!selectedDataSource && attachedFiles.length === 0 && !hasUploadedFiles)}
      />
    </>
  );
};

export default memo(ChatSender);