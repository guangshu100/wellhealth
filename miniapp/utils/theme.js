/**
 * 小程序主题配置
 * 支持运行时主题切换
 */

const themes = {
  sagegreen: {
    name: '鼠尾草绿',
    colors: {
      primary: '#5E8B5A',
      primaryLight: '#7CA878',
      primaryDark: '#4C7048',
      bgPage: '#FCF8F0',
      bgCard: '#FFFFFF',
      bgCardLight: '#FCF8F0',
      bgHover: '#E8F0E6',
      secondary: '#DDCFB0',
      secondaryLight: '#E8DFD0',
      accent: '#E7B83E',
      accentLight: '#F0CE70',
      success: '#5E8B5A',
      warning: '#E7B83E',
      danger: '#CD8B5B',
      error: '#CD8B5B',
      info: '#DDCFB0',
      textPrimary: '#2F2E2A',
      textSecondary: '#7F7D74',
      textPlaceholder: '#A5A49C',
      textInverse: '#FFFFFF',
      border: '#DDCFB0',
      borderLight: '#E8DFD0',
    },
  },
  mistblue: {
    name: '柔雾蓝',
    colors: {
      primary: '#7BA7B9',
      primaryLight: '#9BC0CF',
      primaryDark: '#5E8B9A',
      bgPage: '#F5F9FB',
      bgCard: '#FFFFFF',
      bgCardLight: '#F5F9FB',
      bgHover: '#E8F0F5',
      secondary: '#B8CDD8',
      secondaryLight: '#D4E4EC',
      accent: '#E7B83E',
      accentLight: '#F0CE70',
      success: '#7BA7B9',
      warning: '#E7B83E',
      danger: '#CD8B5B',
      error: '#CD8B5B',
      info: '#B8CDD8',
      textPrimary: '#2C3E50',
      textSecondary: '#6B7C8A',
      textPlaceholder: '#A5ACB2',
      textInverse: '#FFFFFF',
      border: '#B8CDD8',
      borderLight: '#D4E4EC',
    },
  },
  cypress: {
    name: '浅杉绿',
    colors: {
      primary: '#5A9E87',
      primaryLight: '#7BB9A2',
      primaryDark: '#3D7D68',
      bgPage: '#F5FAF8',
      bgCard: '#FFFFFF',
      bgCardLight: '#F5FAF8',
      bgHover: '#E8F5F0',
      secondary: '#A8D4C4',
      secondaryLight: '#C8E4D8',
      accent: '#E7B83E',
      accentLight: '#F0CE70',
      success: '#5A9E87',
      warning: '#E7B83E',
      danger: '#CD8B5B',
      error: '#CD8B5B',
      info: '#A8D4C4',
      textPrimary: '#2C3E38',
      textSecondary: '#6B8078',
      textPlaceholder: '#A5B0AA',
      textInverse: '#FFFFFF',
      border: '#A8D4C4',
      borderLight: '#C8E4D8',
    },
  },
};

const defaultTheme = 'sagegreen';

/**
 * 获取当前主题ID
 */
export function getThemeId() {
  try {
    return uni.getStorageSync('app-theme') || defaultTheme;
  } catch (e) {
    return defaultTheme;
  }
}

/**
 * 获取主题配置
 */
export function getTheme(themeId) {
  return themes[themeId] || themes[defaultTheme];
}

/**
 * 获取主题 CSS 变量样式字符串
 */
export function getThemeCSS(themeId) {
  const theme = getTheme(themeId);
  const c = theme.colors;
  
  return `
    --color-primary: ${c.primary};
    --color-primary-light: ${c.primaryLight};
    --color-primary-dark: ${c.primaryDark};
    --color-bg-page: ${c.bgPage};
    --color-bg-card: ${c.bgCard};
    --color-bg-card-light: ${c.bgCardLight};
    --color-bg-hover: ${c.bgHover};
    --color-secondary: ${c.secondary};
    --color-secondary-light: ${c.secondaryLight};
    --color-accent: ${c.accent};
    --color-accent-light: ${c.accentLight};
    --color-success: ${c.success};
    --color-warning: ${c.warning};
    --color-danger: ${c.danger};
    --color-error: ${c.error};
    --color-info: ${c.info};
    --color-text-primary: ${c.textPrimary};
    --color-text-secondary: ${c.textSecondary};
    --color-text-placeholder: ${c.textPlaceholder};
    --color-text-inverse: ${c.textInverse};
    --color-border: ${c.border};
    --color-border-light: ${c.borderLight};
  `;
}

/**
 * 应用主题 - 尝试使用页面样式设置
 */
export function applyTheme(themeId) {
  const theme = getTheme(themeId);
  const cssVars = getThemeCSS(themeId);
  
  // 保存主题ID
  try {
    uni.setStorageSync('app-theme', themeId);
  } catch (e) {
    console.error('Failed to save theme:', e);
  }
  
  // #ifdef MP-WEIXIN
  // 小程序端：尝试使用 setPageStyle
  try {
    const pages = uni.getCurrentPages();
    let applied = false;
    
    pages.forEach(page => {
      if (page.setPageStyle && typeof page.setPageStyle === 'function') {
        page.setPageStyle(cssVars);
        applied = true;
      }
    });
    
    if (!applied) {
      console.log('setPageStyle not available, using fallback');
      // 降级方案：通过事件通知
      uni.$emit('themeChanged', { themeId, theme: theme.colors });
    }
  } catch (e) {
    console.log('applyTheme failed:', e);
    // 降级方案：通过事件通知
    uni.$emit('themeChanged', { themeId, theme: theme.colors });
  }
  // #endif
  
  // #ifdef H5
  // Web 端通过 CSS 变量设置主题
  try {
    const root = document.documentElement;
    if (root && cssVars) {
      cssVars.split('\n').forEach(line => {
        const match = line.match(/--([^:]+):\s*([^;]+);/);
        if (match) {
          root.style.setProperty(`--${match[1]}`, match[2].trim());
        }
      });
    }
  } catch (e) {
    console.log('H5 theme apply failed:', e);
  }
  // #endif
}

/**
 * 页面 Mixin - 在页面 onShow 中调用以应用主题
 * 使用方式: import { useTheme } from '@/utils/theme.js'
 *           const { applyThemeOnShow } = useTheme()
 *           onShow(() => { applyThemeOnShow() })
 */
export function useTheme() {
  const applyThemeOnShow = () => {
    const themeId = getThemeId();
    const cssVars = getThemeCSS(themeId);
    
    // #ifdef MP-WEIXIN
    // 小程序端：尝试使用 setPageStyle
    try {
      const pages = uni.getCurrentPages();
      const currentPage = pages[pages.length - 1];
      if (currentPage && currentPage.setPageStyle) {
        currentPage.setPageStyle(cssVars);
      } else {
        console.log('setPageStyle not available, using fallback');
        // 降级方案：通过事件通知
        uni.$emit('themeChanged', { themeId });
      }
    } catch (e) {
      console.warn('applyThemeOnShow failed:', e);
      // 降级方案：通过事件通知
      uni.$emit('themeChanged', { themeId });
    }
    // #endif
    
    // #ifdef H5
    // Web 端通过 CSS 变量设置主题
    try {
      const root = document.documentElement;
      if (root && cssVars) {
        cssVars.split('\n').forEach(line => {
          const match = line.match(/--([^:]+):\s*([^;]+);/);
          if (match) {
            root.style.setProperty(`--${match[1]}`, match[2].trim());
          }
        });
      }
    } catch (e) {
      console.warn('H5 applyThemeOnShow failed:', e);
    }
    // #endif
  };
  
  return {
    themeId: getThemeId(),
    theme: getTheme(getThemeId()),
    applyThemeOnShow
  };
}

export default {
  themes,
  defaultTheme,
  getThemeId,
  getTheme,
  getThemeCSS,
  applyTheme,
  useTheme,
};