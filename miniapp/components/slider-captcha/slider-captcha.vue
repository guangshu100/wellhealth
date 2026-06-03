<template>
  <view class="slider-captcha">
    <view class="captcha-header">
      <text class="title">请完成安全验证</text>
      <text class="refresh" @click="refresh">刷新</text>
    </view>
    
    <view class="captcha-img" :style="{ width: width + 'px', height: height + 'px' }">
      <image 
        class="bg-img" 
        :src="captchaData.backgroundImage" 
        mode="aspectFill"
      />
      <view 
        class="slider-block"
        :style="{ 
          left: sliderX + 'px', 
          top: sliderY + 'px',
          transition: isDragging ? 'none' : 'left 0.3s ease'
        }"
      >
        <image 
          class="slider-img" 
          :src="captchaData.sliderImage" 
          mode="aspectFit"
        />
      </view>
    </view>
    
    <view class="slider-track" @touchstart="onTouchStart" @touchmove="onTouchMove" @touchend="onTouchEnd">
      <view class="track-line" :style="{ width: sliderX + 'px' }"></view>
      <view class="slider-btn" :style="{ left: sliderX + 'px' }">
        <text class="arrow">→</text>
      </view>
    </view>
    
    <view v-if="errorMsg" class="error-msg">{{ errorMsg }}</view>
  </view>
</template>

<script>
import { captchaApi } from '@/utils/api'

export default {
  name: 'SliderCaptcha',
  props: {
    width: {
      type: Number,
      default: 280
    },
    height: {
      type: Number,
      default: 150
    },
    onSuccess: {
      type: Function,
      default: () => {}
    },
    onFail: {
      type: Function,
      default: () => {}
    }
  },
  data() {
    return {
      captchaData: {
        captchaId: '',
        backgroundImage: '',
        sliderImage: '',
        watermark: ''
      },
      sliderX: 0,
      sliderY: 30,
      startX: 0,
      startY: 0,
      isDragging: false,
      errorMsg: '',
      track: [],
      isVerified: false
    }
  },
  mounted() {
    this.refresh()
  },
  methods: {
    async refresh() {
      try {
        uni.showLoading({ title: '加载中' })
        const res = await captchaApi.getSliderCaptcha()
        this.captchaData = res
        this.sliderX = 0
        this.errorMsg = ''
        this.isVerified = false
        uni.hideLoading()
      } catch (e) {
        uni.hideLoading()
        uni.showToast({ title: '加载失败', icon: 'none' })
      }
    },
    onTouchStart(e) {
      if (this.isVerified) return
      this.isDragging = true
      this.startX = e.touches[0].clientX
      this.startY = e.touches[0].clientY
      this.track = [{ x: 0, y: 0, t: Date.now() }]
    },
    onTouchMove(e) {
      if (!this.isDragging || this.isVerified) return
      const currentX = e.touches[0].clientX
      const currentY = e.touches[0].clientY
      const diffX = currentX - this.startX
      const diffY = currentY - this.startY
      
      let newX = Math.max(0, Math.min(diffX, this.width - 50))
      this.sliderX = newX
      this.sliderY = 30 + Math.max(-15, Math.min(diffY, 15))
      
      this.track.push({ x: newX, y: diffY, t: Date.now() })
    },
    async onTouchEnd() {
      if (!this.isDragging || this.isVerified) return
      this.isDragging = false
      
      if (this.sliderX < 10) {
        return
      }
      
      try {
        uni.showLoading({ title: '验证中' })
        const res = await captchaApi.verifySlider({
          captchaId: this.captchaData.captchaId,
          sliderImage: this.captchaData.sliderImage,
          X: this.sliderX,
          Y: this.sliderY - 30
        })
        uni.hideLoading()
        
        if (res.result) {
          this.isVerified = true
          this.errorMsg = ''
          this.$emit('success', this.captchaData.captchaId)
          this.onSuccess(this.captchaData.captchaId)
        } else {
          this.errorMsg = res.message || '验证失败'
          this.sliderX = 0
          this.sliderY = 30
          this.$emit('fail', res.message)
          this.onFail(res.message)
        }
      } catch (e) {
        uni.hideLoading()
        this.errorMsg = e.detail || '验证失败'
        this.sliderX = 0
        this.sliderY = 30
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.slider-captcha {
  padding: 20rpx;
  background: #fff;
  border-radius: 12rpx;
}

.captcha-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
  
  .title {
    font-size: 28rpx;
    color: #333;
  }
  
  .refresh {
    font-size: 24rpx;
    color: #5E8B5A;
  }
}

.captcha-img {
  position: relative;
  overflow: hidden;
  border-radius: 8rpx;
  background: #f5f5f5;
  
  .bg-img {
    width: 100%;
    height: 100%;
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
  height: 60rpx;
  background: #f5f5f5;
  border-radius: 30rpx;
  margin-top: 20rpx;
  overflow: hidden;
  
  .track-line {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(to right, #67C23A, #85CE61);
    border-radius: 30rpx 0 0 30rpx;
  }
  
  .slider-btn {
    position: absolute;
    top: 5rpx;
    width: 50rpx;
    height: 50rpx;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    
    .arrow {
      color: #5E8B5A;
      font-size: 24rpx;
    }
  }
}

.error-msg {
  margin-top: 15rpx;
  font-size: 24rpx;
  color: #F56C6C;
  text-align: center;
}
</style>
