/**
 * 康伴健康 - 统一主题配置
 * 支持一键换肤的主题配置方案
 * 
 * 使用方式:
 * - Web: 导入 CSS 变量或在 JS 中引入获取颜色值
 * - Miniapp: 编译 uni.scss 时自动应用变量
 * - 换肤: 动态修改 CSS 变量或切换主题配置
 */

const themes = {
  // V3: 鼠尾草绿主题 (当前使用)
  sagegreen: {
    name: '鼠尾草绿',
    nameEn: 'Sage Green',
    id: 'sagegreen',
    colors: {
      // 主色系
      primary: '#5E8B5A',
      primaryLight: '#7CA878',
      primaryDark: '#4C7048',
      
      // 背景色系
      bgPage: '#FCF8F0',
      bgCard: '#FFFFFF',
      bgCardLight: '#FCF8F0',
      bgHover: '#E8F0E6',
      
      // 辅助色系
      secondary: '#DDCFB0',
      secondaryLight: '#E8DFD0',
      accent: '#E7B83E',
      accentLight: '#F0CE70',
      
      // 功能色系
      success: '#5E8B5A',
      warning: '#E7B83E',
      danger: '#CD8B5B',
      error: '#CD8B5B',
      info: '#DDCFB0',
      
      // 文字色系
      textPrimary: '#2F2E2A',
      textSecondary: '#7F7D74',
      textPlaceholder: '#A5A49C',
      textInverse: '#FFFFFF',
      
      // 边框色系
      border: '#DDCFB0',
      borderLight: '#E8DFD0',
      
      // 渐变配置
      gradient: {
        header: 'linear-gradient(135deg, #5E8B5A, #7CA878)',
        button: 'linear-gradient(135deg, #5E8B5A, #7CA878)',
        primary: 'linear-gradient(135deg, #5E8B5A, #7CA878)',
      },
      
      // 阴影配置
      shadow: {
        card: '0 2px 12px rgba(60, 55, 45, 0.08)',
        button: '0 2px 8px rgba(94, 139, 90, 0.3)',
        popup: '0 4px 20px rgba(60, 55, 45, 0.12)',
      },
    },
    
    // Element Plus 主题 (Web 专用)
    elementPlus: {
      '--el-color-primary': '#5E8B5A',
      '--el-color-primary-light-3': '#7CA878',
      '--el-color-primary-light-5': '#96BC96',
      '--el-color-primary-light-7': '#B0CDB0',
      '--el-color-primary-light-8': '#C8DCC8',
      '--el-color-primary-light-9': '#E0EBE0',
      '--el-color-primary-dark-2': '#4C7048',
      '--el-color-success': '#5E8B5A',
      '--el-color-warning': '#E7B83E',
      '--el-color-danger': '#CD8B5B',
      '--el-color-error': '#CD8B5B',
      '--el-color-info': '#DDCFB0',
      '--el-bg-color': '#FCF8F0',
      '--el-bg-color-overlay': '#FFFFFF',
      '--el-bg-color-page': '#FCF8F0',
      '--el-text-color-regular': '#2F2E2A',
      '--el-text-color-secondary': '#7F7D74',
      '--el-text-color-placeholder': '#A5A49C',
      '--el-text-color-primary': '#5E8B5A',
      '--el-border-color': '#DDCFB0',
      '--el-border-color-light': '#E8DFD0',
      '--el-border-color-lighter': '#F0EBE2',
      '--el-fill-color': '#FCF8F0',
      '--el-fill-color-light': '#FCF8F0',
      '--el-fill-color-lighter': '#FDFBF5',
      '--el-fill-color-blank': '#FFFFFF',
    },
    
    // UniApp 变量 (小程序专用)
    uniApp: {
      '$uni-color-primary': '#5E8B5A',
      '$uni-color-success': '#5E8B5A',
      '$uni-color-warning': '#E7B83E',
      '$uni-color-error': '#CD8B5B',
      '$uni-text-color': '#2F2E2A',
      '$uni-text-color-inverse': '#FFFFFF',
      '$uni-text-color-grey': '#7F7D74',
      '$uni-text-color-placeholder': '#7F7D74',
      '$uni-bg-color': '#FFFFFF',
      '$uni-bg-color-grey': '#FCF8F0',
      '$uni-bg-color-hover': '#E8F0E6',
    },
  },
  
  // V2: 柔雾蓝主题 (备选)
  mistblue: {
    name: '柔雾蓝',
    nameEn: 'Mist Blue',
    id: 'mistblue',
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
      gradient: {
        header: 'linear-gradient(135deg, #7BA7B9, #9BC0CF)',
        button: 'linear-gradient(135deg, #7BA7B9, #9BC0CF)',
        primary: 'linear-gradient(135deg, #7BA7B9, #9BC0CF)',
      },
      shadow: {
        card: '0 2px 12px rgba(50, 70, 85, 0.08)',
        button: '0 2px 8px rgba(123, 167, 185, 0.3)',
        popup: '0 4px 20px rgba(50, 70, 85, 0.12)',
      },
    },
    elementPlus: {},
    uniApp: {},
  },
  
  // V1: 浅杉绿主题 (备选)
  cypress: {
    name: '浅杉绿',
    nameEn: 'Cypress',
    id: 'cypress',
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
      gradient: {
        header: 'linear-gradient(135deg, #5A9E87, #7BB9A2)',
        button: 'linear-gradient(135deg, #5A9E87, #7BB9A2)',
        primary: 'linear-gradient(135deg, #5A9E87, #7BB9A2)',
      },
      shadow: {
        card: '0 2px 12px rgba(50, 70, 60, 0.08)',
        button: '0 2px 8px rgba(90, 158, 135, 0.3)',
        popup: '0 4px 20px rgba(50, 70, 60, 0.12)',
      },
    },
    elementPlus: {},
    uniApp: {},
  },
};

// 默认主题
const defaultTheme = themes.sagegreen;

/**
 * 获取主题 CSS 变量字符串
 * @param {string} themeId 主题ID
 * @returns {string} CSS 变量字符串
 */
function getThemeCSSVariables(themeId = 'sagegreen') {
  const theme = themes[themeId] || defaultTheme;
  const { colors } = theme;
  
  return `
    /* 主题: ${theme.name} */
    :root {
      /* 主色 */
      --color-primary: ${colors.primary};
      --color-primary-light: ${colors.primaryLight};
      --color-primary-dark: ${colors.primaryDark};
      
      /* 背景色 */
      --color-bg-page: ${colors.bgPage};
      --color-bg-card: ${colors.bgCard};
      --color-bg-card-light: ${colors.bgCardLight};
      --color-bg-hover: ${colors.bgHover};
      
      /* 辅助色 */
      --color-secondary: ${colors.secondary};
      --color-secondary-light: ${colors.secondaryLight};
      --color-accent: ${colors.accent};
      --color-accent-light: ${colors.accentLight};
      
      /* 功能色 */
      --color-success: ${colors.success};
      --color-warning: ${colors.warning};
      --color-danger: ${colors.danger};
      --color-error: ${colors.error};
      --color-info: ${colors.info};
      
      /* 文字色 */
      --color-text-primary: ${colors.textPrimary};
      --color-text-secondary: ${colors.textSecondary};
      --color-text-placeholder: ${colors.textPlaceholder};
      --color-text-inverse: ${colors.textInverse};
      
      /* 边框色 */
      --color-border: ${colors.border};
      --color-border-light: ${colors.borderLight};
      
      /* 渐变 */
      --gradient-header: ${colors.gradient.header};
      --gradient-button: ${colors.gradient.button};
      --gradient-primary: ${colors.gradient.primary};
      
      /* 阴影 */
      --shadow-card: ${colors.shadow.card};
      --shadow-button: ${colors.shadow.button};
      --shadow-popup: ${colors.shadow.popup};
    }
  `;
}

/**
 * 获取 Element Plus 主题变量
 * @param {string} themeId 主题ID
 * @returns {object} Element Plus 变量对象
 */
function getElementPlusVariables(themeId = 'sagegreen') {
  const theme = themes[themeId] || defaultTheme;
  return theme.elementPlus;
}

/**
 * 获取 UniApp 主题变量
 * @param {string} themeId 主题ID
 * @returns {object} UniApp 变量对象
 */
function getUniAppVariables(themeId = 'sagegreen') {
  const theme = themes[themeId] || defaultTheme;
  return theme.uniApp;
}

/**
 * 动态应用主题 (Web端)
 * @param {string} themeId 主题ID
 */
function applyTheme(themeId = 'sagegreen') {
  if (typeof document === 'undefined') return;
  
  const theme = themes[themeId] || defaultTheme;
  const { colors } = theme;
  
  // 应用 CSS 变量
  const root = document.documentElement;
  root.style.setProperty('--color-primary', colors.primary);
  root.style.setProperty('--color-primary-light', colors.primaryLight);
  root.style.setProperty('--color-primary-dark', colors.primaryDark);
  root.style.setProperty('--color-bg-page', colors.bgPage);
  root.style.setProperty('--color-bg-card', colors.bgCard);
  root.style.setProperty('--color-bg-card-light', colors.bgCardLight);
  root.style.setProperty('--color-bg-hover', colors.bgHover);
  root.style.setProperty('--color-secondary', colors.secondary);
  root.style.setProperty('--color-secondary-light', colors.secondaryLight);
  root.style.setProperty('--color-accent', colors.accent);
  root.style.setProperty('--color-accent-light', colors.accentLight);
  root.style.setProperty('--color-success', colors.success);
  root.style.setProperty('--color-warning', colors.warning);
  root.style.setProperty('--color-danger', colors.danger);
  root.style.setProperty('--color-error', colors.error);
  root.style.setProperty('--color-info', colors.info);
  root.style.setProperty('--color-text-primary', colors.textPrimary);
  root.style.setProperty('--color-text-secondary', colors.textSecondary);
  root.style.setProperty('--color-text-placeholder', colors.textPlaceholder);
  root.style.setProperty('--color-text-inverse', colors.textInverse);
  root.style.setProperty('--color-border', colors.border);
  root.style.setProperty('--color-border-light', colors.borderLight);
  root.style.setProperty('--gradient-header', colors.gradient.header);
  root.style.setProperty('--gradient-button', colors.gradient.button);
  root.style.setProperty('--gradient-primary', colors.gradient.primary);
  root.style.setProperty('--shadow-card', colors.shadow.card);
  root.style.setProperty('--shadow-button', colors.shadow.button);
  root.style.setProperty('--shadow-popup', colors.shadow.popup);
  
  // 应用 Element Plus 变量
  Object.entries(theme.elementPlus).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
  
  // 保存主题到本地存储
  localStorage.setItem('app-theme', themeId);
}

/**
 * 获取当前主题ID
 * @returns {string} 主题ID
 */
function getCurrentTheme() {
  if (typeof localStorage !== 'undefined') {
    return localStorage.getItem('app-theme') || 'sagegreen';
  }
  return 'sagegreen';
}

module.exports = {
  themes,
  defaultTheme,
  getThemeCSSVariables,
  getElementPlusVariables,
  getUniAppVariables,
  applyTheme,
  getCurrentTheme,
  default: themes,
};
