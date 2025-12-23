<script setup>
    import { ref, defineEmits } from 'vue';

    const fileInput = ref(null)
    const isLoading = ref(false)
    const acceptFile = ref([])
    const isDragging = ref(null)
    //emit传参
    const emit = defineEmits(['data_sent'])
    const datasending = () => {
        emit('data_sent', acceptFile.value)
    }

    //接受文件的函数
    const uploadFile = async (file) => {
        //防呆
        if (!file) return

        if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
            alert('请上传 .zip 格式的单个文件！')
            return
        }

        const fileForm = new FormData()
        fileForm.append('file', file)

        isLoading.value = true
        acceptFile.value = []

        try {
            const response = await fetch('http://127.0.0.1:8000/upload_zip/',{
                method: 'POST',
                body: fileForm
            })
            const data = await response.json()

            if (data.status === 'success'){
                acceptFile.value = data.files
            } else {
                alert('解析出错' + data.error)
            }
        } catch(error){
            alert('upload fail ' + error)
        } finally {
            isLoading.value = false
            datasending()
            if (fileInput.value) {
                fileInput.value.value = '' 
            }
        }

        
    }

    const handleInputChange = (event) => {
        const file = event.target.files[0]
        uploadFile(file)
        // 选完文件后，清空 input，防止选中同名文件不触发 change
        event.target.value = ''
    }

    const handleDragLeave = (e) => {
        // 离开拖拽区域
        isDragging.value = false
    }
    const handleDragOver = (e) => {
        isDragging.value = true
    }

    const handleDrop = (e) => {
        isDragging.value = false
        // 获取拖进来的文件列表
        const file = e.dataTransfer.files[0]
        uploadFile(file)
    }
    const triggerFileInput = () => {
        fileInput.value.click()
    }

</script>
<template>
    <div 
        class="upload-area"
        :class="{'active': isDragging}"
        @click="triggerFileInput"
        @dragover.prevent="handleDragOver" 
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
    >
        <p>
            <span v-if="!isLoading">please upload one AI's zip (ChatGPT or deepseek)</span>
            <span v-else>loading...</span>
        </p>
        <input 
            ref="fileInput"
            type="file"
            accept=".zip"
            @change="handleInputChange"
            style="display: none;"
        />
    </div>
</template>
<style scoped>
    .upload-area { 
        border: 2px dashed #999; 
        color: #fff;
        padding: 40px; 
        text-align: center; 
        margin-bottom: 20px; 
        border-radius: 10px;
        cursor: pointer; /* 鼠标放上去变小手 */
        transition: all 0.3s ease; /* 动画过渡 */
        background-color: #444;
        }

/* 当正在拖拽时，应用这个样式 */
    .upload-area.active {
        border-color: #fff;
        background-color: #4CAF50;
        transform: scale(1.02); /* 稍微放大一点点 */
    }

/* 即使不是拖拽，鼠标悬停时也给点反馈 */
    .upload-area:hover {
        border-color: #fff;
    }
</style>