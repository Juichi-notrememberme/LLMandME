<script setup>
    import { onMounted, ref, defineProps} from 'vue';
    import * as d3 from "d3";
    import keyword from '@/assets/data/keyword.json'
    const props = defineProps({
        data: {
            type: Object,
            required: false,
            default: () => keyword
        }
    });

    const Danref = ref(null);

    const config = ref({
    // 原始画布尺寸
    canvasWidth: 850,
    canvasHeight: 1120,
    
    display: {
        width: 800,// 最大宽度
        height: 900// 固定高度
    }
});

    const draw = () => {
        const { canvasWidth, canvasHeight, display } = config.value

        const color = d3.scaleLinear()
            .domain([0, 5])
            .range(["#ffffff", "#3fa885"])
            .interpolate(d3.interpolateHcl);

        const pink = d3.scaleLinear()
            .domain([0, 5])
            .range(["#ffffff", "#e85299"])
            .interpolate(d3.interpolateHcl);

        const pack = data => d3.pack()
            .size([canvasWidth, canvasHeight])
            .padding(3)
            (d3.hierarchy(data)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value));

        const root = pack(props.data);

        const svg = d3.select(Danref.value)
            .append("svg")
            .attr("viewBox", `0 150 ${canvasWidth} ${canvasHeight}`)
            .attr("preserveAspectRatio", "xMidYMid meet")
            .style("background", '#222')
            .style("cursor", "pointer")
            .style("margin", "0 auto")
            .style("width", "100%")
            .style("display", "block")


        const stem = svg.append("g")
            .attr("stroke", "#ffff")
            .attr("stroke-width", 0.6)
            .attr("fill", "none")
            .attr("class", "stem-line")
            .selectAll()
            .data(root.descendants().slice(1).filter(d => d.parent && d.parent.data.name == props.data.name))
            .join("path")
            .attr("d", d => {
                const startX = d.x;
                const startY = d.y;
                const endX = canvasWidth / 2;
                const endY = canvasHeight * 1.5;

                const controlX = (startX + endX) / 2 + (Math.random() * 150 - 50);
                const controlY = (startY + endY) / 2 + (Math.random() * 150 - 50);
                return `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`;
            });

        const branch = svg.append("g")
            .attr("stroke", pink(1))
            .attr("stroke-width", 0.5)
            .attr("fill", "none")
            .attr("class", "branch-line")
            .selectAll()
            .data(root.descendants().slice(1).filter(d => d.parent && d.parent.data.name !== props.data.name))
            .join("path")
            .attr("d", d => {
                const startX = d.x;
                const startY = d.y;
                const endX = d.parent.x;
                const endY = d.parent.y;

                const controlX = (startX + endX) / 2 + (Math.random() * 50 - 50);
                const controlY = (startY + endY) / 2 + (Math.random() * 50 - 50);
                return `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`;
            });

        const node = svg.append("g")
            .selectAll("circle")
            .data(root.descendants().slice(1).filter(d => d.parent && d.parent.data.name == props.data.name))
            .join("circle")
            .attr("fill", "#222")
            .attr("fill-opacity", 0.1)
            .attr("stroke", color(5))
            .attr("pointer-events", d => !d.children ? "none" : null)
            .attr("cx", d => d.x)
            .attr("cy", d => d.y)
            .attr("r", d => d.r)
            .on("mouseover", function() { d3.select(this).attr("stroke", "#fff"); })
            .on("mouseout", function() { d3.select(this).attr("stroke", color(4)); });

        const Parentslabel = svg.append("g")
            .style("font", " bolder 0.8vw sans-serif")
            .attr("pointer-events", "none")
            .selectAll("text")
            .data(root.descendants().slice(1).filter(d => d.parent && d.parent.data.name == props.data.name))
            .join("text")
            .attr("text-anchor", "middle")
            .style("fill", "#b74675")
            .style("fill-opacity", 0.75)
            .style("display", "inline")
            .attr("x", d => d.x)
            .attr("y", d => d.y - 15)
            .text(d => d.data.name)

        const childrelabel = svg.append("g")
            .style("font", "0.7vw sans-serif")
            .attr("pointer-events", "none")
            .selectAll("text")
            .data(root.descendants().slice(1).filter(d => d.parent && d.parent.data.name !== props.data.name))
            .join("text")
            .attr("text-anchor", "middle")
            .style("fill", color(2))
            .style("fill-opacity", 0.9)
            .attr("x", d => d.x)
            .attr("y", d => d.y)
            .text(d => d.data.name);

        
            
            
    }

    onMounted(() => {
        draw();
    });
</script>
<template>
    <div class="Dandelion">
        <div ref="Danref"></div>
    </div>
</template>
<style scoped>
    .Dandelion {
    width: 100%;
}
</style>