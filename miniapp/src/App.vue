<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'

onLaunch(() => {
  const auth = useAuthStore()
  auth.init()
})
</script>

<style>
@import './static/styles/index.scss';
</style>
