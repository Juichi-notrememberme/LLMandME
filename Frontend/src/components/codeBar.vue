<script setup>
    import { onMounted, ref,defineProps} from 'vue';
    import * as d3 from "d3";
    import code from "@/assets/data/code.json"
    const props = defineProps({
        data: {
            type: Object,
            required: false,
            default: () => code
        }
    });

    const map = props.data["codeMap"]

    const barref = ref(null)

    const config = {
        barHeight: 60,
        width: 928,
        margin: 10,
        height: Math.ceil((map.length + 0.1) * 60)
    }

    const draw = () => {
        const color = d3.scaleLinear()
                .domain([0, Math.max(1, map.length - 1)])
                .range(["#e85299", "#3fa885"])
                .interpolate(d3.interpolateHcl);

        const x = d3.scaleLinear()
            .domain([0, d3.max(map, d => d.value)])
            .range([config.margin, config.width - config.margin]);
  
        const y = d3.scaleBand()
            .domain(d3.sort(map, d => -d.value).map(d => d.codeType))
            .rangeRound([config.margin, config.height - config.margin])
            .padding(0.1);

        const svg = d3.select(barref.value)
        .append("svg")
        .attr("viewBox", [0, 0, config.width, config.height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

        const rect = svg.append("g")
            .selectAll()
            .data(map)
            .join("rect")
            .attr("x", x(0))
            .attr("y", (d) => y(d.codeType))
            .attr("width", (d) => x(d.value) - x(0))
            .attr("height", y.bandwidth())
            .attr("fill", (d, i) => color(i))

        const label = svg.append("g")
            .attr("fill", "white")
            .attr("text-anchor", "end")
            .selectAll()
            .data(map)
            .join("text")
            .attr("x", (d) => x(d.value))
            .attr("y", (d) => y(d.codeType) + y.bandwidth() / 2)
            .attr("dy", "0.35em")
            .attr("dx", -4)
            .text((d) => d.codeType +" "+ d.value)
            .call((text) => text.filter(d => x(d.value) - x(0) < config.width /2) // short bars
            .attr("dx", +4)
            .attr("fill", "white")
            .attr("text-anchor", "start"))
            .style("font", "3vw sans-serif");

        svg.append("g")
            .attr("transform", `translate(0,${config.margin})`)
            .call(d3.axisTop(x).ticks(config.width / 80, "%"))
            .call(g => g.select(".domain").remove());

        svg.append("g")
            .attr("transform", `translate(${config.margin},0)`)
            .call(d3.axisLeft(y).tickSizeOuter(0));
    }

    onMounted(() => {
        draw()
    })
</script>

<template>
    <div ref="barref"></div>
    <div>
        <p>您让AI写了{{ props.data["total"] }}行代码</p>
        <p>您让AI写的最多的语言是{{ props.data["codeMap"][0]["codeType"] }}</p>
    </div>
</template>

<style scoped>
    p {
        color: white;
        display: flex;
        justify-content: center;
        font: "Arial";
        margin-bottom: 0.2vw;
    }
</style>