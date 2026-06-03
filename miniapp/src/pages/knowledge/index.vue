<template>
  <view class="page">
    <view class="card">
      <view class="search-bar flex-row gap-sm">
        <input class="input-field" style="flex:1" v-model="searchQuery" placeholder="搜索健康知识" @confirm="handleSearch" />
        <view class="btn-primary" @tap="handleSearch">
          <text style="color:#fff">搜索</text>
        </view>
      </view>
    </view>

    <scroll-view scroll-x class="category-scroll">
      <view class="flex-row gap-sm" style="padding:0 var(--spacing-md)">
        <view
          v-for="cat in categories"
          :key="cat.value"
          class="category-item"
          :class="{ active: activeCategory === cat.value }"
          @tap="switchCategory(cat.value)"
        >
          <text>{{ cat.icon }} {{ cat.label }}</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="loading" class="flex-center mt-md">
      <text class="text-hint">加载中...</text>
    </view>

    <view v-if="!loading && articles.length === 0" class="empty-state mt-md">
      <text class="empty-icon">📚</text>
      <text class="empty-text">暂无知识文章</text>
    </view>

    <view v-for="article in articles" :key="article.id" class="card article-card" @tap="viewArticle(article)">
      <text class="article-title text-primary">{{ article.title }}</text>
      <text class="article-summary text-secondary mt-sm">{{ truncate(article.content, 80) }}</text>
      <view class="flex-row flex-between mt-sm">
        <view class="flex-row gap-xs">
          <text v-if="article.type" class="tag tag-primary">{{ article.type }}</text>
          <text v-for="tag in (article.tags || []).slice(0, 2)" :key="tag" class="tag tag-info">{{ tag }}</text>
        </view>
        <text class="text-hint" style="font-size:22rpx">{{ formatDate(article.published_at || article.created_at) }}</text>
      </view>
    </view>

    <view v-if="hasMore && articles.length > 0" class="flex-center mt-md mb-md">
      <view class="btn-text" @tap="loadMore"><text>加载更多</text></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

const searchQuery = ref('')
const activeCategory = ref('')
const articles = ref<any[]>([])
const loading = ref(false)
const hasMore = ref(false)
const currentPage = ref(1)
const pageSize = 10

const categories = [
  { value: '', label: '全部', icon: '📋' },
  { value: 'diabetes', label: '糖尿病', icon: '🩸' },
  { value: 'hypertension', label: '高血压', icon: '💓' },
  { value: 'nutrition', label: '营养饮食', icon: '🥗' },
  { value: 'exercise', label: '运动康复', icon: '🏃' },
  { value: 'medication', label: '用药指导', icon: '💊' },
  { value: 'mental_health', label: '心理健康', icon: '🧠' },
]

const truncate = (str: string, len: number) => {
  if (!str) return ''
  return str.length > len ? str.substring(0, len) + '...' : str
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}

const fetchArticles = async (page: number = 1, append: boolean = false) => {
  loading.value = true
  try {
    const params: any = {
      page,
      page_size: pageSize,
    }
    if (searchQuery.value) params.search = searchQuery.value
    if (activeCategory.value) params.type = activeCategory.value

    const res: any = await api.get('/knowledge/', params)
    const items = res.items || []
    if (append) {
      articles.value = [...articles.value, ...items]
    } else {
      articles.value = items
    }
    hasMore.value = items.length >= pageSize
    currentPage.value = page
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchArticles(1, false)
}

const switchCategory = (value: string) => {
  activeCategory.value = value
  currentPage.value = 1
  fetchArticles(1, false)
}

const loadMore = () => {
  fetchArticles(currentPage.value + 1, true)
}

const viewArticle = (article: any) => {
  uni.navigateTo({ url: `/pages/knowledge/detail?id=${article.id}` })
}

onMounted(() => {
  fetchArticles()
})
</script>

<style scoped>
.search-bar {
  align-items: center;
}

.category-scroll {
  white-space: nowrap;
  margin-bottom: var(--spacing-md);
}

.category-item {
  display: inline-block;
  padding: 12rpx 24rpx;
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  font-size: 24rpx;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.category-item.active {
  background: var(--color-primary);
  color: #fff;
}

.article-card {
  padding: var(--spacing-md);
}

.article-title {
  font-size: 30rpx;
  font-weight: 600;
  line-height: 1.5;
}

.article-summary {
  font-size: 24rpx;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
</style>
