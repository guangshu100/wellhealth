<template>
  <view class="page">
    <!-- 顶部搜索栏 -->
    <view class="search-bar">
      <view class="search-box" @click="goToChat">
        <text class="search-icon">🔍</text>
        <text class="search-placeholder">搜索健康问题...</text>
      </view>
    </view>

    <!-- 健康状态卡片 -->
    <view class="health-card" v-if="patient && patient.basic_info">
      <view class="health-header">
        <view class="patient-info">
          <text class="name">{{ patient.basic_info.name }}</text>
          <text class="age">{{ patient.basic_info.age }}岁</text>
          <text class="gender">{{ patient.basic_info.gender === 'male' ? '男' : '女' }}</text>
        </view>
        <view class="health-score">
          <text class="score">健康评分</text>
          <text class="value">{{ healthScore }}</text>
        </view>
      </view>
      
      <!-- 疾病标签 -->
      <view class="disease-tags">
        <text class="tag" v-for="disease in patient.diseases" :key="disease.id">{{ disease.disease_name }}</text>
      </view>

      <!-- 今日关键指标 -->
      <view class="today-vitals">
        <view class="vital-item" v-for="vital in todayVitals" :key="vital.name">
          <text class="vital-name">{{ vital.name }}</text>
          <text class="vital-value" :style="{ color: vital.color }">{{ vital.value }}</text>
          <text class="vital-unit">{{ vital.unit }}</text>
        </view>
      </view>
    </view>

    <!-- 未绑定患者 -->
    <view class="bind-card" v-else>
      <view class="empty-box">
        <text class="empty-icon">📋</text>
        <text class="empty-text">未绑定健康档案</text>
      </view>
      <button class="btn-primary" @click="bindPatient">绑定健康档案</button>
    </view>

    <!-- 功能菜单 -->
    <view class="menu-grid">
      <view class="menu-item" @click="goToHealth">
        <view class="menu-icon">📋</view>
        <text class="menu-text">健康档案</text>
      </view>
      <view class="menu-item" @click="goToFamily">
        <view class="menu-icon">👨‍👩‍👧‍👦</view>
        <text class="menu-text">亲情账号</text>
      </view>
      <view class="menu-item" @click="goToRecipe">
        <view class="menu-icon">🍳</view>
        <text class="menu-text">拍照做菜</text>
      </view>
      <view class="menu-item" @click="goToHealthData">
        <view class="menu-icon">📊</view>
        <text class="menu-text">健康数据</text>
      </view>
      <view class="menu-item" @click="goToChat">
        <view class="menu-icon">🤖</view>
        <text class="menu-text">AI咨询</text>
      </view>
      <view class="menu-item" @click="goToPrediction">
        <view class="menu-icon">🔮</view>
        <text class="menu-text">健康预测</text>
      </view>
      <view class="menu-item" @click="goToSimulation">
        <view class="menu-icon">🎯</view>
        <text class="menu-text">干预预测</text>
      </view>
      <view class="menu-item" @click="goToReminder">
        <view class="menu-icon">💊</view>
        <text class="menu-text">用药提醒</text>
      </view>
      <view class="menu-item" @click="goToCalorie">
        <view class="menu-icon">🔥</view>
        <text class="menu-text">卡路里</text>
      </view>
    </view>

    <!-- AI推荐 -->
    <view class="section">
      <view class="section-title">
        <text>💡 健康推荐</text>
      </view>
      <view class="recommend-list">
        <view class="recommend-item" v-for="item in recommendations" :key="item.id" @click="viewDetail(item)">
          <view class="recommend-content">
            <text class="recommend-title">{{ item.title }}</text>
            <text class="recommend-desc">{{ item.content }}</text>
          </view>
          <text class="arrow">›</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { patientApi, knowledgeApi, vitalsApi } from '@/utils/api'

const patient = ref<any>(null)
const todayVitals = ref<any[]>([])
const recommendations = ref<any[]>([])
const healthScore = ref(85)
const isLoggedIn = ref(false)

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  const token = uni.getStorageSync('token')
  isLoggedIn.value = !!token
  
  if (!token) {
    loadDefaultData()
    return
  }
  
  try {
    // 获取患者信息
    const patientRes = await patientApi.getMyPatient()
    
    if (patientRes && Object.keys(patientRes).length > 0) {
      patient.value = patientRes
      
      if (patientRes.vitals && patientRes.vitals.length > 0) {
        todayVitals.value = formatVitals(patientRes.vitals)
      }
      
      calculateHealthScore(patientRes)
      
      // 获取推荐知识
      if (patientRes.patient_id) {
        try {
          const recRes = await knowledgeApi.getRecommendations(patientRes.patient_id)
          recommendations.value = recRes.recommendations || []
        } catch (e) {
          loadDefaultRecommendations()
        }
      } else {
        loadDefaultRecommendations()
      }
    } else {
      loadDefaultData()
    }
  } catch (e: any) {
    console.log('加载真实数据失败，使用默认数据', e)
    if (e.statusCode === 401) {
      // Token过期，清除登录状态
      uni.removeStorageSync('token')
      uni.removeStorageSync('userInfo')
      uni.reLaunch({ url: '/pages/login/login' })
      return
    }
    loadDefaultData()
  }
}

const loadDefaultData = () => {
  patient.value = null
  healthScore.value = 85
  todayVitals.value = []
  loadDefaultRecommendations()
}

const loadDefaultRecommendations = () => {
  recommendations.value = [
    { id: '1', title: '糖尿病饮食指南', content: '科学饮食，控制血糖从每一餐开始' },
    { id: '2', title: '高血压运动处方', content: '适合高血压患者的运动方案' },
    { id: '3', title: '正确测量血压', content: '掌握正确的血压测量方法' }
  ]
}

const formatVitals = (records: any[]) => {
  const map: Record<string, any> = {}
  const typeNames: Record<string, string> = {
    'blood_sugar': '血糖',
    'blood_pressure_systolic': '血压',
    'blood_pressure_diastolic': '血压',
    'heart_rate': '心率'
  }
  
  records.forEach(r => {
    const typeName = typeNames[r.vital_type] || r.vital_type
    if (r.vital_type === 'blood_pressure_systolic' || r.vital_type === 'blood_pressure_diastolic') {
      // 血压需要合并显示
      if (!map['blood_pressure']) {
        map['blood_pressure'] = { name: '血压', value: '', unit: 'mmHg', color: '#E6A23C' }
      }
      if (r.vital_type === 'blood_pressure_systolic') {
        map['blood_pressure'].systolic = r.value
      } else if (r.vital_type === 'blood_pressure_diastolic') {
        map['blood_pressure'].diastolic = r.value
      }
      if (map['blood_pressure'].systolic && map['blood_pressure'].diastolic) {
        map['blood_pressure'].value = map['blood_pressure'].systolic + '/' + map['blood_pressure'].diastolic
      }
    } else if (!map[r.vital_type]) {
      map[r.vital_type] = { name: typeName, value: r.value, unit: r.unit, color: '#67C23A' }
    }
  })
  return Object.values(map).slice(0, 4)
}

const calculateHealthScore = (patientData: any) => {
  // 简单计算健康评分
  let score = 85
  // 根据疾病数量扣分
  if (patientData.diseases) {
    score -= patientData.diseases.length * 5
  }
  // 根据vitals调整
  if (patientData.vitals) {
    patientData.vitals.forEach((v: any) => {
      if (v.vital_type === 'blood_sugar' && v.value > 7) score -= 5
      if (v.vital_type === 'blood_pressure_systolic' && v.value > 140) score -= 5
    })
  }
  healthScore.value = Math.max(60, Math.min(100, score))
}

const bindPatient = () => {
  uni.navigateTo({ url: '/pages/bind/bind' })
}

const goToChat = () => {
  uni.switchTab({ url: '/pages/chat/chat' })
}

const goToHealth = () => {
  uni.switchTab({ url: '/pages/health/health' })
}

const goToReport = () => {
  uni.navigateTo({ url: '/pages/report/report' })
}

const goToReminder = () => {
  uni.switchTab({ url: '/pages/reminder/reminder' })
}

const goToSimulation = () => {
  uni.navigateTo({ url: '/pages/simulation/simulation' })
}

const goToFamily = () => {
  uni.navigateTo({ url: '/pages/family/family' })
}

const goToRecipe = () => {
  uni.navigateTo({ url: '/pages/recipe/recipe' })
}

const goToHealthData = () => {
  uni.navigateTo({ url: '/pages/health-data/health-data' })
}

const goToPrediction = () => {
  uni.navigateTo({ url: '/pages/prediction/prediction' })
}

const goToCalorie = () => {
  uni.navigateTo({ url: '/pages/calorie/calorie' })
}

const viewDetail = (item: any) => {
  uni.navigateTo({
    url: `/pages/knowledge/detail?id=${item.id}&title=${item.title}`
  })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding: 20rpx;
}

.search-bar {
  padding: 20rpx 0;
}

.search-box {
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border-radius: 50rpx;
  padding: 20rpx 30rpx;
}

.search-icon {
  margin-right: 20rpx;
}

.search-placeholder {
  color: var(--color-text-secondary);
  font-size: 28rpx;
}

.health-card {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 20rpx;
  padding: 30rpx;
  color: var(--color-text-inverse);
  margin-bottom: 20rpx;
}

.health-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.patient-info {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.name {
  font-size: 36rpx;
  font-weight: bold;
}

.age, .gender {
  font-size: 24rpx;
  opacity: 0.9;
}

.health-score {
  text-align: center;
}

.score {
  display: block;
  font-size: 22rpx;
  opacity: 0.8;
}

.value {
  font-size: 44rpx;
  font-weight: bold;
}

.disease-tags {
  display: flex;
  gap: 10rpx;
  flex-wrap: wrap;
  margin-bottom: 20rpx;
}

.tag {
  background: rgba(255,255,255,0.3);
  color: #fff;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.today-vitals {
  display: flex;
  justify-content: space-around;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 15rpx;
  padding: 20rpx;
}

.vital-item {
  text-align: center;
}

.vital-name {
  display: block;
  font-size: 22rpx;
  opacity: 0.8;
  margin-bottom: 5rpx;
}

.vital-value {
  font-size: 32rpx;
  font-weight: bold;
}

.vital-unit {
  font-size: 20rpx;
  opacity: 0.8;
}

.bind-card {
  background: #FFFFFF;
  border-radius: 20rpx;
  padding: 60rpx 30rpx;
  text-align: center;
  margin-bottom: 20rpx;
}

.empty-box {
  margin-bottom: 30rpx;
}

.empty-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 20rpx;
}

.empty-text {
  color: var(--color-text-secondary);
  font-size: 28rpx;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: 50rpx;
  padding: 20rpx 60rpx;
  font-size: 28rpx;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15rpx;
  margin-bottom: 20rpx;
}

.menu-item {
  background: #FFFFFF;
  border-radius: 15rpx;
  padding: 30rpx 20rpx;
  text-align: center;
}

.menu-icon {
  font-size: 50rpx;
  margin-bottom: 10rpx;
}

.menu-text {
  font-size: 24rpx;
  color: var(--color-text-primary);
}

.section {
  background: #FFFFFF;
  border-radius: 15rpx;
  padding: 20rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 20rpx;
}

.recommend-item {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.recommend-item:last-child {
  border-bottom: none;
}

.recommend-content {
  flex: 1;
}

.recommend-title {
  display: block;
  font-size: 28rpx;
  color: var(--color-text-primary);
  margin-bottom: 8rpx;
}

.recommend-desc {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.arrow {
  color: var(--color-text-secondary);
  font-size: 32rpx;
}
</style>
