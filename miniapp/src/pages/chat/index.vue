<template>
  <view class="chat-page">
    <scroll-view
      class="message-list"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
    >
      <view class="message-list-inner">
        <view v-if="messages.length === 0" class="empty-state">
          <view class="empty-icon">🏥</view>
          <view class="empty-text">欢迎使用康伴AI助手，请输入您的健康问题</view>
        </view>

        <view
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-wrapper', msg.role]"
        >
          <view v-if="msg.role === 'user'" class="message user-message">
            <view class="message-content user-content">{{ msg.content }}</view>
            <view class="message-avatar">👤</view>
          </view>
          <view v-else class="message assistant-message">
            <view class="message-avatar">🤖</view>
            <view class="message-content assistant-content">{{ msg.content }}</view>
          </view>
        </view>

        <view v-if="loading" class="loading-wrapper">
          <view class="message assistant-message">
            <view class="message-avatar">🤖</view>
            <view class="message-content assistant-content loading-content">
              <view class="loading-dots">
                <view class="dot"></view>
                <view class="dot"></view>
                <view class="dot"></view>
              </view>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="input-area">
      <input
        class="chat-input"
        v-model="inputText"
        placeholder="请描述您的症状或问题..."
        :disabled="loading"
        confirm-type="send"
        @confirm="sendMessage"
      />
      <view
        :class="['send-btn', { disabled: !inputText.trim() || loading }]"
        @tap="sendMessage"
      >
        发送
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import api from '@/utils/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const loading = ref(false)
const sessionId = ref('')
const scrollTop = ref(0)

const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = scrollTop.value === 0 ? 1 : 0
    nextTick(() => {
      scrollTop.value = 999999
    })
  })
}

const createSession = async () => {
  try {
    const res: any = await api.post('/chat/session/create')
    sessionId.value = res.session_id || res.id || ''
  } catch {
    sessionId.value = ''
  }
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  loading.value = true

  try {
    if (!sessionId.value) {
      await createSession()
    }

    const res: any = await api.post('/chat/send', {
      message: text,
      agent_type: 'general',
      session_id: sessionId.value || undefined
    })

    const reply = res.response || res.content || res.message || '抱歉，我暂时无法回答，请稍后再试。'
    messages.value.push({ role: 'assistant', content: reply })

    if (res.session_id && !sessionId.value) {
      sessionId.value = res.session_id
    }
  } catch {
    messages.value.push({ role: 'assistant', content: '网络请求失败，请检查网络后重试。' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

watch(() => messages.value.length, () => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg-page);
}

.message-list {
  flex: 1;
  padding: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
}

.message-list-inner {
  padding-bottom: var(--spacing-sm);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: var(--spacing-sm);
}

.empty-text {
  font-size: 28rpx;
  color: var(--color-text-hint);
  text-align: center;
}

.message-wrapper {
  margin-bottom: var(--spacing-md);
  display: flex;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

.message {
  display: flex;
  align-items: flex-start;
  max-width: 80%;
}

.user-message {
  flex-direction: row-reverse;
}

.assistant-message {
  flex-direction: row;
}

.message-avatar {
  font-size: 40rpx;
  flex-shrink: 0;
  line-height: 1;
}

.user-message .message-avatar {
  margin-left: var(--spacing-sm);
}

.assistant-message .message-avatar {
  margin-right: var(--spacing-sm);
}

.message-content {
  padding: 20rpx 28rpx;
  border-radius: var(--radius-lg);
  font-size: 28rpx;
  line-height: 1.6;
  word-break: break-word;
}

.user-content {
  background: var(--color-primary);
  color: #ffffff;
  border-top-right-radius: var(--radius-xs);
}

.assistant-content {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border-top-left-radius: var(--radius-xs);
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.loading-wrapper {
  margin-bottom: var(--spacing-md);
  display: flex;
  justify-content: flex-start;
}

.loading-content {
  padding: 24rpx 32rpx;
}

.loading-dots {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: var(--color-text-hint);
  animation: dotBounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: 0s;
}

.dot:nth-child(2) {
  animation-delay: 0.16s;
}

.dot:nth-child(3) {
  animation-delay: 0.32s;
}

@keyframes dotBounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.input-area {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  padding-bottom: calc(var(--spacing-sm) + env(safe-area-inset-bottom));
  background: var(--color-bg-card);
  border-top: 2rpx solid var(--color-border);
  gap: var(--spacing-sm);
}

.chat-input {
  flex: 1;
  height: 72rpx;
  padding: 0 24rpx;
  background: var(--color-bg-page);
  border: 2rpx solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 28rpx;
  color: var(--color-text-primary);
}

.send-btn {
  flex-shrink: 0;
  height: 72rpx;
  padding: 0 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #ffffff;
  border-radius: var(--radius-md);
  font-size: 28rpx;
  font-weight: 500;
}

.send-btn.disabled {
  opacity: 0.5;
}
</style>
