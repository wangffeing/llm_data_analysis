import { createStyles } from 'antd-style';

export const useAppStyles = createStyles(({ token, css }) => {
  return {
    layout: css`
      width: 100%;
      min-width: 320px; // 降低最小宽度以支持移动设备
      height: 100vh;
      display: flex;
      background: ${token.colorBgContainer};
      font-family: AlibabaPuHuiTi, ${token.fontFamily}, sans-serif;
      
      @media (max-width: 768px) {
        flex-direction: column;
        min-width: 320px;
      }
    `,
    
    sider: css`
      background: ${token.colorBgLayout}80;
      width: 280px;
      height: 100%;
      display: flex;
      flex-direction: column;
      padding: 0 12px;
      box-sizing: border-box;
      
      @media (max-width: 768px) {
        width: 100%;
        height: auto;
        max-height: 200px;
        overflow-y: auto;
      }
    `,
    
    chat: css`
      height: 100%;
      width: 100%;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      padding-block: ${token.paddingLG}px;
      padding-inline: 24px;
      gap: 16px;
      
      @media (max-width: 768px) {
        padding-inline: 12px;
        padding-block: 12px;
      }
      
      @media (max-width: 480px) {
        padding-inline: 8px;
        padding-block: 8px;
      }
    `,
    
    chatList: css`
      flex: 1;
      overflow: auto;
      width: 100%;
    `,
    
    sender: css`
      width: 100%;
      max-width: 900px;
      margin: 0 auto;
      min-width: 0;
      overflow: hidden;
      
      @media (max-width: 768px) {
        max-width: 100%;
      }
    `,
    
    senderPrompt: css`
      width: 100%;
      max-width: 900px;
      margin: 0 auto;
      min-width: 0;
      overflow: hidden;
      color: ${token.colorText};
      
      @media (max-width: 768px) {
        max-width: 100%;
      }
    `,
    logo: css`
      display: flex;
      align-items: center;
      justify-content: start;
      padding: 0 24px;
      box-sizing: border-box;
      gap: 8px;
      margin: 24px 0;

      span {
        font-weight: bold;
        color: ${token.colorText};
        font-size: 16px;
      }
    `,
    addBtn: css`
      background: #1677ff0f;
      border: 1px solid #1677ff34;
      height: 40px;
      
      &:hover {
        background: ${token.colorPrimaryHover};
        border-color: ${token.colorPrimaryHover};
      }
    `,
    conversations: css`
      flex: 1;
      overflow-y: auto;
      margin-top: 12px;
      padding: 0;

      .ant-conversations-list {
        padding-inline-start: 0;
      }
    `,
    siderFooter: css`
      border-top: 1px solid ${token.colorBorderSecondary};
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    `,
    chatPrompt: css`
      .ant-prompts {
        .ant-prompts-label {
          color: #000000e0;
        }
        .ant-prompts-desc {
          color: #000000a6;
          width: 100%;
        }
      }
    `,
    loadingMessage: css`
      background-image: linear-gradient(90deg, #ff6b23 0%, #af3cb8 31%, #53b6ff 89%);
      background-size: 100% 2px;
      background-repeat: no-repeat;
      background-position: bottom;
    `,
    placeholder: css`
      padding-top: 32px;
    `,
    speechButton: css`
      font-size: 18px;
      
      &.ant-btn {
        color: ${token.colorText};
      }
    `,
    dataSourceList: css`
      margin-top: 12px;
      
      .ant-conversations-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        
        &:hover {
          background: ${token.colorBgTextHover};
        }
        
        &.selected {
          background: ${token.colorPrimaryBg};
          border: 1px solid ${token.colorPrimary};
        }
      }
    `,
  };
});