<template>
  <div class="slider-captcha">
    <div class="captcha-header">
      <span class="title">请完成安全验证</span>
      <span class="refresh" @click="refresh">
        <el-icon><Refresh /></el-icon>
        刷新
      </span>
    </div>
    
    <div class="captcha-img" :style="{ width: width + 'px', height: height + 'px' }">
      <img 
        class="bg-img" 
        :src="captchaData.backgroundImage" 
        alt="验证码背景"
      />
      <div 
        class="slider-block"
        :style="{ 
          left: sliderX + 'px', 
          top: sliderY + 'px',
          transition: isDragging ? 'none' : 'left 0.3s ease'
        }"
      >
        <img 
          class="slider-img" 
          :src="captchaData.sliderImage" 
          alt="滑块"
        />
      </div>
    </div>
    
    <div 
      class="slider-track" 
      ref="trackRef"
      @mousedown="onMouseDown"
      @touchstart.prevent="onTouchStart"
    >
      <div class="track-line" :style="{ width: sliderX + 'px' }"></div>
      <div class="slider-btn" :style="{ left: sliderX + 'px' }">
        <el-icon><ArrowRight /></el-icon>
      </div>
    </div>
    
    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, ArrowRight } from '@element-plus/icons-vue'
import { getSliderCaptcha, verifySlider } from '@/api/captcha'

interface CaptchaData {
  captchaId: string
  backgroundImage: string
  sliderImage: string
  watermark: string
}

const props = defineProps({
  width: {
    type: Number,
    default: 300
  },
  height: {
    type: Number,
    default: 160
  }
})

const emit = defineEmits(['success', 'fail'])

const trackRef = ref<HTMLElement>()
const captchaData = ref<CaptchaData>({
  captchaId: '',
  backgroundImage: '',
  sliderImage: '',
  watermark: ''
})

const sliderX = ref(0)
const sliderY = ref(30)
const startX = ref(0)
const startY = ref(0)
const isDragging = ref(false)
const errorMsg = ref('')
const isVerified = ref(false)

const track = ref<{ x: number; y: number; t: number }[]>([])

onMounted(() => {
  refresh()
})

async function refresh() {
  try {
    const res = await getSliderCaptcha()
    captchaData.value = res
    sliderX.value = 0
    errorMsg.value = ''
    isVerified.value = false
  } catch (e: any) {
    ElMessage.error('加载失败')
  }
}

function onMouseDown(e: MouseEvent) {
  if (isVerified.value) return
  isDragging.value = true
  startX.value = e.clientX
  startY.value = e.clientY
  track.value = [{ x: 0, y: 0, t: Date.now() }]
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging.value || isVerified.value) return
  const diffX = e.clientX - startX.value
  const diffY = e.clientY - startY.value
  
  const newX = Math.max(0, Math.min(diffX, props.width - 50))
  sliderX.value = newX
  sliderY.value = 30 + Math.max(-15, Math.min(diffY, 15))
  
  track.value.push({ x: newX, y: diffY, t: Date.now() })
}

async function onMouseUp() {
  if (!isDragging.value || isVerified.value) return
  isDragging.value = false
  
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  
  await handleVerify()
}

function onTouchStart(e: TouchEvent) {
  if (isVerified.value) return
  isDragging.value = true
  startX.value = e.touches[0].clientX
  startY.value = e.touches[0].clientY
  track.value = [{ x: 0, y: 0, t: Date.now() }]
  
  document.addEventListener('touchmove', onTouchMove)
  document.addEventListener('touchend', onTouchEnd)
}

function onTouchMove(e: TouchEvent) {
  if (!isDragging.value || isVerified.value) return
  const currentX = e.touches[0].clientX
  const currentY = e.touches[0].clientY
  
  const diffX = currentX - startX.value
  const diffY = currentY - startY.value
  
  const newX = Math.max(0, Math.min(diffX, props.width - 50))
  sliderX.value = newX
  sliderY.value = 30 + Math.max(-15, Math.min(diffY, 15))
  
  track.value.push({ x: newX, y: diffY, t: Date.now() })
}

async function onTouchEnd() {
  if (!isDragging.value || isVerified.value) return
  isDragging.value = false
  
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
  
  await handleVerify()
}

async function handleVerify() {
  if (sliderX.value < 10) return
  
  try {
    const res = await verifySlider({
      captchaId: captchaData.value.captchaId,
      sliderImage: captchaData.value.sliderImage,
      X: sliderX.value,
      Y: sliderY.value - 30
    })
    
    if (res.result) {
      isVerified.value = true
      errorMsg.value = ''
      emit('success', captchaData.value.captchaId)
    } else {
      errorMsg.value = res.message || '验证失败'
      sliderX.value = 0
      sliderY.value = 30
      emit('fail', res.message)
    }
  } catch (e: any) {
    errorMsg.value = e.detail || '验证失败'
    sliderX.value = 0
    sliderY.value = 30
  }
}

defineExpose({ refresh })
</script>

<style scoped lang="scss">
.slider-captcha {
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.captch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .title {
    font-size: 14px;
    color: #333;
  }
  
  .refresh {
    font-size: 13px;
    color: #5E8B5A;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.captcha-img {
  position: relative;
  overflow: hidden;
  border-radius: 4px;
  background: #f5f5f5;
  
  .bg-img {
    width: 100%;
    height: 100%;
    display: block;
  }
  
  .slider-block {
    position: absolute;
    width: 50px;
    height: 40px;
    overflow: hidden;
    
    .slider-img {
      width: 100%;
      height: 100%;
    }
  }
}

.slider-track {
  position: relative;
  height: 40px;
  background: #f5f5f5;
  border-radius: 20px;
  margin-top: 16px;
  overflow: hidden;
  
  .track-line {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(to right, #67C23A, #85CE61);
    border-radius: 20px 0 0 20px;
  }
  
  .slider-btn {
    position: absolute;
    top: 2px;
    width: 36px;
    height: 36px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #5E8B5A;
  }
}

.error-msg {
  margin-top: 12px;
  font-size: 12px;
  color: #F56C6C;
  text-align: center;
}
</style>
