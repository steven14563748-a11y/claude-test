# PROGRESS — NHLI70037 ICA resit 2026（SCN1A / Bob）

## 已完成
- [2026-11-04] 阶段 0 读题：要点拆解、格式要求、字数分配建议、事实清单 → `00_读题与事实清单.md`
- [2026-11-04] 发现并证明变异命名不一致（c.3993C>T 与 p.Asp1331Glu 互相矛盾；MANE 参考碱基为 A、第 1331 位为 Glu）
- [2026-11-04] 读完 ClinGen 钠通道 VCEP《SCN1A 细则》v2.0（GN067）；点击页面下载按钮保存了 PM1 表、旁系同源对照表、PVS1 外显子表（xlsx）→ `02_数据库查询/ClinGen_VCEP附件/`
- [2026-11-05] 阶段 2 数据库查询完成：29 张编号截图（D01–D29）→ `02_数据库查询/screenshots/`；《数据库查询：过程与截图》PDF/HTML；截图 zip + `截图索引.csv`
- [2026-11-05] 阶段 3 初稿：ACMG 逐条判定（VCEP v2.0）→ **PM1_Moderate + PM2_Supporting = VUS**；改变分类所需证据；四个假说；Q2/Q3 证据框架；48 篇候选文献书目经 PubMed API 核实存在 → `03_推导与证据清单.md`

## 待做
- [ ] 等你决定变异命名怎么处理（见"已发现问题 1"）
- [ ] 阶段 1：指定文献精读 —— 题目文件里没有阅读清单【缺】，等你提供（或确认没有）
- [ ] 在你的 Chrome 里补截（本会话做不了，NCBI/PMC/PubMed 有验证码）：NCBI RefSeq NM_001165963.4 页面；Pejaver 2022 表 2；（可选）ClinVar 网页、UCSC 保守性
- [ ] 文献支持句取证（阶段 5 的方法，可以在写作前先做关键几篇：Li 2021、Richards 2015、Tavtigian 2020、Guerrini 1998、Scheffer 1997）
- [ ] 阶段 4–7：写作答疑、引用核对、PubMed 对比、终稿检查（等你的草稿）

## 已发现问题
1. **变异命名不一致**（证明见 `00_读题与事实清单.md` 开头和 PDF 的 A 部分）。需要你决定：问课程负责人，和/或在报告里说明后按 p.(Glu1331Asp)（"第 1331 位保守错义"）评估。
2. **引用格式、计字规则未知**【缺】：题目文件没写，需要查课程手册。
3. **本会话不能用你的 Chrome**：云端容器里没有 Claude in Chrome，也没连上你的电脑。公开数据库用容器内 Chromium 截图；NCBI 网页、PubMed、PMC、Europe PMC、Cell 对该浏览器都有机器人验证（未点、未绕过）。
4. VCEP 附件「Combining Rules」（积分合并规则，最终分类要用）和「PS1_Variants impacting splicing」是 PDF，按"PDF 只在你要求时下载"的规则**没有下载**。是否下载由你决定。
5. Ensembl VEP REST 查询时返回 503/500；在线预测分数改用 dbNSFP（MyVariant.info）和 SpliceAI-lookup，两者一致。
6. VariantValidator 网页版对匿名用户有提交次数限制，只截了 C>T 和 A>T 两张；A>C 用 REST 接口核对过（未截图）。
7. 截图过程中工作进程重启过一次（截图任务被中断）；已检查并重拍中断的截图，最终 29 张都看过高亮位置。
