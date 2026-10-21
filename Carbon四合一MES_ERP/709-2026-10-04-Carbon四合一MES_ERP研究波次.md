# Carbon 四合一 MES/ERP 研究波次（2026-10-04）

- **性质**：独立研究波次（非 aos-platform 代码改动），为栖月汇垂直电商/后续制造场景储备参考系统。来源：头条文章 → GitHub `crbnos/carbon`（ERP/MRP/MES/QMS 四合一，单 Postgres schema，AGPL-3.0 + 商业许可，~2.7k star）。
- **交付物**：`/Users/ddt/work/projects/ai_agent/mes_erp/carbon/`（源码克隆 commit `9e8170c` + `详细使用说明.md`，含三方文档坑对照与三层接入坑勘误）。
- **运行时实测（全通过）**：
  - `pnpm install` 跑通（WorkBuddy shim `NODE_OPTIONS` 注入需 `env -i` 绕过；supabase CLI postinstall 被 pnpm10 静默拦截需手动补二进制）。
  - 冒烟：官方 `check:manifest` 通过（1483 operations / 15 modules）。
  - 全栈：`crbn up --no-portless --all` 拉起 13 容器 + 1092 迁移 + ERP(:3000)/MES(:3001)；satellite 数据集灌入成功（21 工单/37 物料/8 报价/8 工作中心 + MRP 重算 + 排程）。
  - 浏览器验收（agent-browser 截图在 mes_erp/carbon/*.png）：生产看板（13 启用工单+工作中心利用率）、库存（37 物料+补货策略）、质量 QMS（问题趋势/检验/校准）、MES 排程板（4 工作中心甘特+3D 渲染工单卡）——**四系统真实渲染确认**。
  - AI：主聊天 agent 经 `OPENAI_BASE_URL` 打 Agnes（agnes-2.0-flash）中文回复成功。**三层坑**：①`AI_BASE_URL` 只管文档抽取，主 agent 读 `OPENAI_BASE_URL`；②模型名写死在 `packages/utils/src/llm.ts`；③**AI_AGENT 被 `packages/ee` Edition 门控，社区版隐藏，`CARBON_EDITION="test"` 自托管放行**。
- **对 AOS 的可借鉴点**：a) 单 schema 多域（ERP/MES/QMS 同库）+ 1092 迁移的演进纪律；b) `crbn` worktree-per-stack 开发 CLI（与我们 5 分支并行打法的同构思路）；c) Edition 门控把商业功能锁在 `packages/ee` 内部的许可边界设计；d) MCP 15 模块/1483 operations 的 API 面生成管线。
- **证据**：`mes_erp/carbon/详细使用说明.md`（441+ 行）、8 张验收截图、`/tmp/carbon_seed.log`（SEED_EXIT=0）。Docker 镜像源配置变更见工作日志（daemon.json.bak-20261004）。
- **边界**：未动 aos-platform 任何分支；Carbon 栈仍在后台运行（`crbn down` 可停）；`CARBON_EDITION="test"` 仅限本机研究，不可商用部署。

## 建议下波次开发清单（供大同决策）

| # | 事项 | 价值 | 量级 |
|---|---|---|---|
| 1 | **Carbon 借鉴点提炼入 AOS 设计库**：把上面 4 个可借鉴点写成 ADR 草案（尤其 ee 许可边界 + worktree-per-stack），供栖月汇后续演进引用 | 高（架构参考沉淀） | 小 |
| 2 | **Carbon MCP 实测**：起 Carbon 的 MCP server（`/api/mcp`，需 edition=test 已满足），用本地 agent 真连一次，验证 1483 operations 的调用体验 | 中（AI+ERP 交互范式参考） | ✅ 已完成（2026-10-04 晚）：meta-MCP 仅暴露 call_tool/describe_tool/search_tools 三工具；scopes 格式为 `{module_action:[companyId]}`；`call_tool production_getJobsList` 返回 21 条真实工单 |
| 3 | **Carbon 数据模型精读**：重点读 `job/inventory/qualityDocument` 三域 schema + 迁移组织方式，输出《Carbon 数据库设计笔记》供栖月汇订单域对比 | 中 | ✅ 已完成（2026-10-04 晚）：直连运行库提取 368 表/1092 迁移真 schema，交付《Carbon数据库设计笔记.md》（三域列+外键+互联 ER+迁移纪律+栖月汇借鉴点）；并续出《Carbon各业务域数据库表设计ER总览.md》——按 14 个业务域逐表列出 名称/用途/业务链路位置/关联表，含四合一跨域主链路 ER（job 为物理枢纽）+ NCR 放射状贯穿全链路 |
| 4 | **回归 AOS 主线**：mes_erp 研究收口，按 708 号文档接续 aos-platform 当前波次（ISSuer 接续） | 高（主线推进） | 按主线 |
| 5 | Carbon 栈资源回收：研究暂停期 `crbn down` 释放 13 容器内存（数据卷保留，可随时 `crbn up` 恢复） | 低（本机资源） | 小 |
