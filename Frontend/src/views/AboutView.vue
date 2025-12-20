<script setup>
  import { onMounted, ref } from 'vue';

  const message = ref('正在等待后厨的数据...')
  // 当页面加载时，去问后端要数据
onMounted(async () => {
  try {
    // 这里填你 FastAPI 的地址
    const response = await fetch('http://127.0.0.1:8000/items/1')
    const data = await response.json()
    message.value = data.name
  } catch (error) {
    message.value = '后厨好像没开火（连接失败）'
  }
})
</script>

<template>
  <div class="about">
    <h1>这是关于页面</h1>
    <p>这里展示的是另外一个路径的内容。</p>
    <p>{{ message }}</p>
  </div>
</template>

<style>
@media (min-width: 1024px) {
  .about {
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
}
</style>
