import React, { useState, useCallback } from 'react';
import { Input, Button, Spin, message, Card, Tag, Space, Tooltip, Modal, Divider } from 'antd';
import { SearchOutlined, ReloadOutlined, ExpandOutlined, BookOutlined, FileTextOutlined } from '@ant-design/icons';
import GraphVisualization from './components/GraphVisualization';
import { conceptAPI, ConceptNode, ConceptEdge, ArxivPaper } from './services/api';
import './App.css';

// 定义截断工具函数（前端最终保障，确保≤500字）
const truncateDefinition = (text: string, maxLength: number = 500): string => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
};

// 来源标签颜色映射
const sourceColors: Record<string, string> = {
  'Wikipedia': 'green',
  'LLM': 'blue',
  'Arxiv': 'orange',
  'Manual': 'purple'
};

const App: React.FC = () => {
  const [concept, setConcept] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandLoading, setExpandLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [nodes, setNodes] = useState<ConceptNode[]>([]);
  const [edges, setEdges] = useState<ConceptEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<ConceptNode | null>(null);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [searchArxivPapers, setSearchArxivPapers] = useState<ArxivPaper[]>([]);  // 搜索结果的相关论文
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [conceptDetail, setConceptDetail] = useState<{
    detailed_introduction: string;
    wiki_definition: string | null;
    wiki_url: string | null;
    related_papers: ArxivPaper[];
  } | null>(null);

  const handleSearch = async () => {
    if (!concept.trim()) {
      message.warning('请输入概念名称');
      return;
    }
    
    setLoading(true);
    setSelectedNode(null);
    setExpandedNodes(new Set());
    
    try {
      const response = await conceptAPI.discover(concept);
      if (response.status === 'success') {
        // 确保所有节点定义都被截断
        const processedNodes = response.data.nodes.map(node => ({
          ...node,
          definition: truncateDefinition(node.definition, 500)
        }));
        
        // 验证边的有效性（确保source和target都存在）
        const nodeIds = new Set(processedNodes.map(n => n.id));
        const validEdges = response.data.edges.filter(edge => 
          nodeIds.has(edge.source) && nodeIds.has(edge.target)
        );
        
        setNodes(processedNodes);
        setEdges(validEdges);
        
        // 保存arxiv论文信息
        if (response.data.metadata?.arxiv_papers) {
          setSearchArxivPapers(response.data.metadata.arxiv_papers);
        } else {
          setSearchArxivPapers([]);
        }
        
        message.success({
          content: `发现 ${processedNodes.length} 个相关概念，${validEdges.length} 个关联关系`,
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

  const handleNodeClick = useCallback((node: ConceptNode) => {
    // 确保显示的定义已截断
    setSelectedNode({
      ...node,
      definition: truncateDefinition(node.definition, 500)
    });
    console.log('点击节点:', node);
  }, []);

  // 展开节点 - 获取相关概念
  const handleExpandNode = async () => {
    if (!selectedNode) return;
    
    // 检查是否已展开
    if (expandedNodes.has(selectedNode.id)) {
      message.info('该节点已展开过');
      return;
    }
    
    setExpandLoading(true);
    
    try {
      // 传递现有节点ID列表，避免重复
      const existingNodeIds = nodes.map(n => n.id);
      const response = await conceptAPI.expandNode(selectedNode.id, selectedNode.label, existingNodeIds);
      
      if (response.status === 'success' && response.data.nodes.length > 0) {
        // 处理新节点，确保定义截断
        const newNodes = response.data.nodes
          .map(node => ({
            ...node,
            definition: truncateDefinition(node.definition, 500)
          }))
          .filter(newNode => !nodes.some(existing => existing.id === newNode.id));
        
        if (newNodes.length === 0) {
          message.info('没有发现新的相关概念');
          setExpandedNodes(prev => new Set([...prev, selectedNode.id]));
          return;
        }
        
        // 合并节点
        const allNodes = [...nodes, ...newNodes];
        const allNodeIds = new Set(allNodes.map(n => n.id));
        
        // 创建新的边连接到选中节点
        const newEdges: ConceptEdge[] = newNodes.map(newNode => ({
          source: selectedNode.id,
          target: newNode.id,
          relation: 'related_to',
          weight: 0.7,
          reasoning: `从 ${selectedNode.label} 扩展发现`
        }));
        
        // 合并边并验证有效性
        const allEdges = [...edges, ...newEdges, ...response.data.edges]
          .filter(edge => allNodeIds.has(edge.source) && allNodeIds.has(edge.target))
          // 去重
          .filter((edge, index, self) => 
            index === self.findIndex(e => 
              e.source === edge.source && e.target === edge.target
            )
          );
        
        setNodes(allNodes);
        setEdges(allEdges);
        setExpandedNodes(prev => new Set([...prev, selectedNode.id]));
        
        message.success({
          content: `成功展开！新增 ${newNodes.length} 个相关概念`,
          duration: 3,
          icon: '✨'
        });
      } else {
        message.info('未找到更多相关概念');
        setExpandedNodes(prev => new Set([...prev, selectedNode.id]));
      }
    } catch (error: any) {
      console.error('展开失败:', error);
      message.error('展开概念失败，请稍后重试');
    } finally {
      setExpandLoading(false);
    }
  };

  const handleReset = () => {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setConcept('');
    setExpandedNodes(new Set());
    setSearchArxivPapers([]);
    setConceptDetail(null);
  };

  // 获取概念详细介绍
  const handleShowDetail = async () => {
    if (!selectedNode) return;
    
    setDetailLoading(true);
    try {
      const response = await conceptAPI.getConceptDetail(selectedNode.label);
      if (response.status === 'success') {
        setConceptDetail(response.data);
        setShowDetailModal(true);
      }
    } catch (error) {
      console.error('获取详情失败:', error);
      message.error('获取概念详情失败');
    } finally {
      setDetailLoading(false);
    }
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
            {searchArxivPapers.length > 0 && (
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
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fa8c16' }}>
                    {searchArxivPapers.length}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>相关论文</div>
                </div>
              </Card>
            )}
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
                  <Space size={4}>
                    <Tag color="blue" style={{ fontSize: '12px' }}>
                      {selectedNode.discipline}
                    </Tag>
                    {/* 来源标签 */}
                    <Tooltip title={`定义来源: ${selectedNode.source || 'LLM'}`}>
                      <Tag 
                        color={sourceColors[selectedNode.source || 'LLM']} 
                        style={{ fontSize: '12px' }}
                      >
                        {selectedNode.source || 'LLM'}
                      </Tag>
                    </Tooltip>
                    {expandedNodes.has(selectedNode.id) && (
                      <Tag color="cyan" style={{ fontSize: '12px' }}>已展开</Tag>
                    )}
                  </Space>
                </div>
                
                <div style={{ lineHeight: '1.6', marginBottom: '12px' }}>
                  <strong style={{ color: '#764ba2' }}>📖 定义：</strong>
                  <br/>
                  <span style={{ 
                    color: '#555',
                    display: 'block',
                    marginTop: '4px',
                    maxHeight: '150px',
                    overflow: 'auto'
                  }}>
                    {/* 前端最终截断保障 */}
                    {truncateDefinition(selectedNode.definition, 500)}
                  </span>
                  <div style={{ 
                    fontSize: '11px', 
                    color: '#999', 
                    marginTop: '4px',
                    fontStyle: 'italic'
                  }}>
                    来源: {selectedNode.source || 'AI生成'}
                  </div>
                </div>
                
                <div>
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
                          : selectedNode.credibility > 0.5
                          ? 'linear-gradient(90deg, #faad14, #ffc53d)'
                          : 'linear-gradient(90deg, #ff4d4f, #ff7875)',
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
                </div>
                
                <Button 
                  type="primary" 
                  block 
                  icon={<ExpandOutlined />}
                  style={{ 
                    marginTop: '16px',
                    background: expandedNodes.has(selectedNode.id)
                      ? '#d9d9d9'
                      : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: '8px',
                    height: '40px',
                    fontWeight: 'bold'
                  }}
                  loading={expandLoading}
                  disabled={expandedNodes.has(selectedNode.id)}
                  onClick={handleExpandNode}
                >
                  {expandedNodes.has(selectedNode.id) 
                    ? '✓ 已展开' 
                    : '🔎 展开相关概念'}
                </Button>
                
                <Button 
                  type="default" 
                  block 
                  icon={<BookOutlined />}
                  style={{ 
                    marginTop: '8px',
                    borderRadius: '8px',
                    height: '40px',
                    fontWeight: 'bold',
                    borderColor: '#667eea',
                    color: '#667eea'
                  }}
                  loading={detailLoading}
                  onClick={handleShowDetail}
                >
                  📚 查看详细概念介绍
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

      {/* 概念详情弹窗 */}
      <Modal
        title={
          <span style={{ fontSize: '18px' }}>
            📚 {selectedNode?.label} - 详细概念介绍
          </span>
        }
        open={showDetailModal}
        onCancel={() => setShowDetailModal(false)}
        footer={null}
        width={800}
        style={{ top: 20 }}
      >
        {conceptDetail && (
          <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
            {/* 维基百科定义 */}
            {conceptDetail.wiki_definition && (
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ color: '#667eea', marginBottom: '12px' }}>
                  📖 维基百科定义
                </h3>
                <Card size="small" style={{ background: '#f6f8fa' }}>
                  <p style={{ margin: 0, lineHeight: 1.8 }}>
                    {conceptDetail.wiki_definition}
                  </p>
                  {conceptDetail.wiki_url && (
                    <a 
                      href={conceptDetail.wiki_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ fontSize: '12px', marginTop: '8px', display: 'block' }}
                    >
                      🔗 查看维基百科原文
                    </a>
                  )}
                </Card>
              </div>
            )}
            
            <Divider />
            
            {/* 大模型生成的详细介绍 */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ color: '#764ba2', marginBottom: '12px' }}>
                🤖 AI 生成的详细介绍
              </h3>
              <div 
                style={{ 
                  lineHeight: 2,
                  whiteSpace: 'pre-wrap',
                  background: '#fafafa',
                  padding: '16px',
                  borderRadius: '8px'
                }}
                dangerouslySetInnerHTML={{ 
                  __html: conceptDetail.detailed_introduction
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/### (.*)/g, '<h4 style="color: #667eea; margin-top: 16px;">$1</h4>')
                    .replace(/- \*\*(.*?)\*\*：/g, '<li><strong>$1</strong>：')
                    .replace(/\n/g, '<br/>')
                }}
              />
            </div>
            
            <Divider />
            
            {/* Arxiv论文 */}
            {conceptDetail.related_papers && conceptDetail.related_papers.length > 0 && (
              <div>
                <h3 style={{ color: '#fa8c16', marginBottom: '12px' }}>
                  <FileTextOutlined /> 相关学术论文 (Arxiv)
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {conceptDetail.related_papers.map((paper, index) => (
                    <Card 
                      key={index} 
                      size="small"
                      style={{ borderLeft: '3px solid #fa8c16' }}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                        {paper.title}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                        作者: {paper.authors.join(', ')}
                      </div>
                      <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>
                        发表时间: {paper.published}
                      </div>
                      <div style={{ fontSize: '13px', color: '#555' }}>
                        {paper.summary}
                      </div>
                      <a 
                        href={paper.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ fontSize: '12px', marginTop: '8px', display: 'inline-block' }}
                      >
                        🔗 查看论文
                      </a>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <footer className="app-footer">
        <p>提示：点击节点查看详情 | 定义来源于维基百科 | 点击"详细介绍"查看AI生成的扩展内容</p>
      </footer>
    </div>
  );
};

export default App;
