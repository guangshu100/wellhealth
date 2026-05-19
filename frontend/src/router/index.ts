import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { requiresAuth: false, title: '注册' }
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('@/views/ResetPasswordView.vue'),
    meta: { requiresAuth: false, title: '找回密码' }
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true, title: '首页' }
  },
  {
    path: '/patient',
    name: 'patient',
    component: () => import('@/views/PatientView.vue'),
    meta: { requiresAuth: true, title: '患者详情' }
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: true, title: 'AI咨询' }
  },
  {
    path: '/simulation',
    name: 'simulation',
    component: () => import('@/views/SimulationView.vue'),
    meta: { requiresAuth: true, title: '干预预测' }
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { requiresAuth: true, title: '管理后台', roles: ['admin'] }
  },
  {
    path: '/prescription',
    name: 'prescription',
    component: () => import('@/views/PrescriptionView.vue'),
    meta: { requiresAuth: true, title: '处方查询' }
  },
  {
    path: '/purchase',
    name: 'purchase',
    component: () => import('@/views/PurchaseView.vue'),
    meta: { requiresAuth: true, title: '购药记录' }
  },
  {
    path: '/patient-manage',
    name: 'patient-manage',
    component: () => import('@/views/PatientManageView.vue'),
    meta: { requiresAuth: true, title: '患者管理' }
  },
  {
    path: '/chronic',
    name: 'chronic',
    component: () => import('@/views/ChronicDiseaseView.vue'),
    meta: { requiresAuth: true, title: '慢病管理' }
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: () => import('@/views/KnowledgeView.vue'),
    meta: { requiresAuth: true, title: '知识库' }
  },
  {
    path: '/reminder',
    name: 'reminder',
    component: () => import('@/views/MedicationReminderView.vue'),
    meta: { requiresAuth: true, title: '用药提醒' }
  },
  {
    path: '/calorie',
    name: 'calorie',
    component: () => import('@/views/CalorieView.vue'),
    meta: { requiresAuth: true, title: '卡路里跟踪' }
  },
  {
    path: '/family',
    name: 'family',
    component: () => import('@/views/FamilyView.vue'),
    meta: { requiresAuth: true, title: '亲情账号' }
  },
  {
    path: '/recipe',
    name: 'recipe',
    component: () => import('@/views/RecipeView.vue'),
    meta: { requiresAuth: true, title: '拍照做菜' }
  },
  {
    path: '/health-data',
    name: 'health-data',
    component: () => import('@/views/HealthDataView.vue'),
    meta: { requiresAuth: true, title: '健康数据' }
  },
  {
    path: '/prediction',
    name: 'prediction',
    component: () => import('@/views/PredictionView.vue'),
    meta: { requiresAuth: true, title: '健康预测' }
  },
  {
    path: '/cognitive/assessment',
    name: 'cognitive-assessment',
    component: () => import('@/views/CognitiveAssessmentView.vue'),
    meta: { requiresAuth: true, title: '认知评估' }
  },
  {
    path: '/cognitive/training',
    name: 'cognitive-training',
    component: () => import('@/views/CognitiveTrainingView.vue'),
    meta: { requiresAuth: true, title: '认知训练' }
  },
  {
    path: '/cognitive/report',
    name: 'cognitive-report',
    component: () => import('@/views/CognitiveReportView.vue'),
    meta: { requiresAuth: true, title: '训练报告' }
  },
  {
    path: '/cognitive/training/memory-match',
    name: 'cognitive-memory-match',
    component: () => import('@/views/cognitive/MemoryMatchGame.vue'),
    meta: { requiresAuth: true, title: '记忆匹配' }
  },
  {
    path: '/cognitive/training/category-naming',
    name: 'cognitive-category-naming',
    component: () => import('@/views/cognitive/CategoryNamingGame.vue'),
    meta: { requiresAuth: true, title: '类别命名' }
  },
  {
    path: '/cognitive/training/sequence-sort',
    name: 'cognitive-sequence-sort',
    component: () => import('@/views/cognitive/SequenceSortGame.vue'),
    meta: { requiresAuth: true, title: '序列排序' }
  },
  {
    path: '/cognitive/training/word-recall',
    name: 'cognitive-word-recall',
    component: () => import('@/views/cognitive/WordRecallGame.vue'),
    meta: { requiresAuth: true, title: '词语回忆' }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true, title: '个人中心' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiredRoles = to.matched
    .filter(record => record.meta.roles)
    .flatMap(record => record.meta.roles as string[])

  if (requiresAuth) {
    if (!authStore.token) {
      next({ 
        path: '/login', 
        query: { redirect: to.fullPath }
      })
      return
    }

    if (requiredRoles.length > 0) {
      if (!requiredRoles.includes(authStore.userInfo?.role)) {
        next({ path: '/' })
        return
      }
    }
  }

  const demoStored = localStorage.getItem('demo_mode')
  const isDemoMode = demoStored !== null ? demoStored === 'true' : import.meta.env.VITE_DEMO_MODE === 'true'
  const demoHiddenPaths = ['/health-data', '/prediction', '/family', '/reminder', '/calorie', '/recipe', '/knowledge']
  if (isDemoMode && demoHiddenPaths.some(p => to.path.startsWith(p))) {
    next({ path: '/' })
    return
  }

  if (to.path === '/login' && authStore.token) {
    next({ path: '/' })
    return
  }

  next()
})

export default router
