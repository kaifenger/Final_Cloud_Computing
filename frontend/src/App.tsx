import React, { useState } from 'react';
import { Input, Button, Spin, message, Card, Tag, Space } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import GraphVisualization from './components/GraphVisualization';
import { conceptAPI, ConceptNode, ConceptEdge } from './services/api';
import './App.css';

const App: React.FC = () => {
  const [concept, setConcept] = useState('');
  const [loading, setLoading] = useState(false);
  const [nodes, setNodes] = useState<ConceptNode[]>([]);
  const [edges, setEdges] = useState<ConceptEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<ConceptNode | null>(null);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  const handleSearch = async () => {
    if (!concept.trim()) {
      message.warning('请输入概念名称');
      return;
    }
    
    setLoading(true);
    try {
      const response = await conceptAPI.discover(concept);
      if (response.status === 'success') {
        setNodes(response.data.nodes);
        setEdges(response.data.edges);
        message.success({
          content: `发现 ${response.data.nodes.length} 个相关概念，${response.data.edges.length} 个关联关系`,
          duration: 3,
          icon: '🎉'
        });
        // 添加到搜索历史
        if (!searchHistory.includes(concept)) {
          setSearchHistory(prev => [concept, ...prev].slice(0, 5));
        }
      } else {
        message.error('概念挖掘失败');
      }
    } catch (error: any) {
      console.error('搜索失败:', error);
      if (error.response?.status === 504) {
        message.error('Agent服务超时，请稍后重试');
      } else if (error.response?.status === 500) {
        message.error('服务器错误，请检查Agent服务是否正常运行');
      } else {
        message.error('网络错误，请检查后端服务是否启动');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (node: ConceptNode) => {
    setSelectedNode(node);
    console.log('点击节点:', node);
    // TODO: 实现节点展开功能（调用 conceptAPI.getGraph）
  };

  const handleReset = () => {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setConcept('');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>ConceptGraph AI</h1>
        <p className="subtitle">跨学科知识图谱智能体</p>
      </header>

      <div className="search-section">
        {nodes.length > 0 && (
          <div style={{ 
            position: 'absolute', 
            top: '20px', 
            right: '20px',
            display: 'flex',
            gap: '12px',
            zIndex: 10
          }}>
            <Card 
              size="small" 
              style={{ 
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#667eea' }}>
                  {nodes.length}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>概念节点</div>
              </div>
            </Card>
            <Card 
              size="small" 
              style={{ 
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#764ba2' }}>
                  {edges.length}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>关联关系</div>
              </div>
            </Card>
          </div>
        )}
        <Space.Compact style={{ width: '100%', maxWidth: '600px' }}>
          <Input
            placeholder="输入概念（如：熵、神经网络、量子纠缠）"
            value={concept}
            onChange={(e) => setConcept(e.target.value)}
            onPressEnter={handleSearch}
            size="large"
            disabled={loading}
          />
          <Button
            type="primary"
            size="large"
            icon={<SearchOutlined />}
            onClick={handleSearch}
            loading={loading}
          >
            搜索
          </Button>
          <Button
            size="large"
            icon={<ReloadOutlined />}
            onClick={handleReset}
            disabled={loading}
          >
            重置
          </Button>
        </Space.Compact>
        {searchHistory.length > 0 && nodes.length === 0 && (
          <div style={{ 
            marginTop: '20px',
            textAlign: 'center'
          }}>
            <div style={{ 
              color: 'white',
              fontSize: '14px',
              marginBottom: '10px',
              opacity: 0.9
            }}>
              搜索历史:
            </div>
            <Space wrap>
              {searchHistory.map((item, index) => (
                <Tag 
                  key={index}
                  color="purple"
                  style={{ 
                    cursor: 'pointer',
                    fontSize: '14px',
                    padding: '6px 12px',
                    borderRadius: '16px',
                    transition: 'all 0.3s ease'
                  }}
                  onClick={() => {
                    setConcept(item);
                    setTimeout(handleSearch, 100);
                  }}
                >
                  {item}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </div>

      {loading ? (
        <div className="loading-container">
          <Spin size="large" tip="正在挖掘跨学科关联..." />
        </div>
      ) : nodes.length > 0 ? (
        <div className="content-section">
          <div className="graph-section">
            <GraphVisualization
              nodes={nodes}
              edges={edges}
              onNodeClick={handleNodeClick}
            />
          </div>
          
          {selectedNode && (
            <div className="detail-section">
              <Card 
                title={
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>🔍</span>
                    <span>节点详情</span>
                  </span>
                }
                size="small"
                extra={
                  <Button 
                    type="text" 
                    onClick={() => setSelectedNode(null)}
                    style={{ color: 'white' }}
                  >
                    ✕
                  </Button>
                }
              >
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ 
                    fontSize: '18px', 
                    fontWeight: 'bold',
                    marginBottom: '8px',
                    color: '#667eea'
                  }}>
                    {selectedNode.label}
                  </div>
                  <Tag color="blue" style={{ fontSize: '12px' }}>
                    {selectedNode.discipline}
                  </Tag>
                </div>
                
                <p style={{ lineHeight: '1.6' }}>
                  <strong style={{ color: '#764ba2' }}>📖 定义：</strong>
                  <br/>
                  <span style={{ color: '#555' }}>{selectedNode.definition}</span>
                </p>
                
                <p>
                  <strong style={{ color: '#764ba2' }}>📊 可信度：</strong>
                  <br/>
                  <div style={{ marginTop: '8px' }}>
                    <div style={{ 
                      background: '#f0f0f0',
                      borderRadius: '10px',
                      overflow: 'hidden',
                      height: '20px',
                      position: 'relative'
                    }}>
                      <div style={{ 
                        background: selectedNode.credibility > 0.7 
                          ? 'linear-gradient(90deg, #52c41a, #73d13d)'
                          : 'linear-gradient(90deg, #faad14, #ffc53d)',
                        width: `${selectedNode.credibility * 100}%`,
                        height: '100%',
                        transition: 'width 0.5s ease',
                        borderRadius: '10px'
                      }}></div>
                      <span style={{ 
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        color: '#333'
                      }}>
                        {(selectedNode.credibility * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </p>
                
                <Button 
                  type="primary" 
                  block 
                  style={{ 
                    marginTop: '16px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: '8px',
                    height: '40px',
                    fontWeight: 'bold'
                  }}
                  onClick={() => {
                    message.info('展开功能开发中...');
                    // TODO: 实现节点展开功能
                  }}
                >
                  🔎 展开相关概念
                </Button>
              </Card>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <div style={{ fontSize: '72px', marginBottom: '20px' }}>🧠</div>
          <p style={{ marginBottom: '12px', fontSize: '28px', fontWeight: '300' }}>
            输入概念开始探索知识图谱
          </p>
          <p style={{ fontSize: '16px', opacity: '0.8', fontWeight: '300' }}>
            例如：熵、神经网络、量子纠缠、黑洞、区块链
          </p>
        </div>
      )}

      <footer className="app-footer">
        <p>提示：点击节点查看详情 | 拖拽节点调整位置 | 滚轮缩放图谱</p>
      </footer>
    </div>
  );
};

export default App;
