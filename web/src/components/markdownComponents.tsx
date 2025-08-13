import ReactMarkdown from 'react-markdown';
import Prism from 'prismjs';
import type { Components } from 'react-markdown';
import { GPTVis } from '@antv/gpt-vis';
import { Alert } from 'antd';
import DOMPurify from 'dompurify';

import 'prismjs/components/prism-python';
import 'prismjs/themes/prism.css';
import '../styles/markdownComponents.css';

// 定义 code 组件的 props 类型
interface CodeProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

const markdownComponents: Components = {
  // 重写 'code' 元素的渲染逻辑
  code({ node, inline, className, children, ...props }: CodeProps) {
    
    // 判断是否是带 "language-python" 标记的块级代码
    if (!inline && className === 'language-python') {
      try {
        // 使用 Prism.js 高亮代码
        const codeString = String(children).trim();
        
        // 在 dangerouslySetInnerHTML 前添加净化
        const highlighted = Prism.highlight(codeString, Prism.languages.python, 'python');
        const sanitizedHighlighted = DOMPurify.sanitize(highlighted);
        
        return (
          <div className="thought-chain-content">
            <pre className="code-block">
              <code 
                className={className} 
                dangerouslySetInnerHTML={{ __html: sanitizedHighlighted }}
                {...props}
              />
            </pre>
          </div>
        );
      } catch (error) {
        // 如果高亮失败，回退到普通的代码块显示
        console.warn('Prism highlighting failed:', error);
        return (
          <div className="thought-chain-content">
            <pre className="code-block-error">
              <code className={className} {...props}>
                {children}
              </code>
            </pre>
          </div>
        );
      }
    }
    
    // 判断是否是带 "language-gpt-vis" 标记的块级代码
    if (!inline && className === 'language-gpt-vis') {
      try {
        const codeString = String(children).trim();
        
        // 返回 GPT-Vis 图表渲染
        return (
          <div className="thought-chain-content">
            <div style={{
              border: '1px solid #e1e4e8',
              borderRadius: '6px',
              padding: '12px',
              background: '#fff',
              margin: '8px 0'
            }}>
              <GPTVis>{codeString}</GPTVis>
            </div>
          </div>
        );
      } catch (error) {
        // 如果 GPT-Vis 渲染失败，显示错误信息
        console.warn('GPT-Vis rendering failed:', error);
        const errorMessage = error instanceof Error ? error.message : '未知错误';
        return (
          <div className="thought-chain-content">
            <Alert
              message="图表渲染失败"
              description={`GPT-Vis 渲染错误: ${errorMessage}`}
              type="error"
              showIcon
              style={{ margin: '8px 0' }}
            />
          </div>
        );
      }
    }
    
    // 对于其他情况（行内代码或非 Python/GPT-Vis 代码），使用默认渲染
    return <code className={className} {...props}>{children}</code>;
  },
  
  // 添加段落组件以应用样式
  p({ children, ...props }) {
    return (
      <div className="thought-chain-content">
        <p className="markdown-content" {...props}>{children}</p>
      </div>
    );
  },
  
  // 添加其他常用元素的样式
  div({ children, ...props }) {
    return (
      <div className="thought-chain-content" {...props}>
        {children}
      </div>
    );
  },
};

export default markdownComponents; // 你可以把它保存成一个独立文件，方便导入