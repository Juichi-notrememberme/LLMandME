<script setup>
    import { onMounted, ref,defineProps} from 'vue';
    import * as d3 from "d3";
    import emotions from "@/assets/data/emotions.json"
    const props = defineProps({
        data: {
            type: Object,
            required: false,
            default: () => emotions
        }
    });

    const rTotal = ref(0)
    const rArc = ref(0)
    const rMaxItem = ref([])
    const rColor = ref(0)
    /**
 * 函数 1: 获取 total_avg
 * @param {Object} data - 源数据对象
 * @returns {Number} - 平均分
 */
const getTotalAvg = (data) => {
  return data.total_avg
}

/**
 * 函数 2: 获取 mapping 中最高分的项目，并转换为数组格式
 * @param {Object} data - 源数据对象
 * @returns {Array} - [title, avg_score]
 */
const getHighestScoreItem = (data) => {
  // 使用 reduce 遍历一次即可找到最大值，性能最优
  const maxItem = data.mapping.reduce((prev, current) => {
    // 如果当前项的分数大于之前记录的最大项分数，则返回当前项，否则保持不变
    return (current.avg_score > prev.avg_score) ? current : prev
  })

  // 按照你的要求转换为数组 [title, avg_score]
  return [maxItem.title, maxItem.avg_score * 100]
}

// 颜色适配
const getcolorindex = (num) => {
    return Math.floor(num / 20)
} 


    const arcref = ref(null)

    const ArcConfig = {
        viewWidth: 420,
        viewHeight: 420,
        width: 420,
        height: 420,
        margin: { top: 0, right: 0, bottom: 0, left: 0 }
    }


    const draw = () => {
        d3.select(arcref.value).selectAll("*").remove();
        
        const arcGenerator = d3.arc()
            .cornerRadius(5)
            .innerRadius(130)
            .outerRadius(180)

        const svgArc = d3.select(arcref.value)
            .append("svg")
            .attr("viewBox", `0 0 ${ArcConfig.viewWidth} ${ArcConfig.viewHeight}`)
            .style("max-width", "100%")
            .style("height", "auto")
            .attr("style", "max-width: 100%; height: auto; background: #222;");

        const color = d3.scaleLinear()
                .domain([0, 4])
                .range(["#e85299", "#3fa885"])
                .interpolate(d3.interpolateHcl);

        const Arc = svgArc.append("g")
                    .attr("transform", `translate(${ArcConfig.width / 2}, ${ArcConfig.height / 2})`)
                    .append("path")
                    .attr("d", d => arcGenerator({
                        endAngle: rArc.value,
                        startAngle: 0,
                    }))
                    .attr("fill", d => color(rColor.value))
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 2)

        const label = svgArc.append("g")
            .attr("pointer-events", "none")
            .append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .style("font", "4rem Arial")
            .style("fill", "#fff")
            .style("fill-opacity", 1)
            .attr("x", ArcConfig.width / 2 )
            .attr("y", ArcConfig.height / 2 + 10)
            .text(rTotal.value.toFixed(0));
    }
    onMounted(() => {
        rTotal.value = getTotalAvg(props.data) * 100
        rArc.value = getTotalAvg(props.data) * 2 * Math.PI
        rMaxItem.value = getHighestScoreItem(props.data)
        rColor.value = getcolorindex(rTotal.value)
        draw()
    })
</script>

<template>
    <div><span id="title">您的情绪化指数</span></div>
    <div ref="arcref"></div>
    <div>
        <span>您讨论的最令人情绪化的话题是</span>
        <span>{{ rMaxItem[0] }}</span>
        <span>情绪化指数为{{ rMaxItem[1] }}</span>
    </div>
</template>

<style scoped>
    #title {
        font-size: 1vw;
    }
    span {
        color: white;
        display: flex;
        flex-direction: column;
        justify-self: center;
    }
</style>