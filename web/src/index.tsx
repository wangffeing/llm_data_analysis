import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// 移除message.config配置，因为现在使用App组件包装

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);

reportWebVitals();
