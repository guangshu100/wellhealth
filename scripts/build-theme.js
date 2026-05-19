/**
 * 主题构建脚本
 * 
 * 使用方法:
 *   node scripts/build-theme.js           // 构建当前主题
 *   node scripts/build-theme.js sagegreen // 构建指定主题
 *   node scripts/build-theme.js --all     // 构建所有主题
 */

const fs = require('fs');
const path = require('path');

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
};

const rootDir = path.resolve(__dirname, '..');

function generateSCSS(theme) {
  const { colors } = theme;
  return `/**
 * 主题: ${theme.name}
 * 生成时间: ${new Date().toISOString()}
 * 
 * 使用方式: 
 * - Web: @import '@/assets/styles/theme.scss';
 * - 将此文件内容复制到 main.scss 中
 */

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
  --gradient-header: linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight});
  --gradient-button: linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight});
  
  /* 阴影 */
  --shadow-card: 0 2px 12px rgba(60, 55, 45, 0.08);
  --shadow-button: 0 2px 8px ${colors.primary}4D;
  
  /* Element Plus 主题 */
  --el-color-primary: ${colors.primary};
  --el-color-primary-light-3: ${colors.primaryLight};
  --el-color-primary-light-5: ${colors.primaryLight};
  --el-color-primary-light-7: ${colors.primaryLight};
  --el-color-primary-dark-2: ${colors.primaryDark};
  --el-color-success: ${colors.success};
  --el-color-warning: ${colors.warning};
  --el-color-danger: ${colors.danger};
  --el-color-error: ${colors.error};
  --el-color-info: ${colors.info};
  --el-bg-color: ${colors.bgPage};
  --el-bg-color-overlay: ${colors.bgCard};
  --el-text-color-regular: ${colors.textPrimary};
  --el-text-color-secondary: ${colors.textSecondary};
  --el-text-color-placeholder: ${colors.textPlaceholder};
  --el-border-color: ${colors.border};
  --el-border-color-light: ${colors.borderLight};
}
`;
}

function generateUniAppSCSS(theme) {
  const { colors } = theme;
  return `/**
 * 主题: ${theme.name}
 * 生成时间: ${new Date().toISOString()}
 * 
 * 使用方式: 复制到 miniapp/uni.scss
 */

/* 主色 */
$uni-color-primary: ${colors.primary};
$uni-color-success: ${colors.success};

/* 文字颜色 */
$uni-text-color: ${colors.textPrimary};
$uni-text-color-grey: ${colors.textSecondary};
$uni-text-color-placeholder: ${colors.textPlaceholder};

/* 背景颜色 */
$uni-bg-color: ${colors.bgCard};
$uni-bg-color-grey: ${colors.bgPage};
$uni-bg-color-hover: ${colors.bgHover};

/* 边框颜色 */
$uni-border-color: ${colors.border};
`;
}

function buildTheme(themeId) {
  const theme = themes[themeId];
  if (!theme) {
    console.error(`主题 ${themeId} 不存在`);
    return;
  }
  
  console.log(`🏗️ 构建主题: ${theme.name}`);
  
  // 生成 Web 主题 SCSS
  const webScss = generateSCSS(theme);
  const webPath = path.join(rootDir, 'frontend/src/assets/styles/theme.scss');
  fs.writeFileSync(webPath, webScss);
  console.log(`✅ Web 主题已生成: ${webPath}`);
  
  // 生成 Miniapp 主题 SCSS
  const miniappScss = generateUniAppSCSS(theme);
  const miniappPath = path.join(rootDir, 'miniapp/uni-theme.scss');
  fs.writeFileSync(miniappPath, miniappScss);
  console.log(`✅ Miniapp 主题已生成: ${miniappPath}`);
  
  // 生成颜色配置文件
  const colorsJs = `/**
 * 主题: ${theme.name}
 * 生成时间: ${new Date().toISOString()}
 */
export const colors = ${JSON.stringify(theme.colors, null, 2)};
export default colors;
`;
  const colorsPath = path.join(rootDir, 'config/theme-colors.js');
  fs.writeFileSync(colorsPath, colorsJs);
  console.log(`✅ 颜色配置已生成: ${colorsPath}`);
  
  console.log(`\n🎉 主题 ${theme.name} 构建完成!\n`);
}

// 主程序
const args = process.argv.slice(2);
const themeId = args[0] || 'sagegreen';

if (themeId === '--all') {
  console.log('🏗️ 构建所有主题...\n');
  Object.keys(themes).forEach(buildTheme);
} else {
  buildTheme(themeId);
}
