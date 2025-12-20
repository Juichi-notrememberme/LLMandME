<script setup>
import { onMounted, ref, defineProps} from 'vue';
import * as d3 from "d3";
import { sankey, sankeyLinkHorizontal } from "d3-sankey";
import times from "@/assets/data/time.json"


    const props = defineProps({
        data: {
            type: Object,
            required: false,
            default: () => times
        }
    });
/**
 * 将原始 JSON 转换为 D3 Sankey 所需的 graph 格式 { nodes, links }
 * @param {Object} rawData - 用户传入的原始 JSON 数据
 * @returns {Object} { nodes: [], links: [] }
 */
function transformToSankeyGraph(rawData) {
  // --- 第一阶段：生成所有可能的节点和连线 (临时数据) ---
  const tempNodes = [];
  const tempLinks = [];

  // 1. 先生成 0-23 全量时间节点 (索引 0-23)
  for (let i = 0; i < 24; i++) {
    tempNodes.push({
      name: `${i}:00`,
      category: "Time"
    });
  }

  // 2. 生成话题节点和连线
  if (rawData && rawData.message) {
    rawData.message.forEach((topicItem) => {
      // 记录当前话题在 tempNodes 中的索引
      const topicNodeIndex = tempNodes.length;
      
      tempNodes.push({
        name: topicItem.title,
        category: "Topic"
      });

      if (topicItem.map) {
        topicItem.map.forEach((timePoint) => {
          const hours = parseInt(timePoint.id);
          const value = timePoint.value;

          if (value > 0) {
            tempLinks.push({
              source: hours,          // 暂时指向旧索引
              target: topicNodeIndex, // 暂时指向旧索引
              value: value,
              names: [topicItem.title]
            });
          }
        });
      }
    });
  }

  // --- 第二阶段：清洗数据 (Pruning) ---
  
  // 1. 找出所有“有用”的节点索引
  const usedNodeIndices = new Set();
  tempLinks.forEach(link => {
    usedNodeIndices.add(link.source);
    usedNodeIndices.add(link.target);
  });

  // 2. 创建新旧索引映射表
  // 我们将 Set 转为数组并排序，保证时间节点依然排在话题节点前面 (因为时间节点的旧索引 0-23 较小)
  const sortedIndices = Array.from(usedNodeIndices).sort((a, b) => a - b);
  
  const oldToNewIndexMap = new Map();
  const finalNodes = [];

  sortedIndices.forEach((oldIndex, newIndex) => {
    // 建立映射：旧索引 -> 新数组中的索引
    oldToNewIndexMap.set(oldIndex, newIndex);
    // 把该节点加入最终数组
    finalNodes.push(tempNodes[oldIndex]);
  });

  // 3. 更新连线的 source 和 target 为新索引
  const finalLinks = tempLinks.map(link => {
    return {
      ...link, // 复制 value, names 等属性
      source: oldToNewIndexMap.get(link.source),
      target: oldToNewIndexMap.get(link.target)
    };
  });

  return { nodes: finalNodes, links: finalLinks };
}

const chartRef = ref(null);

const drawSankey = () => {
  // 1. 数据转换
  const graph = transformToSankeyGraph(props.data);

  // 2. 设置画布
  const width = 928;
  const height = 1250;
  const svg = d3.select(chartRef.value)
      .append("svg")
      .attr("viewBox", [0, 0, width, height])
      .attr("width", width)
      .attr("height", height)
      .style("max-width", "100%")
      .attr("style", "max-width: 100%; height: 100%; background: #222;");


  // 3. 配置 Sankey 生成器
  const sankeyGenerator = sankey()
      .nodeSort(null)
      .linkSort(null)
      .nodeWidth(4)
      .nodePadding(10)
      .extent([[0, 5], [width, height - 5]]);

  // 4. 计算布局 (注意：必须使用深拷贝，因为 d3 会修改数据)
  const { nodes, links } = sankeyGenerator({
      nodes: graph.nodes.map(d => ({ ...d })),
      links: graph.links.map(d => ({ ...d }))
  });

  // 5. 定义颜色 (根据话题名称定义颜色)
  // 提取所有唯一的话题名称作为 domain
  const allTopicNames = props.data.message.map(m => m.title);
  const TopicDict = {}
  allTopicNames.forEach((topic, index) => {
  TopicDict[topic] = index;
    });
  const color = d3.scaleLinear()
                .domain([0, Math.max(1, allTopicNames.length - 1)])
                .range(["#e85299", "#3fa885"])
                .interpolate(d3.interpolateHcl);

  // 6. 绘制连线
  svg.append("g")
      .attr("fill", "none")
      .selectAll("path")
      .data(links)
      .join("path")
      .attr("d", sankeyLinkHorizontal())
      .attr("stroke", d => color(TopicDict[d.names[0]]))
      .attr("stroke-width", d => Math.max(1, d.width))
      .attr("stroke-opacity", 0.5)
      .append("title")
      .text(d => `${d.source.name} → ${d.target.name}\n聊天消息数: ${d.value}`);

  // 7. 绘制节点
  svg.append("g")
      .selectAll("rect")
      .data(nodes)
      .join("rect")
      .attr("x", d => d.x0)
      .attr("y", d => d.y0)
      .attr("height", d => d.y1 - d.y0)
      .attr("width", d => d.x1 - d.x0)
      .attr("fill", "#fff")
      .append("title")
      .text(d => `${d.name}\n聊天消息数: ${d.value}`);

  // 8. 绘制文字
  svg.append("g")
      .style("font", "0.7rem sans-serif")
      .style("fill", '#fff')
      .selectAll("text")
      .data(nodes)
      .join("text")
      .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
      .attr("y", d => (d.y1 + d.y0) / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
      .text(d => d.x0 < width / 2 ? `${d.name}   ${d.value}` : `${d.value}   ${d.name}`);
}

onMounted(() => {
    drawSankey();
})
</script>

<template>
    <div ref="chartRef"></div>
</template>