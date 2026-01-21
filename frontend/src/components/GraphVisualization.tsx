import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { ConceptNode, ConceptEdge } from '../services/api';
import './GraphVisualization.css';

interface GraphProps {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
  onNodeClick?: (node: ConceptNode) => void;
}

const GraphVisualization: React.FC<GraphProps> = ({ nodes, edges, onNodeClick }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const zoomRef = useRef<any>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const width = 1200;
    const height = 800;

    // 清空之前的内容
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('style', 'max-width: 100%; height: auto;');

    const g = svg.append('g');

    // 添加缩放功能
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoomLevel(event.transform.k);
      });

    zoomRef.current = zoom;
    svg.call(zoom as any);

    // 学科颜色映射
    const colorScale = d3.scaleOrdinal<string>()
      .domain(['数学', '物理', '化学', '生物', '计算机', '社会学'])
      .range(['#FF6B6B', '#4ECDC4', '#95E1D3', '#F38181', '#AA96DA', '#FCBAD3']);

    // 识别根节点（depth=0的节点，通常是第一个节点）
    const rootNode = nodes.find((n: any) => n.depth === 0) || nodes[0];
    
    console.log('[Graph] 根节点:', rootNode.id, rootNode.label);
    console.log('[Graph] 总节点数:', nodes.length);
    console.log('[Graph] 总边数:', edges.length);
    console.log('[Graph] 边列表:', edges.map((e: any) => `${e.source} -> ${e.target}`));
    
    // 为每个节点计算目标半径（根据深度）
    const getTargetRadius = (node: any) => {
      const depth = node.depth || (node.id === rootNode.id ? 0 : 1);
      if (depth === 0) return 0; // 根节点在中心
      return 150 * depth; // 每一层距离中心150px
    };

    // 力导向图模拟 - 使用径向布局
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges)
        .id((d: any) => d.id)
        .distance((d: any) => {
          // 根据层级调整边长度
          const sourceDepth = (d.source as any).depth || 0;
          const targetDepth = (d.target as any).depth || 0;
          return 100 + Math.abs(targetDepth - sourceDepth) * 50;
        })
        .strength(1.2))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))
      // 径向力：将节点推向各自层级的圆环上
      .force('radial', d3.forceRadial((d: any) => getTargetRadius(d), width / 2, height / 2).strength(0.8));

    // 绘制边（每条边包含line和title）
    const linkGroup = g.append('g')
      .attr('class', 'links')
      .selectAll('g')
      .data(edges)
      .enter()
      .append('g');

    // 添加连线
    linkGroup.append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.5)
      .attr('stroke-width', (d) => Math.max(2, d.weight * 5))
      .style('cursor', 'help');  // 鼠标悬停时显示帮助图标
    
    // 为连线添加tooltip显示关联解释
    linkGroup.append('title')
      .text((d: any) => {
        const reasoning = d.reasoning || `${d.source} 与 ${d.target} 的关联`;
        return reasoning;
      });

    // 绘制节点组
    const nodeGroup = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .call(d3.drag<any, any>()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded));

    // 绘制节点圆圈（增强动画和交互效果，根据深度调整大小）
    nodeGroup.append('circle')
      .attr('r', (d: any) => {
        // 根据深度计算节点大小：深度越深，节点越小
        const depth = d.depth || 0;
        const baseSize = depth === 0 ? 35 : (depth === 1 ? 18 : 12);  // 根节点35，一级子节点18，二级+12
        const credibilityBonus = d.credibility ? d.credibility * 5 : 0;
        return baseSize + credibilityBonus;
      })
      .attr('fill', (d) => colorScale(d.discipline))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('filter', 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2))')
      .on('click', function(event, d) {
        event.stopPropagation();
        // 移除之前的选中状态
        svg.selectAll('.node').classed('selected', false);
        // 添加当前选中状态
        d3.select((this as any).parentNode).classed('selected', true);
        if (onNodeClick) onNodeClick(d);
      })
      .on('mouseenter', function(_event, d: any) {
        const element = d3.select(this);
        element.interrupt(); // 中断之前的动画
        const depth = d.depth || 0;
        const baseSize = depth === 0 ? 35 : (depth === 1 ? 18 : 12);
        const credibilityBonus = d.credibility ? d.credibility * 5 : 0;
        const currentRadius = baseSize + credibilityBonus;
        element
          .transition()
          .duration(200)
          .attr('r', currentRadius * 1.3)
          .attr('stroke-width', 4)
          .style('filter', 'drop-shadow(0 8px 16px rgba(102, 126, 234, 0.5))');
      })
      .on('mouseleave', function(_event, d: any) {
        const isSelected = d3.select((this as any).parentNode).classed('selected');
        if (!isSelected) {
          const element = d3.select(this);
          element.interrupt(); // 中断之前的动画
          const depth = d.depth || 0;
          const baseSize = depth === 0 ? 35 : (depth === 1 ? 18 : 12);
          const credibilityBonus = d.credibility ? d.credibility * 5 : 0;
          const currentRadius = baseSize + credibilityBonus;
          element
            .transition()
            .duration(200)
            .attr('r', currentRadius)
            .attr('stroke-width', 2)
            .style('filter', 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2))');
        }
      });

    // 节点标签（增强样式）
    nodeGroup.append('text')
      .text((d) => d.label)
      .attr('font-size', 13)
      .attr('font-weight', 600)
      .attr('dx', (d) => (d.credibility ? 10 + d.credibility * 8 : 15) + 8)
      .attr('dy', 4)
      .attr('fill', '#333')
      .attr('pointer-events', 'none')
      .style('text-shadow', '0 2px 4px rgba(255, 255, 255, 0.8)');

    // 添加标题（悬浮提示）
    nodeGroup.append('title')
      .text((d) => `${d.label}\n学科: ${d.discipline}\n定义: ${d.definition}\n可信度: ${(d.credibility * 100).toFixed(0)}%`);

    // 更新位置
    simulation.on('tick', () => {
      linkGroup.selectAll('line')
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // 拖拽函数
    function dragStarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragEnded(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // 清理函数
    return () => {
      simulation.stop();
    };
  }, [nodes, edges, onNodeClick]);

  return (
    <div className="graph-container">
      <svg ref={svgRef}></svg>
      <div className="zoom-controls">
        <button
          className="zoom-btn"
          onClick={() => {
            if (!svgRef.current || !zoomRef.current) return;
            const svg = d3.select(svgRef.current);
            svg.transition().duration(300).call(zoomRef.current.scaleBy, 1.2);
          }}
          title="放大"
        >
          +
        </button>
        <span className="zoom-level">{Math.round(zoomLevel * 100)}%</span>
        <button
          className="zoom-btn"
          onClick={() => {
            if (!svgRef.current || !zoomRef.current) return;
            const svg = d3.select(svgRef.current);
            svg.transition().duration(300).call(zoomRef.current.scaleBy, 0.833);
          }}
          title="缩小"
        >
          −
        </button>
        <button
          className="zoom-btn reset-btn"
          onClick={() => {
            if (!svgRef.current || !zoomRef.current) return;
            const svg = d3.select(svgRef.current);
            svg.transition().duration(300).call(zoomRef.current.transform, d3.zoomIdentity);
          }}
          title="重置"
        >
          ⟲
        </button>
      </div>
    </div>
  );
};

export default GraphVisualization;
