import React from 'react';
import { Conversations } from '@ant-design/x';
import { DeleteOutlined } from '@ant-design/icons';

interface ConversationListProps {
  conversations: any[];
  curConversation: string;
  messageHistory: Record<string, any>;
  styles: any;
  abortController: React.MutableRefObject<AbortController | null>;
  onConversationChange: (val: string) => void;
  setMessages: (messages: any) => void;
  setConversations: (conversations: any) => void;
  setCurConversation: (key: string) => void;
}

const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  curConversation,
  messageHistory,
  styles,
  abortController,
  onConversationChange,
  setMessages,
  setConversations,
  setCurConversation,
}) => {
  return (
    <Conversations
      items={conversations}
      className={styles.conversations}
      activeKey={curConversation}
      onActiveChange={async (val) => {
        abortController.current?.abort();
        setTimeout(() => {
          setCurConversation(val);
          setMessages(messageHistory?.[val] || []);
        }, 100);
      }}
      groupable
      styles={{ item: { padding: '0 8px' } }}
      menu={(conversation) => ({
        items: [
          {
            label: '删除',
            key: 'delete',
            icon: <DeleteOutlined />,
            danger: true,
            onClick: () => {
              const newList = conversations.filter((item) => item.key !== conversation.key);
              const newKey = newList?.[0]?.key;
              setConversations(newList);
              setTimeout(() => {
                if (conversation.key === curConversation) {
                  setCurConversation(newKey);
                  setMessages(messageHistory?.[newKey] || []);
                }
              }, 200);
            },
          },
        ],
      })}
    />
  );
};

export default ConversationList;