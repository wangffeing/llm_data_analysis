import React, { useState, useRef, useEffect } from 'react';
import {
  Drawer,
  Typography,
  Collapse,
  Card,
  Steps,
  Space,
  List,
  Divider,
} from 'antd';
import {
  QuestionCircleOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { Welcome } from '@ant-design/x';
import { helpSections } from '../constants/helpConstants';
import { styles } from '../styles/helpStyles';
import logo from '../resource/logo1.png';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;

interface HelpGuideProps {
  visible: boolean;
  onClose: () => void;
}

const HelpGuide: React.FC<HelpGuideProps> = ({ visible, onClose }) => {
  const [activeStep, setActiveStep] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleStepClick = (stepIndex: number) => {
    setActiveStep(stepIndex);
  };

  useEffect(() => {
    if (visible && contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [activeStep, visible]);

  const currentSection = helpSections[activeStep];

  return (
    <Drawer
      title={
        <Space>
          <QuestionCircleOutlined style={{ color: '#1677ff' }} />
          <span>功能帮助指南</span>
        </Space>
      }
      open={visible}
      onClose={onClose}
      width={900}
      placement="right"
      styles={{
        body: styles.drawerBody,
      }}
    >
      {/* 欢迎卡片 */}
      <div style={styles.welcomeCard}>
        <Welcome
          variant="borderless"
          icon={<img src={logo} alt="Logo" style={{ width: 64, height: 64 }} />}
          title="欢迎使用智能数据分析助手"
          description="本指南将帮助您快速掌握各项功能，让您的数据分析工作更加高效、智能。"
        />
      </div>

      {/* 功能导航 */}
      <Card 
        title="功能导航" 
        bordered={false} 
        style={styles.navigationCard}
        size="small"
      >
        <Steps
          current={activeStep}
          type="navigation"
          size="small"
          onChange={handleStepClick}
          items={helpSections.map((section) => ({
            key: section.title,
            title: section.title,
            icon: section.icon,
          }))}
        />
      </Card>

      {/* 内容区域 */}
      <div ref={contentRef}>
        <Card
          bordered={false}
          style={styles.contentCard}
          title={
            <Space size="middle">
              {currentSection.icon}
              <Title level={5} style={styles.sectionHeader}>
                {currentSection.title}
              </Title>
            </Space>
          }
        >
          <Paragraph type="secondary">{currentSection.description}</Paragraph>

          <Collapse 
            defaultActiveKey={[0]} 
            accordion 
            ghost
            size="small"
          >
            {currentSection.content.map((item, index) => (
              <Panel
                key={index}
                header={
                  <Space>
                    {item.icon}
                    <Text strong>{item.category}</Text>
                  </Space>
                }
              >
                <List
                  size="small"
                  dataSource={item.items}
                  renderItem={(listItem) => (
                    <List.Item style={styles.listItem}>
                      <List.Item.Meta
                        avatar={<div style={styles.bulletPoint} />}
                        title={
                          <Paragraph style={styles.listItemMeta}>
                            {listItem}
                          </Paragraph>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Panel>
            ))}
          </Collapse>

          {/* 小贴士部分 */}
          <div style={styles.tipsSection}>
            <Divider orientation="left" dashed>
              <Space>
                <BulbOutlined style={{ color: '#faad14' }} />
                <Text strong>小贴士</Text>
              </Space>
            </Divider>

            <Space direction="vertical" size="small">
              {currentSection.tips.map((tip, index) => (
                <Text key={index} type="secondary">
                  • {tip}
                </Text>
              ))}
            </Space>
          </div>
        </Card>
      </div>
    </Drawer>
  );
};

export default HelpGuide;