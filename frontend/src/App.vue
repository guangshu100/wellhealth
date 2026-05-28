<template>
  <div id="app">
    <!-- 顶部导航 - 仅登录后显示 -->
    <div v-if="isLoggedIn" class="navbar">
      <div class="navbar-left">
        <router-link to="/" class="logo">
          <img src="@/assets/images/logo.png" alt="康伴" class="logo-img" />
          <span class="logo-text">康伴</span>
        </router-link>
      </div>
      
      <div class="navbar-menu">
        <router-link to="/" class="menu-item" :class="{ active: $route.path === '/' }">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </router-link>

        <router-link to="/chat" class="menu-item" :class="{ active: $route.path === '/chat' }">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI问答</span>
        </router-link>

        <el-dropdown v-if="!isDemoMode" trigger="hover" class="menu-dropdown">
          <router-link to="/health-data" class="menu-item">
            <el-icon><FirstAidKit /></el-icon>
            <span>健康管理</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </router-link>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/health-data">
                  <el-icon><DataAnalysis /></el-icon>
                  健康数据
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/prediction">
                  <el-icon><TrendCharts /></el-icon>
                  健康预测
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/reminder">
                  <el-icon><Bell /></el-icon>
                  用药提醒
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/chronic">
                  <el-icon><Sugar /></el-icon>
                  慢病管理
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/calorie">
                  <el-icon><Food /></el-icon>
                  卡路里跟踪
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/family">
                  <el-icon><UserFilled /></el-icon>
                  亲情守护
                </router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown v-if="!isDemoMode" trigger="hover" class="menu-dropdown">
          <router-link to="/cognitive/assessment" class="menu-item">
            <el-icon><DataAnalysis /></el-icon>
            <span>认知健康</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </router-link>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/cognitive/assessment">
                  <el-icon><DataAnalysis /></el-icon>
                  认知评估
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/cognitive/training">
                  <el-icon><TrendCharts /></el-icon>
                  认知训练
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/cognitive/report">
                  <el-icon><Sugar /></el-icon>
                  训练报告
                </router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown v-if="!isDemoMode" trigger="hover" class="menu-dropdown">
          <router-link to="/recipe" class="menu-item">
            <el-icon><Food /></el-icon>
            <span>生活服务</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </router-link>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/recipe">
                  <el-icon><Food /></el-icon>
                  拍照做菜
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/knowledge">
                  <el-icon><Reading /></el-icon>
                  知识库
                </router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="hover" class="menu-dropdown">
          <router-link to="/prescription" class="menu-item">
            <el-icon><Document /></el-icon>
            <span>医疗数据</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </router-link>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/prescription">
                  <el-icon><Document /></el-icon>
                  处方查询
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/purchase">
                  <el-icon><ShoppingCart /></el-icon>
                  购药记录
                </router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown v-if="!isDemoMode" trigger="hover" class="menu-dropdown">
          <router-link to="/prescription-review" class="menu-item">
            <el-icon><Cpu /></el-icon>
            <span>智能医疗</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </router-link>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/simulation">
                  <el-icon><Cpu /></el-icon>
                  干预模拟
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/prescription-review">
                  <el-icon><Document /></el-icon>
                  处方审核
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/patient-profile">
                  <el-icon><DataAnalysis /></el-icon>
                  患者画像
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/data-insight">
                  <el-icon><TrendCharts /></el-icon>
                  数据洞察
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/health-plan">
                  <el-icon><FirstAidKit /></el-icon>
                  健康计划
                </router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown v-if="!isDemoMode" trigger="hover" class="menu-dropdown">
          <router-link to="/patient-manage" class="menu-item">
            <el-icon><User /></el-icon>
            <span>管理中心</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </router-link>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/patient-manage">
                  <el-icon><User /></el-icon>
                  患者管理
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/dashboard">
                  <el-icon><DataAnalysis /></el-icon>
                  管理大屏
                </router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/admin">
                  <el-icon><Setting /></el-icon>
                  系统管理
                </router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="navbar-right">
        <el-dropdown @command="handleCommand">
          <div class="user-info">
            <el-icon><User /></el-icon>
            <span>{{ authStore.userInfo?.name || '用户' }}</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人中心
              </el-dropdown-item>
              <el-dropdown-item command="theme" divided>
                <el-icon><Brush /></el-icon>
                切换主题
              </el-dropdown-item>
              <el-dropdown-item command="demo" divided>
                <el-icon><component :is="isDemoMode ? View : Hide" /></el-icon>
                {{ isDemoMode ? '开发模式' : '演示模式' }}
              </el-dropdown-item>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主内容区 -->
    <div v-if="isLoggedIn" class="main-content">
      <router-view />
    </div>
    <router-view v-else />

    <!-- 底部版权 - 仅登录后显示 -->
    <div v-if="isLoggedIn" class="footer">
      <span>© 2024 康伴(WellHealth) - 慢性疾病管理AI平台</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { HomeFilled, User, ChatDotRound, Cpu, Setting, Reading, Document, ShoppingCart, Bell, ArrowDown, Sugar, UserFilled, DataAnalysis, TrendCharts, Food, FirstAidKit, SwitchButton, Brush, View, Hide } from '@element-plus/icons-vue'

const getDemoModeDefault = () => {
  const stored = localStorage.getItem('demo_mode')
  if (stored !== null) return stored === 'true'
  return import.meta.env.VITE_DEMO_MODE === 'true'
}

const isDemoMode = ref(getDemoModeDefault())

const toggleDemoMode = () => {
  isDemoMode.value = !isDemoMode.value
  localStorage.setItem('demo_mode', String(isDemoMode.value))
  ElMessage.success(isDemoMode.value ? '已切换为演示模式（部分菜单已隐藏）' : '已切换为开发模式（所有菜单可见）')
}

const router = useRouter()
const authStore = useAuthStore()

// 页面加载时应用保存的主题
onMounted(() => {
  const savedTheme = localStorage.getItem('app-theme')
  if (savedTheme && savedTheme !== 'sagegreen') {
    applyTheme(savedTheme)
  }
})

function applyTheme(themeId: string) {
  const root = document.documentElement
  const themeColors: Record<string, Record<string, string>> = {
    mistblue: {
      '--color-primary': '#7BA7B9',
      '--color-primary-light': '#9BC0CF',
      '--color-primary-dark': '#5E8B9A',
      '--color-bg-page': '#F5F9FB',
      '--color-bg-card': '#FFFFFF',
      '--color-bg-hover': '#E8F0F5',
      '--color-secondary': '#B8CDD8',
      '--color-accent': '#E7B83E',
      '--color-danger': '#CD8B5B',
      '--color-text-primary': '#2C3E50',
      '--color-text-secondary': '#6B7C8A',
      '--color-border': '#B8CDD8',
      '--el-color-primary': '#7BA7B9',
      '--el-color-success': '#7BA7B9',
      '--el-color-warning': '#E7B83E',
      '--el-color-danger': '#CD8B5B',
      '--el-bg-color': '#F5F9FB',
      '--el-text-color-regular': '#2C3E50',
    }
  }
  
  const colors = themeColors[themeId]
  if (colors) {
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })
  }
}

const isLoggedIn = computed(() => !!authStore.token)

async function handleCommand(command: string) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      authStore.logout()
      router.push('/login')
    } catch {
      // 用户取消
    }
  } else if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'theme') {
    showThemeSelector()
  } else if (command === 'demo') {
    toggleDemoMode()
  }
}

function showThemeSelector() {
  ElMessageBox.confirm(
    '<div style="text-align: center;"><p>选择主题风格</p></div>',
    '切换主题',
    {
      confirmButtonText: '鼠尾草绿',
      cancelButtonText: '柔雾蓝',
      distinguishCancelAndClose: true,
      dangerouslyUseHTMLString: true
    }
  ).then(() => {
    switchTheme('sagegreen')
  }).catch((action) => {
    if (action === 'cancel') {
      switchTheme('mistblue')
    }
  })
}

function switchTheme(themeId: string) {
  const themeConfig: Record<string, { colors: Record<string, string>; replacements: Record<string, string> }> = {
    sagegreen: {
      colors: {
        '--color-primary': '#5E8B5A',
        '--color-primary-light': '#7CA878',
        '--color-primary-dark': '#4C7048',
        '--color-bg-page': '#FCF8F0',
        '--color-bg-card': '#FFFFFF',
        '--color-bg-hover': '#E8F0E6',
        '--color-secondary': '#DDCFB0',
        '--color-accent': '#E7B83E',
        '--color-danger': '#CD8B5B',
        '--color-text-primary': '#2F2E2A',
        '--color-text-secondary': '#7F7D74',
        '--color-border': '#DDCFB0',
        '--el-color-primary': '#5E8B5A',
        '--el-color-success': '#5E8B5A',
        '--el-color-warning': '#E7B83E',
        '--el-color-danger': '#CD8B5B',
        '--el-bg-color': '#FCF8F0',
        '--el-text-color-regular': '#2F2E2A',
      },
      replacements: {
        '#7BA7B9': '#5E8B5A',
        '#9BC0CF': '#7CA878',
        '#5E8B9A': '#4C7048',
        '#B8CDD8': '#DDCFB0',
        '#F5F9FB': '#FCF8F0',
        '#E8F0F5': '#E8F0E6',
        '#2C3E50': '#2F2E2A',
        '#6B7C8A': '#7F7D74',
      }
    },
    mistblue: {
      colors: {
        '--color-primary': '#7BA7B9',
        '--color-primary-light': '#9BC0CF',
        '--color-primary-dark': '#5E8B9A',
        '--color-bg-page': '#F5F9FB',
        '--color-bg-card': '#FFFFFF',
        '--color-bg-hover': '#E8F0F5',
        '--color-secondary': '#B8CDD8',
        '--color-accent': '#E7B83E',
        '--color-danger': '#CD8B5B',
        '--color-text-primary': '#2C3E50',
        '--color-text-secondary': '#6B7C8A',
        '--color-border': '#B8CDD8',
        '--el-color-primary': '#7BA7B9',
        '--el-color-success': '#7BA7B9',
        '--el-color-warning': '#E7B83E',
        '--el-color-danger': '#CD8B5B',
        '--el-bg-color': '#F5F9FB',
        '--el-text-color-regular': '#2C3E50',
      },
      replacements: {
        '#5E8B5A': '#7BA7B9',
        '#7CA878': '#9BC0CF',
        '#4C7048': '#5E8B9A',
        '#DDCFB0': '#B8CDD8',
        '#FCF8F0': '#F5F9FB',
        '#E8F0E6': '#E8F0F5',
        '#2F2E2A': '#2C3E50',
        '#7F7D74': '#6B7C8A',
      }
    }
  }
  
  const config = themeConfig[themeId]
  if (!config) return
  
  // 1. 设置 CSS 变量
  const root = document.documentElement
  Object.entries(config.colors).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
  
  // 2. 替换页面中所有硬编码的颜色
  setTimeout(() => {
    const styleElements = document.querySelectorAll('style')
    styleElements.forEach((styleEl: any) => {
      if (styleEl.textContent) {
        let content = styleEl.textContent
        Object.entries(config.replacements).forEach(([oldColor, newColor]) => {
          content = content.replace(new RegExp(oldColor, 'g'), newColor)
        })
        styleEl.textContent = content
      }
    })
  }, 100)
  
  // 3. 保存主题并提示
  localStorage.setItem('app-theme', themeId)
  ElMessage.success(`已切换到${themeId === 'sagegreen' ? '鼠尾草绿' : '柔雾蓝'}主题`)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background-color: var(--color-bg-page, #FCF8F0);
}

/* 导航栏 */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 30px;
  background: linear-gradient(135deg, #5E8B5A, #7CA878);
  color: white;
  box-shadow: 0 2px 8px rgba(60, 55, 45, 0.1);
}

.navbar-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: bold;
  color: white;
  text-decoration: none;
  cursor: pointer;
}

.logo-img {
  height: 36px;
  width: auto;
  border-radius: 6px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
}

.navbar-menu {
  display: flex;
  gap: 10px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.3s;
  font-size: 14px;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.2);
}

.menu-item.active {
  background: rgba(255, 255, 255, 0.3);
  font-weight: 600;
}

.menu-dropdown {
  display: inline-flex;
}

.menu-dropdown .menu-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  cursor: pointer;
}

/* 主内容区 */
.main-content {
  padding-top: 60px;
  min-height: calc(100vh - 60px);
}

/* 底部 */
.footer {
  text-align: center;
  padding: 20px;
  color: #7F7D74;
  font-size: 13px;
  background: #FFFFFF;
  border-top: 1px solid #DDCFB0;
  margin-top: auto;
}
</style>
