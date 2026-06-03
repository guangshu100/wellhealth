/**
 * 简单的Markdown转HTML转换器
 * 支持: 标题、粗体、斜体、代码块、行内代码、链接、列表
 */

export function parseMarkdown(text: string): string {
  if (!text) return ''

  let html = text
    // 转义HTML特殊字符
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 代码块 ```code```
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre class="code-block"><code>${code.trim()}</code></pre>`
  })

  // 行内代码 `code`
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')

  // 标题 ### H3, ## H2, # H1
  html = html.replace(/^#{1,6}\s+(.+)$/gm, '<h3 class="md-h3">$1</h3>')

  // 加粗 **text** 或 __text__
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>')

  // 斜体 *text* 或 _text_
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/_([^_]+)_/g, '<em>$1</em>')

  // 删除线 ~~text~~
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>')

  // 无序列表 - item 或 * item
  html = html.replace(/^[-*]\s+(.+)$/gm, '<li class="md-li">$1</li>')

  // 有序列表 1. item
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li class="md-li">$1</li>')

  // 链接 [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="md-link">$1</a>')

  // 换行处理
  html = html.replace(/\n/g, '<br>')

  return html
}
