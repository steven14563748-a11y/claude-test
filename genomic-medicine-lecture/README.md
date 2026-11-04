# 变异效应预测讲义精读

讲义 *Accurate genome-wide variant effect prediction*（Imperial College London 2026，Jun Cheng，Google DeepMind）的逐页双语学习页面，共 37 页。

每页包括：

- 幻灯片原图（点击放大）
- 原文与译文逐行对照，原文中的重点词后面附中文释义
- “图中文字”：图片和截图里的主要标签、坐标轴等文字的整理
- “讲解”：难懂概念、图的读法和背景知识

页面顶部的按钮可以隐藏释义、译文、讲解或原图；隐藏译文后，点击模糊的译文可以逐行显示，用来自测。文末有自动汇总的词汇表，可以搜索。

## 文件

| 路径 | 说明 |
| --- | --- |
| `index.html` | 生成好的页面，用浏览器直接打开即可 |
| `slides/` | 从 PDF 渲染出的 37 张幻灯片图片 |
| `src/content.txt` | 内容源文件（原文、译文、释义、讲解） |
| `src/build.py` | 把 `content.txt` 生成为 `index.html` 的脚本 |

修改内容后重新生成：

```bash
python3 src/build.py
```
