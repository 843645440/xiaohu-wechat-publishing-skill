# 代码块渲染 bug 记录（2026-05）

## 症状

公众号代码块开头出现脏内容，例如：

- `class="language-text">`
- `class="language-python">def ...`
- `class="language-yaml">为什么二手书能成立: ...`

用户明确指出这是错误渲染，而不是内容本身问题。

## 根因

Markdown `fenced_code` 会先生成：

```html
<pre><code class="language-python">...</code></pre>
```

如果后续排版逻辑先：
1. 对整段 `pre_content` 做空格保护
2. 把换行替换成 `<br>`
3. 直接把整段当代码正文处理

那么 `<code class="language-xxx">` 这层外壳就会被当成正文的一部分输出，最终泄漏到公众号正文中。

## 正确处理顺序

必须改成：

1. 先匹配并剥离 `<code ...>...</code>` 外壳
2. 单独提取 `class="language-xxx"` 等 attributes
3. 只对真正的代码内容做：
   - 空格保护
   - `\n -> <br>`
   - 语法高亮
4. 再包回干净的 `<code style="...">代码内容</code>`

## 经验结论

- 处理 fenced code 时，**永远不要直接拿整个 `pre_content` 做文本替换**
- 先拆标签，再处理内容
- 如果看到公众号正文里出现 `class="language-...">`，优先检查代码块预处理顺序
