<script>
import { getThemeId, getThemeCSS } from '@/utils/theme.js'

export default {
	data() {
		return {
			themeId: 'sagegreen'
		}
	},
	onLaunch: function() {
		console.log('App Launch')
		this.initTheme()
		this.checkLogin()
	},
	onShow: function() {
		// 每次显示时检查主题变化和登录状态
		this.applyTheme()
		this.checkLogin()
	},
	onHide: function() {
		console.log('App Hide')
	},
	methods: {
		initTheme() {
			this.themeId = getThemeId()
			this.applyTheme()
			
			// 监听主题变化事件
			uni.$on('themeChanged', ({ themeId }) => {
				this.themeId = themeId
				this.applyTheme()
			})
		},
		applyTheme() {
			const themeId = this.themeId || getThemeId()
			const cssVars = getThemeCSS(themeId)
			
			// 使用 uni.setPageStyle 设置页面样式
			try {
				// 尝试使用页面实例方法
				const pages = uni.getCurrentPages()
				pages.forEach(page => {
					if (page.setPageStyle) {
						page.setPageStyle(cssVars)
					}
				})
			} catch (e) {
				console.log('setPageStyle not available, using fallback')
			}
			
			// 同时更新 page 根元素的 CSS 变量 (通过重新设置样式)
			// 注意: 小程序中这可能不会立即生效，需要页面自身处理
		},
		checkLogin() {
			const token = uni.getStorageSync('token')
			
			try {
				const pages = uni.getCurrentPages()
				if (!pages || pages.length === 0) return
				
				const currentRoute = pages[0].route
				const isLoginPage = currentRoute === 'pages/login/login'

				if (!token && !isLoginPage) {
					uni.reLaunch({
						url: '/pages/login/login'
					})
				}
			} catch (e) {
				console.log('checkLogin skipped:', e)
			}
		}
	}
}
</script>

<style>
@import '@/static/styles/index.scss';
</style>
