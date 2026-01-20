import React, { useState } from 'react';
import { Button, Card, Tag, Space, Divider, Progress, Input, message } from 'antd';
import { ExpandOutlined, SendOutlined } from '@ant-design/icons';
import { ConceptNode } from '../services/api';

const { TextArea } = Input;

interface NodeDetailPanelProps {
  selectedNode: ConceptNode;
  expandedNodes: Set<string>;
  expandLoading: boolean;
  onClose: () => void;
  onExpand: () => void;
}

const truncateDefinition = (text: string, maxLength: number = 500): string => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
};

const NodeDetailPanel: React.FC<NodeDetailPanelProps> = ({
  selectedNode,
  expandedNodes,
  expandLoading,
  onClose,
  onExpand
}) => {
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiChatLoading, setAiChatLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{role: string; content: string}>>([]);

  const handleAiChat = async () => {
    if (!aiQuestion.trim()) {
      message.warning('请输入问题');
      return;
    }
    
    setAiChatLoading(true);
    try {
      // TODO: 调用AI问答API
      const newChat = [
        ...chatHistory, 
        { role: 'user', content: aiQuestion },
        { role: 'assistant', content: `关于"${selectedNode.label}"的解答：这是一个示例回答。实际实现时需要调用后端AI问答API。` }
      ];
      setChatHistory(newChat);
      setAiQuestion('');
      message.success('提问成功');
    } catch (error) {
      message.error('AI问答失败');
    } finally {
      setAiChatLoading(false);
    }
  };

  return (
    <Card
      style={{
        width: '420px',
        maxHeight: 'calc(100vh - 200px)',
        overflow: 'auto',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '16px',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
        border: 'none',
        color: 'white'
      }}
      bodyStyle={{
        background: 'white',
        borderRadius: '12px',
        margin: '8px',
        padding: '24px'
      }}
      title={
        <Button
          type="text"
          size="small"
          onClick={onClose}
          style={{ color: 'white', fontSize: '16px' }}
        >
          ✕
        </Button>
      }
    >
      {/* 1. 概念名称 */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          fontSize: '26px', 
          fontWeight: 'bold',
          marginBottom: '12px',
          color: '#667eea',
          borderBottom: '3px solid #667eea',
          paddingBottom: '10px'
        }}>
          {selectedNode.label}
        </div>
      </div>

      {/* 2. 所属学科 */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '13px', color: '#999', marginBottom: '8px', fontWeight: '500' }}>
          📚 所属学科
        </div>
        <Space size={6} wrap>
          <Tag color="blue" style={{ fontSize: '13px', padding: '5px 14px', borderRadius: '12px' }}>
            {selectedNode.discipline}
          </Tag>
          {/* 可以有多个学科标签 */}
        </Space>
      </div>

      {/* 3. 一句话简介 (GPT生成) */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '13px', color: '#999', marginBottom: '8px', fontWeight: '500' }}>
          💡 一句话简介
        </div>
        <div style={{ 
          background: '#f6f8fa',
          padding: '14px',
          borderRadius: '10px',
          fontSize: '14px',
          lineHeight: '1.7',
          color: '#333',
          border: '1px solid #e8e8e8'
        }}>
          {truncateDefinition(selectedNode.definition, 200)}
        </div>
      </div>

      <Divider style={{ margin: '18px 0' }} />

      {/* 4. 与搜索词的相关度 */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '13px', color: '#999', marginBottom: '8px', fontWeight: '500' }}>
          🎯 与搜索词的相关度
        </div>
        <Progress 
          percent={Math.round(selectedNode.credibility * 100)} 
          status="active"
          strokeColor={{
            '0%': '#667eea',
            '100%': '#764ba2',
          }}
          strokeWidth={12}
        />
      </div>

      <Divider style={{ margin: '18px 0' }} />

      {/* 5. 维基百科权威定义 */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '13px', color: '#999', marginBottom: '8px', fontWeight: '500' }}>
          📖 维基百科权威定义
        </div>
        <div style={{ 
          background: selectedNode.source === 'Wikipedia' ? '#e6f7ff' : '#fff7e6',
          padding: '14px',
          borderRadius: '10px',
          fontSize: '13px',
          lineHeight: '1.7',
          maxHeight: '180px',
          overflow: 'auto',
          border: selectedNode.source === 'Wikipedia' ? '1px solid #91d5ff' : '1px solid #ffd591'
        }}>
          {selectedNode.source === 'Wikipedia' ? (
            <>
              <div style={{ color: '#333', marginBottom: '10px' }}>
                {truncateDefinition(selectedNode.definition, 500)}
              </div>
              {(selectedNode as any).wiki_url && (
                <a 
                  href={(selectedNode as any).wiki_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ fontSize: '12px', color: '#1890ff' }}
                >
                  🔗 查看维基百科原文
                </a>
              )}
            </>
          ) : (
            <div style={{ color: '#999', fontStyle: 'italic', textAlign: 'center', padding: '10px' }}>
              ⚠️ 维基百科中暂无此条目
            </div>
          )}
        </div>
      </div>

      <Divider style={{ margin: '18px 0' }} />

      {/* 6. 相关文献 (Arxiv) */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '13px', color: '#999', marginBottom: '8px', fontWeight: '500' }}>
          📄 相关文献
        </div>
        <div style={{ 
          fontSize: '12px', 
          color: '#666',
          background: '#f9f9f9',
          padding: '10px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          点击下方"节点拓展"后可查看相关学术论文
        </div>
      </div>

      <Divider style={{ margin: '18px 0' }} />

      {/* 7. AI问答窗口 */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '13px', color: '#999', marginBottom: '8px', fontWeight: '500' }}>
          🤖 AI问答
        </div>
        
        {/* 聊天记录 */}
        {chatHistory.length > 0 && (
          <div style={{ 
            maxHeight: '220px', 
            overflow: 'auto',
            marginBottom: '12px',
            background: '#f6f8fa',
            padding: '14px',
            borderRadius: '10px',
            border: '1px solid #e8e8e8'
          }}>
            {chatHistory.map((chat, index) => (
              <div key={index} style={{ marginBottom: '12px' }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: chat.role === 'user' ? '#667eea' : '#52c41a',
                  fontWeight: 'bold',
                  marginBottom: '6px'
                }}>
                  {chat.role === 'user' ? '👤 你：' : '🤖 AI：'}
                </div>
                <div style={{ 
                  fontSize: '13px', 
                  color: '#333', 
                  paddingLeft: '24px',
                  lineHeight: '1.6'
                }}>
                  {chat.content}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 输入框 */}
        <TextArea
          placeholder={`针对"${selectedNode.label}"提问...`}
          value={aiQuestion}
          onChange={(e) => setAiQuestion(e.target.value)}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              handleAiChat();
            }
          }}
          autoSize={{ minRows: 2, maxRows: 4 }}
          style={{ marginBottom: '10px', borderRadius: '8px' }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleAiChat}
          loading={aiChatLoading}
          block
          style={{
            borderRadius: '8px',
            height: '38px',
            fontWeight: '500'
          }}
        >
          发送提问
        </Button>
      </div>

      <Divider style={{ margin: '18px 0' }} />

      {/* 8. 节点拓展按钮 */}
      <Button 
        type="primary" 
        block 
        icon={<ExpandOutlined />}
        style={{ 
          background: expandedNodes.has(selectedNode.id)
            ? '#d9d9d9'
            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          borderRadius: '10px',
          height: '48px',
          fontSize: '16px',
          fontWeight: 'bold',
          boxShadow: expandedNodes.has(selectedNode.id) 
            ? 'none' 
            : '0 4px 12px rgba(102, 126, 234, 0.4)'
        }}
        loading={expandLoading}
        disabled={expandedNodes.has(selectedNode.id)}
        onClick={onExpand}
      >
        {expandedNodes.has(selectedNode.id) 
          ? '✓ 已展开' 
          : '🔎 节点拓展'}
      </Button>
    </Card>
  );
};

export default NodeDetailPanel;
