import { CSSProperties } from 'react';

export const styles = {
  drawerBody: {
    padding: '16px',
    backgroundColor: '#f7f8fa',
  } as CSSProperties,
  
  welcomeCard: {
    marginBottom: '16px',
    padding: '16px',
    backgroundColor: '#fff',
    borderRadius: '8px',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
  } as CSSProperties,
  
  bulletPoint: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: '#1677ff',
    marginTop: '9px',
    flexShrink: 0,
  } as CSSProperties,
  
  searchContainer: {
    marginBottom: '16px',
  } as CSSProperties,
  
  navigationCard: {
    marginBottom: '16px',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
  } as CSSProperties,
  
  contentCard: {
    minHeight: '400px',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
  } as CSSProperties,
  
  sectionHeader: {
    margin: 0,
  } as CSSProperties,
  
  listItem: {
    border: 'none',
    padding: '4px 0',
  } as CSSProperties,
  
  listItemMeta: {
    margin: 0,
    fontWeight: 'normal',
    lineHeight: '1.6',
  } as CSSProperties,
  
  tipsSection: {
    marginTop: '16px',
  } as CSSProperties,
  
  // 响应式样式
  '@media (max-width: 768px)': {
    drawerBody: {
      padding: '12px',
    },
    welcomeCard: {
      padding: '12px',
    },
  } as CSSProperties,
};