import React, { useEffect, useRef } from 'react';
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

    // 学科颜色映射
    const colorScale = d3.scaleOrdinal<string>()
      .domain(['数学', '物理', '化学', '生物', '计算机', '社会学'])
      .range(['#FF6B6B', '#4ECDC4', '#95E1D3', '#F38181', '#AA96DA', '#FCBAD3']);

    // 力导向图模拟
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges)
        .id((d: any) => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // 添加缩放和拖拽支持
    const g = svg.append('g');

    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        }) as any
    );

    // 绘制边（增强动画效果）
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edges)
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.5)
      .attr('stroke-width', (d) => Math.max(2, d.weight * 5))
      .attr('stroke-dasharray', '1000')
      .attr('stroke-dashoffset', '1000')
      .transition()
      .duration(1000)
      .attr('stroke-dashoffset', '0');

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

    // 绘制节点圆圈（增强动画和交互效果）
    nodeGroup.append('circle')
      .attr('r', (d) => d.credibility ? 10 + d.credibility * 8 : 15)
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
      .on('mouseenter', function(_event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', (d.credibility ? 10 + d.credibility * 8 : 15) * 1.3)
          .attr('stroke-width', 4)
          .style('filter', 'drop-shadow(0 8px 16px rgba(102, 126, 234, 0.5))');
      })
      .on('mouseleave', function(_event, d) {
        const isSelected = d3.select((this as any).parentNode).classed('selected');
        if (!isSelected) {
          d3.select(this)
            .transition()
            .duration(200)
            .attr('r', d.credibility ? 10 + d.credibility * 8 : 15)
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
      link
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
    </div>
  );
};

export default GraphVisualization;
