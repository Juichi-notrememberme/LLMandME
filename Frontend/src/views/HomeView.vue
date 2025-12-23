<script setup>
  import FileAcceptor from '@/components/FileAcceptor.vue';
  import Showcard from '@/components/Showcard.vue';
  import { ref, defineProps } from 'vue'

  const dataTransfer = ref([])

  const isSent = ref(false)

  const handleData = (amount) =>{
    dataTransfer.value = amount
    if (amount) {
      isSent.value = true
    }
  }
</script>

<template>
  <header v-if="!isSent">
    <div id="header" >
      <FileAcceptor @data_sent="handleData"/>
      <p id="title">Liter<span id="greentitle">Oasis</span></p>
    </div>
  </header>
  <main v-if="isSent">
    <Showcard :data="dataTransfer"/>      
  </main>
</template>

<style scoped>
header {
  height: 100vh; /* 关键：占据 100% 视口高度 */
  width: 100vw;  /* 占据 100% 视口宽度 */
  display: flex; 
  justify-content: center; /* 水平居中 */
  align-items: center;     /* 垂直居中 */
}
#header {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: row;
  gap: 0.5vw;
  padding-bottom: 3.5vw;
}
#title {
    margin-bottom: 0rem;
    color: white;
    margin-left: 0.5vh;
    font-size: 10vh;
    font-weight: bold;
    font-family: Arial, Helvetica, sans-serif;
}
#greentitle {
    margin-bottom: 0rem;
    color: #4CAF50;
    font-size: 10vh;
    font-weight: bold;
    font-family: Arial, Helvetica, sans-serif;
}
</style>