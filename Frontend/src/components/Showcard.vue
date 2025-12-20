<script setup>
    import Dandelion from './Dandelion.vue';
    import mood from './mood.vue';
    import SankeyTime from './SankeyTime.vue';
    import plainInfo from './plainInfo.vue';
    import codeBar from './codeBar.vue';
    import {defineProps} from 'vue';
    const props = defineProps({
        data: {
            type: Object,
            required: false,
            default: () => []
        }
    });
</script>

<template>
    <div id="card">
        <div class="column0" id="Ac">
            <Dandelion :data="props.data[5]"/>
        </div>
        <div class="column1" id="Bc">
            <plainInfo :bubbles="props.data[2]" :words="props.data[1]"/>
            <mood :data="props.data[4]"/>
            <codeBar :data="props.data[3]"/>
        </div>
        <div class="column2" id="Cc">
            <SankeyTime :data="props.data[0]"/>
        </div>
    </div>
</template>

<style scoped>
    #card {
        width: 100%;
        display: flex;
        flex-direction: row;
        justify-content: center;
    }
    .column0 {
        width: 43vw;
        height: 40vh;
        margin: 0.4vw;
    }
    .column1 {
        width: 17vw;
        height: 40vh;
        margin: 0.4vw;
    }
    .column2 {
        width: 42vw;
        height: 40vh;
        margin: 0.4vw;
    }
</style>