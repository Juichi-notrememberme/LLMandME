<script setup>
    import { onMounted, ref,defineProps} from 'vue';
    import bubbles from '@/assets/data/bubbles.json'
    import words from '@/assets/data/words.json'
    const props = defineProps({
        bubbles: {
            type: Object,
            required: false,
            default: () => bubbles
        },
        words: {
            type: Object,
            required: false,
            default: () => words
        }

    });

</script>

<template>
    <div>
        <div><span class="num">{{ props.words["total_value"] }}</span></div>
        <div>
            <pre>
{{"您和AI已经\n进行了 "+ props.bubbles["total"] +" 次对话，\n开启了 "+ props.bubbles["mapping"].length +" 个话题，\n总共聊了 "+ props.words["total_value"] + " 字。" }}
            </pre>
        </div>
    </div>
</template>

<style scoped>
    .num {
        color: #e85299;
    }
    pre {
        color: white;
        display: flex;
        justify-content: center;
    }
    span {
        color: white;
        display: flex;
        justify-content: center;
        font: 5vw "Arial";
        margin-bottom: 0.2vw;
    }
</style>