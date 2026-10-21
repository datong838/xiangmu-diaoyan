# 专业群 AI 工作站功能清单与字段设计

> 版本：v1.3 产品方案对象与办理链同步稿　更新日期：2026-10-18　状态：待校方与服务方确认，尚未形成开发或验收承诺。
> 配套文件：[专业群AI工作站需求确认单](专业群AI工作站需求确认单.md)。两份文件按同一版本共同确认；如填写结果与本稿不同，先同步修订再冻结。

本版同步 `产品方案/13—24` 的对象、状态、智能体任务、知识吸收、跨页面流程和字段差异设计。新增逻辑对象用于说明产品如何承载业务，不表示已经建表或实现；具体物理模型仍须经过技术方案和迁移评审。

本工作站围绕“建设任务书—指标与年度目标—日常工作与成果—支撑证据—进度反馈—报告审核”形成闭环。教师和管理人员在工作站内完成核心操作；第三方平台与模型作为可选后端能力。统一身份认证跳转、经选配的消息提醒可作为辅助入口，不要求用户切换到第三方产品才能完成主流程，也不向普通用户暴露密钥或存储路径。

## 一、审核依据与总体方案

### 1.1 资料依据与证据边界

| 资料 | 本稿采用的内容 | 使用限制 |
| --- | --- | --- |
| `09-16 校企共建AI工作站及专业群建设.docx` | 00:21:45–00:24:38 任务书、日常材料与进度表；00:34:37–00:37:29 归档、反馈改稿与教师进度；01:00:41 专业群建设与排课两项工作 | 原始转写存在错字；提出诉求不等于需求已签署或功能已实现 |
| `会议原始资料.md` | 先试点后推广、私域可控、旧系统持续运行、人工决定、评课暂不开放 | 摘要时间轴与 Word 转写不同，引用时注明文件，不能混用时间戳 |
| `方案梳理.md` | 指标、素材、报告及溯源主链路 | 飞书前端路线仅为早期建议，本稿沿用两份目标文档的独立工作站定位 |
| `钉钉飞书的选型.md`、`飞书豆包api_cli_群建设探索.md` | 可插拔集成、身份区分、模型路由等候选思路 | 品牌、接口数量、版本、许可与能力未在本次独立联网核验，不作为采购或实现承诺 |
| `会议纪要图.jpg` | 辅助目录概览 | 不用缩略图中无法辨认的文字作为独立结论依据 |

会议中的“71 个专业”“百余名教师”是扩展背景，不能写成 71 个专业群或本期并发人数；“训练技能”在本项目中先解释为规则、模板与知识配置，不自动授权模型训练、微调或跨校复用原始材料。

### 1.2 审核结论及本次修订

原稿具备模块框架，但尚不能直接作为实施基线。本次保留八大模块及原功能编号，修正以下问题。

| 问题 | 修订结果 |
| --- | --- |
| 两份文档对 OCR、版本、审批、导出的优先级不一致 | 统一 P0 最小闭环与 P1 扩展；基本版本、证据确认、报告审核和导出进入 P0 |
| 对话查进度与按反馈修改初稿未完整体现 | 增补 9.1–9.4，自然语言查询与表格使用同一统计口径 |
| 材料数量、任务进度与指标达成混用 | 分开记录工作状态、实际完成量、证据覆盖、风险和审核结论 |
| 专业、建设周期、实际值与历史版本缺字段 | 增加专业关系、建设周期、指标修订、分期目标、进展确认及成果去重 |
| 引用仅指向文件路径或段落序号 | 改为不可变素材版本、片段定位、报告版本与稳定段落标识 |
| “私有部署”被等同于“不出域” | 明确完全内网模式和受控外部服务模式；OCR、向量化也纳入出域控制 |
| 工期、架构与性能数字写成既定结论 | 改为候选方案与待确认验收条件；不提前承诺多平台集成、全校推广 |

### 1.3 范围与分期

- **P0 建议本期**：一个试点专业群、一个建设周期、一套已确认指标、基本任务填报与站内提醒、素材归集与人工确认、进度问答和看板、一份选定报告模板、反馈改稿、单级审核、Word/PDF 导出，以及版本、权限、审计、限额和恢复能力。
- **P1 候选扩展**：任务书 AI 拆解、OCR/音视频转写、更多报告模板、可视化版本对比、多级审批、复杂预警、定时简报、附件打包及经验证的外部采集。选入本期须写明功能编号、费用、依赖和验收用例。
- **P2 后续研究**：原生移动 App、复杂绩效打分、专项数据库接入等，均不计入 P0 验收。
- **排课独立评估**：保留会议提出的排课方向，先核对旧系统及教师、教室、班级、时段冲突样例，出具可行性与限制清单；不在本稿承诺自动排课、调课写回或替换旧系统。
- **本期排除**：摄像头与学生行为分析、心理状态推断、自动评课、加工程序与机器人控制、自动对外申报、跨校训练或复用校方素材。后续需要时另行论证和立项。

### 1.4 总体架构

```text
学校用户 → 工作站网页与对话入口
                 ↓ 身份认证与每次请求授权
      指标/任务/素材/进度/报告/审核服务
          ├─ 关系数据、不可变附件版本、审计与备份
          ├─ 异步作业 → 解析、检索、生成、导出
          └─ 能力适配层 → 已授权的模型或办公平台
                            ↑ 出域策略、预算与调用审计
```

工作站数据是业务事实的主记录；第三方文档、通知与索引是受控映射，不形成两套互相覆盖的主记录。检索索引可重建，不能替代证据原件；AI 不直接修改正式指标值、审批结论或旧业务系统。

## 二、功能清单

### 2.1 专业群管理模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 1.1 | 创建 / 编辑专业群 | 录入名称、编号、级别、包含专业、负责人、成员 | P0 |
| 1.2 | 专业群生命周期 | 申报期 → 建设期 → 验收期，可配置阶段 | P0 |
| 1.3 | 成员管理 | 维护成员与角色（负责人 / 编辑 / 只读） | P0 |
| 1.4 | 专业群切换 | 用户在授权专业群间切换，校级在本校授权范围内跨群总览 | P0 |

### 2.2 指标库管理模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 2.1 | 指标树维护 | 多级指标草稿增删改排序；已生效或被引用指标归档并保留历史 | P0 |
| 2.2 | 从任务书自动解析 | 上传 Word/PDF，AI 提取指标草稿并标明出处，人工确认；手工录入与 Excel 导入为兜底 | P1 |
| 2.3 | 指标详细信息 | 编号、名称、目标值、单位、责任部门、责任人、时间节点、验收标准、权重、关联专业 | P0 |
| 2.4 | 指标版本管理 | P0 保留不可覆盖的指标修订与生效记录；P1 提供可视化差异对比 | P0 |
| 2.5 | 指标状态设置 | 业务状态与风险分离；进展经确认后计入统计，口径见 2.10 | P0 |
| 2.6 | 指标 Excel 批量导入导出 | 从现有 Excel 台账迁移 | P0 |
| 2.7 | 指标拆分到专业 | 群级指标分配到具体专业；联合完成与独立累计分开，避免重复计数 | P0 |
| 2.8 | 指标卡片详情页 | 描述、状态、关联素材、历史动态、预警 | P0 |

### 2.3 素材中心模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 3.1 | 素材上传 | 工作站网页端拖拽、批量上传；手机浏览器上传与拍照选择，不含原生 App | P0 |
| 3.2 | 素材类型支持 | P0 支持 docx/xlsx/pptx/可提取文本 PDF/jpg/png；旧版 Office、音视频、压缩包和网页采集为 P1 扩展 | P0 |
| 3.3 | 自动格式解析 | P0 提取文本型 PDF/Office，图片可登记、预览与人工摘要；OCR、音视频转写为 P1 | P0 |
| 3.4 | 自动分类打标 | 用户先选授权专业群；AI 推荐专业、指标、主题、业务年份；不得自动变更归属与权限 | P0 |
| 3.5 | 素材-指标关联 | 自动推荐关联指标，用户确认/修改，支持一材多用 | P0 |
| 3.6 | 素材标签管理 | 系统标签 + 自定义标签，支持筛选 | P0 |
| 3.7 | 素材检索 | 关键词、标签、上传人、时间、指标维度、专业群、文件类型混合检索 | P0 |
| 3.8 | 素材预览 | P0 预览 PDF/图片及 Office 转换结果；转换失败提供受控下载，不宣称可解析所有格式 | P0 |
| 3.9 | 素材版本 | P0 保留不可覆盖的原件版本和哈希，同名不等于同一材料；P1 增加版本对比 | P0 |
| 3.10 | 素材审核 | P0 支持提交、确认、退回；确认后才可计入正式证据；是否共享仍由授权决定 | P0 |
| 3.11 | 外部来源自动采集 | 仅接经验证且获授权的连接器、指定数据范围；普通微信群自动采集不作默认承诺 | P1 |
| 3.12 | 素材去重查漏 | P0 同范围文件哈希查重及证据缺项；P1 语义相似查重 | P0 |
| 3.13 | 素材删除回收站 | 回收站保留期建议 30 天，待确认；被正式报告引用的版本禁止直接物理删除 | P0 |

### 2.4 任务与预警模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 4.1 | 任务创建 | 基于指标创建任务，指派人员、设置截止时间；AI 仅建议，人员确认后派发 | P0 |
| 4.2 | 任务分派 | 负责人分派基本任务；多层子任务为 P1 | P0 |
| 4.3 | 任务进度上报 | 被指派人提交进展说明、业务发生日期和过程素材，由负责人确认 | P0 |
| 4.4 | 预警规则配置 | P0 提供逾期与缺证据提醒；P1 可配置复杂规则 | P0 |
| 4.5 | 消息触达 | P0 站内消息；邮件、短信及办公平台通知为 P1，独立确认渠道和费用 | P0 |
| 4.6 | 周报月报自动生成 | 定期汇总已确认进展，生成周/月总结及下一周期计划草稿；和 5.11 使用同一调度，不自动发布 | P1 |
| 4.7 | 周期性总结与计划 | 支持周、月、年总结及下周、下月、下一年度计划；是否由系统定时无人触发、是否需要人工发起分别配置 | P0 |
| 4.8 | 业绩分类与指标匹配 | 按学校提供的分类规则整理业绩，匹配建设任务或指标，输出可核对的汇总表；分类结果由人工确认 | P0 |

### 2.5 报告生成模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 5.1 | 报告类型配置 | 支持申报书、建设任务书、实施方案、年度报告/自评、中期评审、终期验收等类型字典；本期落地模板由校方选定 | P0 |
| 5.2 | 模板管理 | 管理校方提供的最终成品模板、填写说明、正式通知和历史合格样例；记录必填章节/字段、表格结构、附件、命名和提交格式 | P0 |
| 5.3 | 报告生成入口 | 选择专业群、建设周期、模板版本、统计期间与数据截止点，预览缺项后生成草稿 | P0 |
| 5.4 | 生成结果结构 | 总体情况、指标完成、主要措施成效、存在问题、下一步计划、佐证清单 | P0 |
| 5.5 | 内容可溯源 | 事实、数字关联素材不可变版本与具体页/段/表格定位；通过工作站鉴权查看，不暴露存储路径 | P0 |
| 5.6 | 人工编辑 | 在线编辑并按反馈局部改稿；保存为草稿，须经审核才能定稿 | P0 |
| 5.7 | 版本管理 | P0 保留初稿、修订稿及定稿快照；P1 可视化差异对比 | P0 |
| 5.8 | 佐证材料清单 | P0 生成指标、证据、版本、定位清单；P1 经逐项权限校验打包附件 | P0 |
| 5.9 | 导出 | P0 导出选定模板的 Word/PDF，保留目录、页码及引用清单；草稿带标识 | P0 |
| 5.10 | 审批流 | P0 指定审核人确认/退回，作者不得自审；P1 支持多级可配置审批 | P0 |
| 5.11 | 定时自动生成 | 如每月 1 日自动生成上月月报草稿，与 4.6 统一配置 | P1 |
| 5.12 | 模板清单维护 | 维护已知模板清单并允许随时新增，区分项目、部门、年度、批次和模板版本；未提供正式模板时标记待补 | P0 |

### 2.6 数据看板模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 6.1 | 全局总览 | 按授权范围显示专业群数、叶子指标达成率、证据覆盖率、未填报数、数据截止时间 | P0 |
| 6.2 | 专业群详情看板 | 指标完成率、维度分布、时间进度、风险预警 | P0 |
| 6.3 | 指标分解看板 | 各级指标完成状态、责任部门、支撑材料数 | P0 |
| 6.4 | 素材增长趋势 | 每月上传量、人工复核采纳率；准确率须在标注样本集评测，不将采纳率当准确率 | P1 |
| 6.5 | 成果墙 | 展示标志性成果（荣誉、校企合作、学生获奖） | P1 |

### 2.7 数据集成模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 7.1 | 飞书集成 | 候选连接器；能力、权限、许可与数据处理边界验证通过后再纳入范围 | P1 |
| 7.2 | 钉钉集成 | 候选连接器；与飞书按校方条件选配，不默认两套同时建设 | P1 |
| 7.3 | 教务/排课评估 | 单独确认只读样例、冲突规则、旧系统操作路径与限制；生产接入另立范围 | 独立评估 |
| 7.4 | 数据库直连 | 非默认路线；确需使用时专项确认厂商授权、只读账号、字段范围与影响 | P2 |
| 7.5 | Webhook/开放 API | 获授权的外部系统推送到待审核区，验签、幂等与重放防护 | P1 |
| 7.6 | Excel 批量导入 | 指标、成员、素材清单批量导入 | P0 |

### 2.8 系统管理模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 8.1 | 用户管理 | 创建、编辑、停用与批量导入；已关联业务记录的用户不直接物理删除 | P0 |
| 8.2 | 角色权限 | 业务角色与运维角色分离；学校、专业群、材料范围授权，见第七章 | P0 |
| 8.3 | 登录安全 | P0 提供本地账号或一套已确认的 SSO；不是同时承诺所有登录方式 | P0 |
| 8.4 | 模型配置 | 在允许出域及预算范围内配置候选模型，至少验证一个合规可用模型；连接密钥不交给教师 | P0 |
| 8.5 | 成本统计 | P0 记录调用、费用估算与预算上限；P1 提供多维分析看板 | P0 |
| 8.6 | 操作日志 | 登录、上传、生成、导出、删除等 | P0 |
| 8.7 | 数据备份 | 备份数据库、附件、配置及密钥恢复依赖，并完成恢复演练 | P0 |
| 8.8 | 字典管理 | 专业群级别、材料类型、指标状态等枚举值 | P0 |

### 2.9 对话与岗位助手

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 9.1 | 自然语言查询进度 | 如“本年度还有哪些未完成指标”，返回表格、统计范围、截止时间及证据入口；缺少群或期间时先澄清 | P0 |
| 9.2 | 查询材料与缺项 | 在当前权限内找材料、解释证据缺项；无依据时显示“未找到已确认资料”，不编造 | P0 |
| 9.3 | 按反馈修改报告 | 用户指定章节和修改要求，产生新草稿版本，保护已人工编辑内容并重新检查引用 | P0 |
| 9.4 | 计划与补材料建议 | 根据已确认指标提出待办建议；展示对象、责任人、截止时间后由授权用户确认执行 | P1 |
| 9.5 | 业务事项登记 | 将新增业务事项登记为可补充任务，维护对象、周期、负责人、输入材料、产物和确认状态，不因尚未开发而丢失 | P0 |
| 9.6 | 教学管理选配助手 | 对教学检查、听评课、出卷要求/审核等材料提供归集、台账和审核记录能力；是否建设专用流程另行确认 | P1 |

### 2.10 业务流程与统计口径

1. **建档**：选定专业群、建设周期、核心/支撑专业及成员；录入或导入指标并确认任务书依据和年度目标。AI 拆解的内容先进入草稿。
2. **日常填报**：教师提交工作记录、发生日期、成果与素材；AI 给出标签和关联建议。负责人确认实际值及证据适用性，退回时必须说明原因。
3. **查进度**：表格、看板与对话共用同一已确认数据源。未填报、待审核、退回、证据缺失均单独显示；实时指查询当前已入库且已确认的记录，同时显示同步/统计时间。
4. **生成报告**：选择模板版本、建设周期、期间和数据截止点，检查缺项，锁定输入快照，生成带引用草稿。支持用户反馈和局部改稿，不覆盖正在编辑的版本。
5. **审核定稿**：作者提交指定版本，审核人通过或退回；通过版本不可覆盖，继续修改须新建版本并重新审核。正式导出只取通过版本，草稿导出带“待审核”标识。
6. **模板与事项扩展**：校方可持续补充业务事项和最终成品模板；新增事项先登记范围与字段，新增模板先登记版本和适用范围，再决定是否进入本期功能。

| 口径 | 定义与边界 |
| --- | --- |
| 实际完成量 | 采用指定期间最后一条已确认累计填报；P0 不把历次累计数相加。增量数据先按业务成果去重后汇总，再提交累计确认 |
| 数值进度 | P0 对“越大越好”且目标值 > 0 的指标计算 `min(max(实际值/目标值,0),1)×100%`；保留实际值与超额量。目标为 0、区间、上限型及复杂比例指标由确认单指定规则，未定规则显示不可计算 |
| 定性指标 | 人工确认里程碑或达成结论；不得按附件个数自动判定完成 |
| 业务状态 | `not_started / in_progress / completed / suspended`；风险标识独立，不将“有风险”当完成状态。已完成须满足已确认标准、必需证据及审核条件 |
| 指标达成率 | 当前周期和期间内已确认达成的适用叶子指标数 / 适用叶子指标总数；父节点不重复计数，未填报仍在分母。不适用须批准并单列数量；分母为 0 显示“不适用” |
| 加权进度 | 仅在叶子指标进度可计算、权重完整且汇总规则确认后展示；有效权重归一化，缺失时不输出误导性总分。跨群默认分别展示，不简单平均百分比 |
| 证据覆盖率 | 已有满足必需证据清单的确认材料的适用叶子指标数 / 适用叶子指标总数；没有定义证据要求时标为“标准待补”，不得默认为已覆盖 |
| 证据完整度 | 某指标已满足的必需证据类型数 / 规定的必需证据类型数；先核对各类型最低数量与有效期，同类型多份材料不增加分母或反复计数 |
| 逾期与数据新鲜度 | 当前时间超过截止时间且未完成为逾期；业务发生日期、提交时间、确认时间、外部同步时间分别保存，旧数据不能标为实时新进展 |
| 一材多用与成果去重 | 一份材料可支持多个指标；同一成果在同一指标、同一统计期间内只计一次。跨专业贡献按已确认分配规则，不按引用次数累计 |
| 历史报告 | 保存当时任务书版本、目标、实际值、证据及模板快照；后续修订不回写旧报告。撤销证据时标记受影响报告，禁止继续作为有效正式版导出 |

### 2.11 建设依据与专业群知识模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 10.1 | 三类依据文件登记 | 分别登记申报书、建设任务书和实施方案的版本、批准状态、生效时间和适用周期 | P0 |
| 10.2 | 原文条款与定位 | 提取目标、指标、任务、节点和证据要求候选，保留页、段、表格或单元格定位，由人确认 | P0 |
| 10.3 | 建设事项对照 | 把三类文件相关条款组织到同一建设事项，候选和确认关系分开 | P0 |
| 10.4 | 口径冲突与决定 | 并排展示冲突来源和影响，由获授权负责人形成正式决定，智能体不得自行选用 | P0 |
| 10.5 | 专业群知识地图 | 查看专业群、专业、依据、指标、任务、人员、材料、证据、成果和报告的双向关系 | P0 |
| 10.6 | 资料吸收批次 | 分别显示已登记、可读取、已拆解、待确认、已发布及失败/冲突/受限数量 | P0 |
| 10.7 | 版本影响复核 | 依据、规则、事实或证据变化后列出受影响对象，由人决定重算、重写、沿用或作废 | P0 |

### 2.12 专业群智能体办理模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 11.1 | 智能体任务单 | 保存用户原话、理解目标、范围、输入版本、预期产出、处理计划、状态和写回对象 | P0 |
| 11.2 | 受控知识任务包 | 按学校、专业群、专业、周期、权限和任务目标组装本次可用知识，不把全校资料无差别载入 | P0 |
| 11.3 | 可见处理计划 | 展示已找到资料、缺少条件、准备执行的步骤、可能修改的对象和人工确认点 | P0 |
| 11.4 | 页面内协助办理 | 将建议带入资料、任务、进度或成果编辑区，用户可修改、拒绝或确认 | P0 |
| 11.5 | 人工确认卡 | 保存接受、修改后接受、拒绝、退回补充和暂不决定，并记录影响范围 | P0 |
| 11.6 | 结果写回 | 把确认结果写入业务对象、版本和建设账本，不让结果只停留在聊天消息中 | P0 |
| 11.7 | 暂停、继续与转交 | 保留任务上下文、未完成步骤和当前版本；恢复时检查权限和输入变化 | P1 |

### 2.13 内容整理、问题差距与建设账本模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 12.1 | 指定用途内容整理 | 按用户给定栏目形成文字、表格结构或汇报内容草稿，固定输入版本和来源 | P0 |
| 12.2 | 内容版本与缺项 | 每轮整理形成新草稿和差异，缺失内容留空并进入待补清单 | P0 |
| 12.3 | 业务问题管理 | 把工作未完成、材料不足、口径待确认等问题作为可跟踪对象，不与提醒事件混用 | P0 |
| 12.4 | 差距原因与补充动作 | 按数量不足、工作推进中、证据缺失、期间不符、规则冲突等形成建议动作 | P0 |
| 12.5 | 补充任务确认 | 建议动作经负责人确认后才成为正式任务，并返回任务流程跟踪 | P0 |
| 12.6 | 建设账本 | 追加记录业务对象的状态、版本、关系、人工决定和影响变化；与技术审计日志关联但职责分开 | P0 |

### 2.14 T15—T18 选配与推广模块

| 编号 | 功能 | 说明 | 优先级 |
| --- | --- | --- | --- |
| 13.1 | 教学检查与听评课归集 | 保留人工评价、问题和整改记录；专用流程是否建设由学校另行确认 | P1/待确认 |
| 13.2 | 出卷任务与人工审核 | 复用任务、版本、退回和审核；试卷正文和保密范围另行确认 | P1/待确认 |
| 13.3 | 产教融合实践资料 | 归集真实项目、参与关系、过程和人工验收结果；首期至少支持资料归集 | P1/待确认 |
| 13.4 | 新专业群初始化 | 复制结构、配置、模板和方法，重新确认新群依据、专业、人员、资料和权限 | P1 |
| 13.5 | 初始化差异预览 | 在创建前展示将复用和必须重新建立的内容，禁止复制试点真实进度和成果 | P1 |

## 三、核心字段设计

本章为逻辑设计，供原型、接口和数据建模核对，不等于已实现数据库。类型按关系数据库通用表达；最终建表、迁移与兼容性在技术方案确认后落实。表格表达业务对象和约束，实施时可在保持隔离、历史与审计能力的前提下合并物理表，不要求一个逻辑对象对应一个独立服务。**P0 表先满足闭环；P1 表只在对应功能选入后实施，不因出现在字典中就视为本期承诺。**

### 3.1 通用字段与约束

除明确例外，每张业务表包含以下通用字段，后续表格不重复列出；下文写“必填”表示业务必填，不是只要求前端校验。

| 字段 | 类型 | 必填 | 含义及约束 |
| --- | --- | --- | --- |
| id | bigint | 是 | 内部主键；外部接口序列化为字符串，避免整数精度丢失 |
| school_id | bigint | 是 | 学校边界，服务端从授权上下文确定；跨表关联必须同校 |
| created_at / created_by | datetime / bigint | 条件必填 | created_at 必填；业务记录 created_by 必填，系统作业使用可追踪服务主体；匿名失败审计允许为空，由 actor_type 标明 |
| updated_at / updated_by | datetime / bigint | 是 | 最后更新时间、主体；不可变版本及追加日志不设置这两个更新字段 |
| row_version | int | 是 | 可变对象乐观锁版本，初始 1；不等于业务历史版本；不可变版本及追加日志不设此字段 |
| deleted_at | datetime | 否 | 可回收主对象软删除时间；追加日志与历史版本不使用软删除隐藏历史 |

时间统一存 UTC、界面按学校时区显示；业务日期与学年不能用上传时间替代。金额统一 `decimal(18,6)` 并记录币种；计数/量值采用 `decimal(18,4)`，单位独立保存。JSON 必须有可验证结构，不用 JSON 数组替代核心外键关系。所有外键检验同校、同群、同建设周期及有效状态；物理外键或等价事务约束均需测试。下表 `?` 表示可空，其余字段必填；“条件必填”见说明。

### 3.2 组织、专业与身份

| 表及阶段 | 字段（除通用字段外） | 关键约束 |
| --- | --- | --- |
| `school` P0 | name varchar(100), code varchar(50), timezone varchar(50), status varchar(20) | 学校主表不另设 school_id；code 唯一，status=active/disabled |
| `department` P0 | name varchar(100), code varchar(50), parent_id bigint? | 同校 code 唯一；部门树无环 |
| `major` P0 | name varchar(100), code varchar(50), dept_id bigint, status varchar(20) | 同校 code 唯一；专业与专业群是不同对象 |
| `major_group` P0 | name varchar(100), code varchar(50), level varchar(20), status varchar(20), owner_user_id bigint, dept_id bigint, description text? | 同校 code 唯一；level=national/province/school/undetermined；status=declaring/building/accepting/completed/archived |
| `major_group_major` P0 | major_group_id bigint, major_id bigint, role varchar(20), valid_from date, valid_to date? | role=core/supporting；有效期不重叠，记录专业历史归属 |
| `construction_cycle` P0 | major_group_id bigint, name varchar(100), start_date date, end_date date, status varchar(20), basis_material_version_id bigint? | status=draft/active/closed；生效时任务书依据必填；结束日期不早于开始日期 |
| `sys_user` P0 | username varchar(100), real_name varchar(100), status varchar(20), phone varchar(30)?, email varchar(200)? | 同校 username 唯一；status=active/disabled；停用立即撤销会话和后台委托 |
| `user_identity` P0 | user_id bigint, provider varchar(30), provider_tenant_id varchar(100)?, external_subject varchar(200)?, password_hash varchar(255)? | 本地身份要求密码哈希，SSO 身份要求 provider_tenant_id 与 external_subject；禁止为纯 SSO 用户强制保存密码；外部身份组合唯一 |
| `major_group_member` P0 | major_group_id bigint, user_id bigint, role varchar(20), joined_at datetime, expires_at datetime? | role=owner/editor/viewer；同群同用户一条有效成员记录，失效即撤权 |
| `role_assignment` P0 | user_id bigint, role_code varchar(40), scope_type varchar(20), scope_id bigint, expires_at datetime? | scope_type=school/group；校级角色也只在本校显式授权范围生效 |
| `sys_role` / `sys_permission` / `sys_role_permission` P0 | role_code、role_name；permission_code；role_id、permission_id | role_code / permission_code 同校唯一；关系表复合唯一，不自动给运维人员业务读取权限 |

### 3.3 指标、修订与分期目标

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `indicator` P0 | major_group_id bigint, cycle_id bigint, stable_code varchar(50), current_revision_id bigint? | 稳定逻辑身份；同周期 stable_code 唯一；草稿允许尚无生效修订 |
| `indicator_revision` P0 | indicator_id bigint, revision_no int, parent_indicator_id bigint?, name varchar(200), description text?, metric_type varchar(20), unit varchar(20)?, calculation_rule json?, weight decimal(7,4)?, standard text, required_evidence json, responsible_dept_id bigint, responsible_user_id bigint, source_version_id bigint, source_locator json, effective_at datetime?, change_reason text? | metric_type=quantitative/qualitative；同指标修订号唯一；生效后不可改，权重范围 0–100。parent 必须同周期且无环；叶子指标是否计入统计由快照树确定 |
| `indicator_period_target` P0 | indicator_revision_id bigint, period_key varchar(50), period_start date, period_end date, target_numeric decimal(18,4)?, target_text text?, comparator varchar(20), aggregation_mode varchar(30), deadline date, applicability varchar(20), applicability_reason text? | comparator=gte/lte/range/manual；P0 自动计算仅 gte 正目标。数值或定性目标条件必填；aggregation_mode=cumulative_confirmed；applicability=applicable/not_applicable，不适用须批准；同修订 period_key 唯一；目标及适用性生效后不覆盖，更正创建新指标修订及目标 |
| `indicator_major_allocation` P0 | target_id bigint, major_id bigint, contribution_mode varchar(20), allocated_target decimal(18,4)?, note text? | mode=joint/independent；同目标同专业唯一；拆分不得擅自改变群级目标 |
| `indicator_log` P0 | indicator_id bigint, target_id bigint?, event_type varchar(40), old_value json?, new_value json?, reason text, actor_id bigint, occurred_at datetime | 只追加，记录修订生效、目标调整、不适用批准及状态变更；旧值不得被新值覆盖 |

任务书未正式批准时可用草稿开展演示，但看板、报告须显示“依据待确认”。年度、中期和终期目标分别建记录，不把多年累计成果直接当本年新增成果；跨年沿用须符合确认单规则。指标准则变更后显式重评，不直接沿用旧达成结论。

### 3.4 日常工作、成果与进展确认

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `work_record` P0 | major_group_id bigint, cycle_id bigint, author_id bigint, major_id bigint?, title varchar(200), occurred_on date, content text, status varchar(20) | status=draft/submitted/confirmed/returned；提交后改内容须退回或新建修订 |
| `work_record_material` P0 | work_record_id bigint, material_version_id bigint | 组合唯一；绑定确切版本 |
| `achievement` P0 | major_group_id bigint, cycle_id bigint, title varchar(200), business_key varchar(200), achieved_on date, owner_major_id bigint?, description text? | 同群同周期 business_key 唯一，如协议编号/奖项编号；无编号时人工确认去重键，不能由模型臆造业务编号 |
| `achievement_material` P0 | achievement_id bigint, material_version_id bigint | 组合唯一；证明同一成果的多份文件不能重复计成果 |
| `indicator_progress` P0 | target_id bigint, report_date date, actual_numeric decimal(18,4)?, actual_text text?, work_status varchar(20), declared_progress decimal(5,2)?, calculated_progress decimal(5,2)?, risk_level varchar(20), risk_reason text?, review_status varchar(20), submitted_by bigint, submitted_at datetime?, reviewed_by bigint?, reviewed_at datetime?, review_comment text?, supersedes_id bigint? | review_status=draft/submitted/confirmed/returned/withdrawn；数值/定性实际值按类型必填；确认时审核人与时间必填；历史记录不可覆盖，纠错用新记录替代 |
| `progress_evidence` P0 | progress_id bigint, material_indicator_id bigint | 组合唯一；提交时即可记录候选证据，但正式确认时必须为已确认的同目标关联 |
| `indicator_achievement` P0 | target_id bigint, achievement_id bigint, contribution_value decimal(18,4), confirmed_by bigint, confirmed_at datetime | 同目标同成果唯一；若按成果汇总，数值与去重成果总量不一致须解释并复核 |

`work_status` 使用 2.10 的业务状态；`risk_level=none/attention/high`。进展百分比限定 0–100；未填报实际值为 null，不能默认为 0。确认一条进展时，正式实际值、审核记录、证据引用与审计在同一事务或可恢复事务流程中提交。撤销记录必须保留原因与受影响对象。

### 3.5 素材、不可变版本与片段

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `material` P0 | major_group_id bigint, title varchar(300), current_version_id bigint?, uploader_id bigint, source_type varchar(30), classification varchar(20), visibility varchar(20), business_date date?, retention_until date? | source_type=upload/import/connector；classification=public/internal/restricted；visibility=private/group/restricted；默认 private，发布范围由人确认；上传中可无 current_version_id |
| `material_version` P0 | material_id bigint, version_no int, original_name varchar(300), mime_type varchar(100), file_size bigint, storage_key varchar(500), sha256 char(64), uploaded_by bigint, uploaded_at datetime | 同素材 version_no 唯一；不可变原件，内部存储键不直接返回普通用户；大小与类型核验；同名不覆盖 |
| `material_processing` P0 | material_version_id bigint, parser_version varchar(100)?, parse_status varchar(20), parsed_content_key varchar(500)?, error_code varchar(80)?, reviewed_status varchar(20), reviewed_by bigint?, reviewed_at datetime?, review_comment text? | 每版本一条当前处理状态；parse_status=pending/processing/succeeded/failed/unsupported；reviewed_status=pending/confirmed/returned/withdrawn；确认与解析成功分开 |
| `material_chunk` P0 | material_version_id bigint, chunk_no int, text_key varchar(500), text_hash char(64), locator json, index_version varchar(50)? | 同版本 chunk_no 唯一；定位记录 PDF 页/文本段、Word 段落/表格、Excel 工作表/单元格、PPT 页、图片区域；P1 音视频用起止毫秒；索引可重建 |
| `material_indicator` P0 | material_version_id bigint, target_id bigint, evidence_type varchar(50), origin varchar(20), confidence decimal(5,4)?, status varchar(20), confirmed_by bigint?, confirmed_at datetime?, reason text? | origin=ai/manual；status=suggested/confirmed/rejected/withdrawn；同版本同目标同证据类型唯一；confidence 范围 0–1，仅为建议可信度，不等于事实正确 |
| `material_major` P0 | material_id bigint, major_id bigint | 同校同群有效专业范围内关联，组合唯一；一材多专业不改变权限 |
| `material_metadata_suggestion` P0 | material_version_id bigint, field_name varchar(50), proposed_value json, confidence decimal(5,4)?, status varchar(20), reviewed_by bigint?, reviewed_at datetime? | field_name 限专业/主题/业务日期等白名单；status=suggested/accepted/rejected；采纳后写入对应业务字段，保留建议记录 |
| `material_tag` P0 | name varchar(50), tag_type varchar(20) | tag_type=system/user；同校同类型同名唯一 |
| `material_tag_relation` P0 | material_id bigint, tag_id bigint, origin varchar(20), confirmed_by bigint? | 组合唯一；AI 候选与人工确认分开；不再同时保存 ai_tags/manual_tags 两套权威标签 |
| `resource_grant` P0 | resource_type varchar(30), resource_id bigint, grantee_type varchar(20), grantee_id bigint, action varchar(30), expires_at datetime?, granted_by bigint | 对象、主体、动作组合唯一；允许同校指定共享，跨校共享默认禁止；授权不能扩大对象的模型出域范围 |

确认单中的“业务日期/年度”应写入人工确认元数据，不用模型猜测的年份直接参与统计。图片未 OCR 时可以登记与人工描述，但不得声称 AI 已读懂内容。解析失败可重试或人工补充，不丢失原件；重新解析产生新片段集合时，已引用片段保留。已确认素材换版后，新版本须重新审核，旧报告继续引用旧版本。撤回、删除与权限变更须同步使索引/缓存不可检索；保留历史不等于保留所有人的访问权。

### 3.6 任务、预警与通知

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `task` P0 | major_group_id bigint, cycle_id bigint, target_id bigint?, title varchar(200), description text?, assignee_user_id bigint, due_at datetime, status varchar(20), submitted_at datetime?, completed_at datetime? | status=todo/doing/submitted/done/cancelled；逾期是计算属性，不覆盖业务状态；确认完成不自动判指标达成 |
| `task_submission` P0 | task_id bigint, work_record_id bigint, review_status varchar(20), reviewer_id bigint?, reviewed_at datetime?, comment text? | review_status=submitted/confirmed/returned；采用工作记录关联素材，不存 related_material_ids 字符串 |
| `periodic_plan` P0 | major_group_id bigint, cycle_id bigint, period_type varchar(20), period_start date, period_end date, plan_kind varchar(20), trigger_mode varchar(20), content text, source_report_id bigint?, status varchar(20), confirmed_by bigint?, confirmed_at datetime? | period_type=week/month/year；plan_kind=summary/next_plan；trigger_mode=manual/scheduled；同群同周期同期间同类型唯一；确认后才进入正式统计 |
| `achievement_classification` P0 | achievement_id bigint, classification_code varchar(50), indicator_id bigint?, rule_version varchar(50), status varchar(20), confirmed_by bigint?, confirmed_at datetime?, note text? | 分类依据来自校方规则或模板；AI 只能建议；同一业绩可多分类但每项指标匹配须可追溯 |
| `business_item` P0 | major_group_id bigint, cycle_id bigint?, item_type varchar(40), name varchar(200), scope text?, owner_user_id bigint?, input_requirements json?, output_requirements json?, cadence varchar(20)?, status varchar(20) | item_type=professional_group/teaching_management/industry_school/other；支持新增事项；status=draft/confirmed/active/closed；不因未映射功能而删除 |
| `alert_rule` P0 基础/P1 可配 | major_group_id bigint, rule_type varchar(30), parameters json, enabled boolean, cooldown_minutes int | P0 固定 overdue/missing_evidence；规则变更记录版本 |
| `alert_event` P0 | rule_id bigint, target_type varchar(30), target_id bigint, window_key varchar(80), status varchar(20), triggered_at datetime, resolved_at datetime? | 同规则同对象同窗口去重；status=open/acknowledged/resolved；已提醒不等于问题已解决 |
| `notification` P0 站内/P1 外部 | recipient_id bigint, alert_event_id bigint?, channel varchar(30), dedup_key varchar(200), status varchar(20), sent_at datetime?, read_at datetime?, error_code varchar(80)? | channel=in_app/email/sms/connector；status=pending/sent/failed/unknown；外部发送结果未知先对账，不盲目重发 |

### 3.7 报告模板、快照、审核与引用

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `report_template` P0 | name varchar(100), type varchar(30), scope_type varchar(30), applicable_year varchar(20)?, batch_key varchar(50)?, current_version_id bigint? | type=application/task_book/implementation/annual/midterm/acceptance/weekly/monthly/yearly/other；scope_type=school/department/major_group/major；适用年度、批次可空但确认后应填写 |
| `report_template_version` P0 | template_id bigint, version_no int, storage_key varchar(500)?, source_notice_key varchar(500)?, instruction_key varchar(500)?, sample_key varchar(500)?, variable_schema json, section_schema json, attachment_schema json?, submission_schema json?, file_hash char(64)? | 同模板版本号唯一；模板、填写说明、正式通知和历史合格样例可分别登记；至少记录必填字段、表格结构、附件、命名及提交格式；无空白模板时记录依据来源 |
| `report` P0 | major_group_id bigint, cycle_id bigint, title varchar(300), type varchar(30), owner_user_id bigint, current_version_id bigint?, approved_version_id bigint? | 报告容器，不保存可被覆盖的唯一正式正文 |
| `report_version` P0 | report_id bigint, version_no int, template_version_id bigint, period_start date, period_end date, data_cutoff_at datetime, snapshot_key varchar(500), snapshot_hash char(64), content_key varchar(500), content_hash char(64), status varchar(20), generation_job_id bigint?, parent_version_id bigint?, change_summary text? | 同报告版本号唯一；status=draft/reviewing/returned/approved/invalidated/archived；正文和输入快照不可覆盖；AI 产物须关联生成作业，人工版本可空 |
| `report_citation` P0 | report_version_id bigint, section_key varchar(100), block_id varchar(100), claim_text text, progress_id bigint?, material_version_id bigint, chunk_id bigint?, locator json, quote_hash char(64)?, verification_status varchar(20), verified_by bigint?, verified_at datetime? | 汇总数字通过 progress_id 及报告统计快照追溯，多份依据用多条引用；稳定章节与段落标识，不用易漂移的 paragraph_index；verification_status=pending/valid/invalid；定位必填，人工图像引用可无 chunk_id |
| `review_record` P0 | target_type varchar(30), target_version_id bigint, reviewer_id bigint, action varchar(30), comment text?, acted_at datetime, content_hash char(64) | action=submit/approve/return/withdraw；只追加，退回/撤销原因必填；通过针对确切版本与哈希，作者不得自审 |
| `report_export` P0 | report_version_id bigint, format varchar(20), file_key varchar(500), file_hash char(64), exported_by bigint, exported_at datetime, citation_manifest_key varchar(500), status varchar(20) | format=docx/pdf；status=available/revoked/expired；输出权限与报告及所有引用证据校验，不能绕过限制 |

正文修改造成引用失效时标为待核验，不能沿用“审核通过”。没有证据的事实标“待补充”；“下一步计划”等建议明确标注，不伪装成已完成事实。正式报告审核需核对关键数字、结论与引文是否相符；链接可打开不代表证据能支持结论。快照包括目标、进展、成果、版本 ID 与口径，内部访问受权限控制；导出文档含可读的证据编号、文件名、版本和页段定位，不能只依赖会过期的临时链接。

### 3.8 异步作业、对话与模型成本

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `async_job` P0 | major_group_id bigint, type varchar(30), requested_by bigint, status varchar(30), idempotency_key varchar(100), input_snapshot_key varchar(500), attempt int, max_attempts int, progress decimal(5,2), started_at datetime?, finished_at datetime?, result_type varchar(30)?, result_id bigint?, error_code varchar(80)?, cancel_requested_at datetime? | type=parse/tag/generate/export；status=queued/running/succeeded/failed/cancel_requested/cancelled/unknown；同校同请求主体同类型同幂等键唯一；业务任务 task 与后台作业 job 不混用 |
| `conversation` P0 | major_group_id bigint, cycle_id bigint, owner_user_id bigint, title varchar(200)?, expires_at datetime? | 切换群或权限时重建受控上下文；不把前一群内容带入新会话 |
| `conversation_message` P0 | conversation_id bigint, role varchar(20), content_key varchar(500), query_scope json, data_cutoff_at datetime?, source_manifest_key varchar(500)?, related_job_id bigint? | role=user/assistant；回答保留查询范围和证据，按会话权限访问；消息只追加 |
| `model_config` P0 | provider varchar(100), model_id varchar(100), endpoint_ref varchar(200), credential_ref varchar(200), deployment_mode varchar(20), allowed_classifications json, capability_types json, enabled boolean | deployment_mode=local/approved_external；密钥只存引用，配置和可用性测试通过后启用；品牌不是能力保证 |
| `model_call` P0 | job_id bigint?, conversation_message_id bigint?, user_id bigint, major_group_id bigint, model_config_id bigint, model_version varchar(100), prompt_version varchar(100), policy_version varchar(100), request_id varchar(100), tokens_in bigint?, tokens_out bigint?, estimated_cost decimal(18,6)?, billed_cost decimal(18,6)?, currency char(3), status varchar(20), duration_ms bigint? | 至少关联作业或对话消息；status=started/succeeded/failed/unknown；区分估算和账单，未知费用不是 0；结束时记录 duration_ms，不写原始敏感提示词进普通日志 |
| `budget_policy` P0 | scope_type varchar(20), scope_id bigint, period_key varchar(50), currency char(3), limit_amount decimal(18,6), reserved_amount decimal(18,6), spent_amount decimal(18,6), on_exceed varchar(20) | scope_type=school/group；并发预占预算，on_exceed=block；管理员确认调整才继续，重试费用同样计入 |

### 3.9 审计及选配集成

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `audit_log` P0 | actor_type varchar(20), actor_id bigint?, major_group_id bigint?, module varchar(50), action varchar(50), target_type varchar(50)?, target_id bigint?, request_id varchar(100), job_id bigint?, before_hash char(64)?, after_hash char(64)?, detail json?, ip varchar(50)?, result varchar(20), occurred_at datetime | actor_type=user/service/anonymous；登录失败可无 actor_id；result=success/denied/fail/unknown；只追加，详情脱敏，不记录密钥或全量正文；普通管理员不可删除 |
| `integration_config` P1 | platform varchar(50), credential_ref varchar(200), direction varchar(20), approved_scope json, status varchar(20), authorized_by bigint, expires_at datetime? | direction=read_only/approved_write；默认只读；status=draft/enabled/disabled；权限、许可、出域模式验证通过方可启用 |
| `external_object_mapping` P1 | integration_id bigint, external_object_type varchar(50), external_object_id varchar(200), external_version varchar(100), local_type varchar(50), local_id bigint, last_synced_at datetime, content_hash char(64) | 外部标识与版本组合唯一；同源重放不产生重复素材；冲突进入人工处理 |
| `integration_sync_run` P1 | integration_id bigint, cursor_before text?, cursor_after text?, status varchar(20), received_count int, applied_count int, failed_count int, error_code varchar(80)? | status=running/succeeded/partial/failed/unknown；成功落库后才提交游标，补偿不覆盖人工修改 |
| `approval_flow` / `approval_task` P1 | flow_version、节点和审批范围；实例、target_version_id、当前节点、审批人及结果 | 动态多级审批为选配；P0 使用 review_record 固定单级审核 |
| `dict_type` / `dict_item` P0 | type_code；type_id、item_code、label、enabled | 类型与项目编码唯一；禁用不破坏历史含义 |

### 3.10 关系总览与最小样例

```text
学校 → 部门/用户/专业群 → 建设周期 → 指标 → 不可变指标修订 → 分期目标
专业群 ↔ 专业                 分期目标 → 进展确认 ↔ 成果与证据
素材 → 不可变素材版本 → 片段 ────────────────┘
模板 → 模板版本 → 报告版本 → 引用 → 素材版本/片段
                      ├→ 审核记录 → 正式导出
                      └→ 输入快照 / 生成作业 / 模型调用
```

例：某年度“新增合作企业”目标为 10 家；两位教师上传同一协议的扫描件与电子版，只形成一个成果。已确认累计 6 家时数值进度为 60%，状态为进行中；七份附件不等于七家。次年上传去年协议不自动计为次年新增。把目标修订为 12 家后，新报告使用新口径；旧报告仍保留 10 家目标及当时 6 家实际值，修改原因可追溯。

### 3.11 状态转换与结构化字段约定

| 对象 | 允许的主要转换 | 防止错误生效的约束 |
| --- | --- | --- |
| 工作记录/进展 | 草稿 → 提交 → 确认或退回；退回修改后重新提交 | 教师提交不自动确认；已确认进展纠错新建替代记录，保留撤销或替代关系 |
| 指标修订/分期目标 | 草稿 → 人工批准生效 → 被后续修订替代 | 同一统计日期选择唯一有效版本；调整目标后重新核对实际值，不自动继承旧达成结论 |
| 素材及证据关联 | 待确认/建议 → 确认或退回/拒绝；确认 → 撤回 | 版本解析成功、材料可用、关联适用是不同条件；撤回触发报告影响检查 |
| 报告版本 | draft → reviewing → approved 或 returned；approved → invalidated 或 archived | returned 修改产生新 draft 版本；审核中内容不可变；不允许 draft 直接变 approved |
| 后台作业 | queued → running → succeeded/failed/unknown；未结束时可请求取消 | 只有确认取消成功才记 cancelled；未知结果先对账，不直接重发 |

关键 JSON 结构必须在接口方案中展开校验，最小内容如下：`required_evidence` 是证据要求数组，每项包含 `evidence_type`、正整数 `min_count`、`required` 和可选有效期；`locator` 包含 `kind` 与相应页码、段落/表格、工作表/单元格、图片区域或音视频时间段；`calculation_rule` 包含规则类型、规则版本、值来源及舍入规则；`variable_schema` 包含变量名、类型、是否必填和缺失处理；`query_scope` 包含群、周期、期间和当前授权范围标识。客户端不能自定义可执行脚本或通过 JSON 扩大权限。

原始材料字典中的证据类型要求 `min_count>1` 时，只有已确认且去重后的有效版本达到最低数量，该类型才算满足；同一素材不同副本不重复计数。正式数据的删除、撤销、修订必须使看板、问答及待审核报告同步标记变化。

### 3.12 建设依据、条款、冲突与决定

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `basis_document` P0 | major_group_id, cycle_id, document_type, title, current_version_id?, status | document_type=application/task_book/implementation/other；稳定身份不保存可覆盖正文 |
| `basis_document_version` P0 | document_id, version_no, material_version_id, approval_status, approved_at?, effective_from?, effective_to?, supersedes_id? | approval_status=draft/pending/approved/invalid；同文档版本号唯一；已引用版本不可覆盖 |
| `source_clause` P0 | document_version_id, clause_type, stable_code?, text_key, locator, status, confirmed_by?, confirmed_at? | status=suggested/confirmed/rejected/conflicted/invalid；定位必填，正文可放受控内容存储 |
| `construction_item` P0 | major_group_id, cycle_id, stable_code, name, description?, status, current_revision_no | 同周期 stable_code 唯一；多份文件相关条款可归入同一事项 |
| `clause_item_relation` P0 | clause_id, item_id, relation_type, origin, status, reason?, confirmed_by?, confirmed_at? | origin=ai/manual；status=suggested/confirmed/rejected/invalid；未确认不进入正式依据 |
| `scope_conflict` P0 | major_group_id, cycle_id, subject_type, subject_id, conflict_type, source_manifest_key, impact_manifest_key?, status, owner_id? | status=open/reviewing/resolved/reopened；保留各来源，不覆盖冲突内容 |
| `scope_decision` P0 | conflict_id, decision_version, decision_text, reason, effective_scope, status, confirmed_by, confirmed_at, supersedes_id? | status=draft/effective/revoked/superseded；智能体不得填写 confirmed_by |

`construction_cycle.basis_material_version_id` 仅作为旧稿兼容字段，不再表达完整建设依据；正式关系由 `basis_document`、`source_clause` 和 `construction_item` 共同承载。

### 3.13 智能体任务、步骤、确认与写回

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `agent_task` P0 | major_group_id, cycle_id?, owner_user_id, conversation_id?, original_request_key, interpreted_goal, expected_output, status, current_step?, writeback_target_type?, writeback_target_id? | status=understanding/waiting_input/waiting_confirmation/running/waiting_human/completed/failed/cancelled；业务任务身份与 async_job 分开 |
| `agent_task_scope` P0 | task_id, major_ids?, period_start?, period_end?, permission_snapshot_key, knowledge_manifest_key, allowed_actions, data_cutoff_at? | 固定本次范围；恢复执行前重新校验当前权限 |
| `agent_task_step` P0 | task_id, sequence_no, protocol_stage, capability_code, input_snapshot_key, status, result_type?, result_id?, error_code? | protocol_stage=S0—S9；同任务序号唯一；步骤成功不等于业务已确认 |
| `agent_confirmation` P0 | task_id, step_id?, confirmation_type, proposed_change_key, impact_manifest_key?, required_role, status, decided_by?, decided_at?, decision_note? | status=pending/accepted/accepted_with_changes/rejected/returned/deferred；服务主体不能替代人工决定 |
| `agent_writeback` P0 | task_id, step_id, target_type, target_id, target_version_id?, action, request_id, result, ledger_entry_id? | result=success/fail/unknown；unknown 先只读对账，不直接重发 |

`conversation_message` 保存交流内容，`agent_task` 保存办理状态，业务对象保存正式结果；三者不能互相替代。

### 3.14 资料吸收、候选知识与发布

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `ingestion_batch` P0 | major_group_id?, purpose, submitted_by, visibility, status, registered_count, readable_count, decomposed_count, pending_review_count, released_count, failed_count, started_at, finished_at? | status=receiving/processing/waiting_review/partial/completed/failed；无群资料进入待分派范围 |
| `ingestion_item` P0 | batch_id, material_version_id, read_status, decompose_status, knowledge_status, error_code? | 分别记录读取、拆解和知识确认，不能只用一个“成功” |
| `candidate_object` P0 | ingestion_item_id, object_type, proposed_payload_key, source_locator, confidence?, status, reviewed_by?, reviewed_at? | status=suggested/accepted/accepted_with_changes/rejected/conflicted；接受后写入专用对象 |
| `knowledge_release` P0 | object_type, object_id, object_version_id?, major_group_id, scope_key, release_status, confirmed_by, confirmed_at, invalidated_at? | release_status=active/invalid；只有已确认对象可发布到正式知识范围 |
| `knowledge_issue` P0 | ingestion_item_id?, object_type?, object_id?, issue_type, description, status, assignee_id? | issue_type=conflict/unknown/restricted/duplicate/unreadable/uncovered；问题关闭需处理结果 |

### 3.15 内容整理任务与版本

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `content_transform_task` P0 | major_group_id, owner_user_id, purpose, audience?, output_type, structure_schema, status | output_type=text/table/presentation_content/other；可编辑内容不自动等于 Excel/PPT 成品 |
| `content_input_snapshot` P0 | task_id, source_type, source_id, source_version_id, included_at | 同任务同源版本唯一；新版本不静默替换本次输入 |
| `content_draft_version` P0 | task_id, version_no, parent_version_id?, content_key, source_manifest_key, change_summary?, status, created_by_type | status=draft/submitted/confirmed/rejected/archived；智能体和人工版本都保留来源 |
| `content_gap` P0 | task_id, section_key?, missing_type, description, status, resolved_by_type?, resolved_by_id? | 缺失内容留空或提示，不由模型编造 |

### 3.16 问题、差距与补充任务

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `business_issue` P0 | major_group_id, cycle_id?, source_type, source_id, issue_type, description, status, owner_id?, due_at?, closed_at? | status=open/confirmed/in_progress/waiting_review/closed/reopened；与 alert_event 分开 |
| `progress_calculation_snapshot` P0 | target_id, rule_version, data_cutoff_at, input_manifest_key, result_numeric?, result_text?, detail_key, status, calculated_at | 输入与结果不可覆盖；相同规则、截止点和输入摘要可幂等复用 |
| `progress_judgement` P0 | target_id, calculation_snapshot_id?, suggested_status?, official_status?, reason, status, confirmed_by?, confirmed_at?, supersedes_id? | official_status=achieved/not_achieved/insufficient_evidence/pending_scope；正式结论必须人工确认 |
| `gap_analysis` P0 | judgement_id, gap_type, reason, evidence_manifest_key, status | gap_type=quantity/work_pending/evidence_missing/period_mismatch/scope_pending/other |
| `corrective_action` P0 | gap_id, action_type, proposal, assignee_suggestion?, due_suggestion?, expected_output?, status | status=suggested/confirmed/rejected/converted；确认前不下达 |
| `corrective_task_relation` P0 | action_id, task_id, confirmed_by, confirmed_at | 同动作同任务唯一；任务完成后重新计算，不直接关闭指标差距 |

现有 `indicator_progress` 继续承载人员进展填报；`progress_calculation_snapshot` 承载确定性计算；`progress_judgement` 承载系统建议和人工正式结论，三者不再混用。

### 3.17 工作、任务、总结和引用结构补充

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `work_record_revision` P0 | work_record_id, revision_no, parent_revision_id?, occurred_on, title, content_key, status, change_reason?, created_by | 已确认记录纠错产生替代修订，不覆盖原内容 |
| `task_relation` P0 | task_id, relation_type, source_type, source_id, source_version_id?, status | relation_type=derived_from/parent/depends_on/supports；任务来源和上下级关系可追溯 |
| `task_revision` P0 | task_id, revision_no, title, description?, assignee_user_id, due_at, expected_output?, status, change_reason?, confirmed_by? | 调整责任人、节点或产出形成新修订；派发需负责人确认 |
| `periodic_summary_version` P0 | periodic_plan_id, version_no, input_snapshot_key, completed_facts_key, variance_key, unresolved_key, next_plan_key, status | content 作为可读成品，结构化事实和关系另存 |
| `periodic_summary_item_relation` P0 | summary_version_id, item_type, item_id, relation_type | relation_type=completed/variance/unresolved/next_task/source |
| `report_source_relation` P0 | report_version_id, section_key, block_id, source_type, source_id, source_version_id?, locator?, verification_status | 允许引用条款、事实、成果、计算、决定或材料；至少一种来源必填 |

`report_citation.material_version_id` 调整为可空；当引用汇总计算、事实或条款时由 `report_source_relation` 指向对应来源。正式事实至少有一条有效来源关系。

### 3.18 版本影响与建设账本

| 表及阶段 | 字段 | 关键约束 |
| --- | --- | --- |
| `change_impact_batch` P0 | changed_type, changed_id, previous_version_id?, current_version_id, detected_at, status | status=open/reviewing/completed；一次变化只形成一批影响分析 |
| `change_impact_item` P0 | batch_id, affected_type, affected_id, affected_version_id?, impact_type, suggestion?, status, reviewed_by?, reviewed_at?, resolution? | status=pending/confirmed_unaffected/recalculate/rewrite/review/invalidated/completed |
| `business_ledger_entry` P0 | major_group_id?, actor_type, actor_id?, action, target_type, target_id, target_version_id?, before_state_key?, after_state_key?, basis_key?, impact_manifest_key?, result, request_id, occurred_at | 只追加；表达业务对象变化；通过 request_id 与 audit_log/agent_writeback 关联 |

`audit_log` 记录技术调用与访问，`business_ledger_entry` 记录业务变化；二者都不得被普通管理员删除。

## 四、数据存储与一致性要求

- 关系主库、私有附件存储和检索索引分工明确。数据库类型、向量方案及是否使用独立向量库由数据规模、校方资源和 PoC 决定，不预先锁定厂商。国产数据库适配须实测，不承诺无修改兼容。
- 核心索引围绕 `(school_id, major_group_id, cycle_id)` 与状态、时间组合；唯一性按照第三章定义。不可变版本、关系去重、历史外键保护均由服务端约束验证。
- 新文件先做大小、真实类型、恶意文件和解压风险检查，再进入解析；P0 不自动执行宏、不抓取任意内网 URL。重复哈希提示只在用户有权看到的范围内返回。
- 建设周期关闭后只读；更正走有记录的修订。删除专业群不能级联清除报告和审计；已使用对象先归档，只有符合保留策略并经授权的清理作业才能物理删除。
- 提交审核、确认进展、启用指标版本使用并发版本检查；冲突返回明确提示。文件落库与索引更新分步时使用可恢复作业，界面展示未完成状态。
- 不按未经测量的“50 万行”直接分库分表。先做容量与查询评估，再确定分区、归档和扩容；索引、缓存、备份同样适用数据权限和保留策略。

## 五、接口与后台作业约定

以下路径为设计草案，不代表已有接口。前缀 `/api/v1`；认证方式随本地账号/SSO 方案确定，不能仅因使用 JWT 就视为完成权限校验。

| 模块 | 建议接口与行为 |
| --- | --- |
| 基础对象 | `/major-groups`、`/majors`、`/construction-cycles`，归档替代直接级联删除 |
| 指标 | `/indicators`、`/indicators/{id}/revisions`、`/indicator-targets`、`/indicator-targets/{id}/progress`，修订生效与进展确认独立动作 |
| 素材 | `/materials/uploads`、`/materials/{id}/versions`、`/materials/search`、`/material-indicator-links`；获取下载链接前重新鉴权；Excel 导入清单只能登记元数据，不能用本地路径冒充已上传证据 |
| 工作任务 | `/work-records`、`/tasks`、`/tasks/{id}/submissions`、`/notifications` |
| 问答 | `/conversations`、`/conversations/{id}/messages`；返回 scope、data_cutoff_at、来源清单 |
| 报告 | POST `/reports/generate` 返回 `job_id`；`/reports/{id}/versions`、`/report-versions/{id}/reviews`、`/report-versions/{id}/exports` |
| 作业 | GET `/jobs/{id}`、POST `/jobs/{id}/cancel`；仅发起人及授权管理员可查，无权者看不到任务存在性 |
| 看板与管理 | `/dashboards/overview`、`/dashboards/major-groups/{id}`、用户授权、模型预算和审计查询 |

响应统一包含 `request_id`；列表带稳定排序、分页及过滤条件；错误区分参数无效、无权限、版本冲突、预算不足、外部不可用和结果未知，不暴露内部路径。服务器从当前身份校验学校/群范围，禁止直接相信客户端传入 ID。

异步写入要求幂等键与输入摘要：同键同输入返回已有结果，同键异输入报冲突。自动重试仅针对可重试且已确认未产生重复副作用的阶段；建议最多 2 次重试，具体超时按负载冻结。未知结果先核对作业或供应商请求记录；取消是请求，不代表外部调用已停止或已免计费。作业执行与交付时再次校验发起人的当前权限；引用材料权限收紧时，相关报告与对话历史也必须重算访问资格，不能通过旧正文绕过撤权。撤权后不得继续交付结果；生成失败保留原草稿，不能用空内容覆盖已有报告。

## 六、AI 能力及可靠性边界

- **权限先于检索**：候选检索、重排、上下文拼接、缓存、答案、下载和导出均校验当前权限。不能先跨群检索再仅在界面隐藏结果。
- **结构化数据负责计算**：指标值、分母、权重和日期由确定性规则计算，模型仅解释和组织文字；提示词不能成为唯一的业务校验。
- **材料是数据**：材料中的指令不能提升权限、修改系统规则或触发外部工具。模型工具只允许列出的查询和草稿操作，正式写入走授权业务接口。
- **缺证据时停止断言**：对无依据、冲突、低质量 OCR 等情况列出缺项，允许生成明确标识的草稿，不补造达成事实。正式定稿前补足或明确处理缺项。
- **模型选择以实测为准**：在校方允许的数据处理范围内比较候选模型的中文长文、表格、引用、成本和时延；不预设某品牌一定便宜或适合报告。
- **失败降级不越界**：模型不可用时保留人工填报、查询及编辑；不自动从本地模型切换到外部服务。提示词、解析器、模板和模型版本进入调用/生成记录，便于复测。

## 七、权限与数据处理边界

### 7.1 角色矩阵

| 角色 | 默认允许范围 | 关键限制 |
| --- | --- | --- |
| 教师 | 本人工作记录、本人素材、获授权的群材料与任务 | 不自行确认指标达成，不查看其他群私有素材 |
| 专业群负责人 | 被授权群的指标、任务、进展确认与材料组织 | 不能跨群越权；本人撰写报告由独立审核人审核 |
| 教务审核人 | 被指派群/报告的证据核对、退回和定稿审核 | 无权调整系统密钥，不能随意扩大材料可见范围 |
| 校级业务负责人 | 本校已授权汇总及明细，可配置跨群查看范围 | 不是全系统超级用户；受限材料仍需单独授权 |
| 信息中心/运维管理员 | 账号、配置、服务运行、备份与恢复 | 默认不获得业务正文读取权限；临时排障访问有时限及审计 |
| 外部专家（选配） | 指定报告及必要证据，只读、限时 | 下载/导出独立授权，到期自动撤销 |

### 7.2 数据主权与处理边界

学校对数据库、文件、索引、报告、备份及其他业务数据资产拥有完整权利和数据主权。数据资产可以部署在学校内部服务器，也可以部署在学校租赁并控制的私域远程云服务器中；部署位置不改变学校的权利归属。

服务方提供云端服务能力和业务 Action，包括解析、检索、向量化、推理、生成、任务编排及结果回写能力。服务方云端不建立学校业务数据资源的持久化副本；一次任务所需的数据可按授权临时处理，完成、失败、取消或超时后清理，不进入服务方云端持久化缓存、日志、消息队列、备份或训练数据。需要恢复或续跑的任务状态与业务内容保存在学校数据环境，云端按授权重新读取。

| 模式 | 允许路径 | 禁止或条件 |
| --- | --- | --- |
| 学校数据环境 | 数据库、文件、索引、报告、业务记录及备份位于学校内部服务器或学校租赁并控制的私域远程云服务器 | 资源账号、访问授权、备份和导出由学校控制；服务方不得据此取得数据资产所有权 |
| 服务方云端 Action | 云端提供解析、检索、向量化、推理、生成和编排等服务能力，按授权读取学校数据并回写结果 | 不在服务方云端持久化学校业务数据，不用于训练或跨校复用；临时数据须按任务结束/异常清理 |
| 第三方能力（如有） | 仅可按学校批准范围临时处理必要数据 | 接收方、区域、字段、保留、训练用途、清理验证和期限逐项登记；未经批准不得调用 |

这里是固定的数据与服务分工，不是学校在“完全内网”和“允许外部服务”之间二选一。具体网络通道、访问对象、动作权限、临时处理期限和第三方条件另行登记。模式未确认前仅使用经批准的脱敏样例做原型。材料敏感级别与出域规则独立；模型、OCR、Embedding、遥测、错误日志及第三方文档存储均纳入同一边界。

保留期由学校制度和项目约定确认：回收站建议 30 天、备份建议 30 天、审计建议至少 2 年，均非本稿对法定期限的判断。恢复备份后必须重新应用删除/撤权清单，避免已撤销数据再次可见。正式报告引用证据按建设与归档要求保留；保留与合法清理冲突时暂停导出并由指定责任人处理。

密钥仅由受控后端使用，传输加密，附件默认私有；临时链接建议不超过 15 分钟，下载统一经工作站鉴权代理，内部短期存储链接不直接暴露；外部已下载副本无法远程撤回，按下载审计与学校管理流程处理。业务日志只记必要元数据；脱敏样例、演示数据与真实数据分开。任何模型训练、微调或跨校使用材料均须独立明确授权，未授权不执行。

## 八、部署、运维与交付

试点以可维护的最小部署为原则，是否引入集群、主从、高可用或多地域由可用性目标决定，不把 K8s、多副本或跨区存储列为未确认硬要求。服务方提供资源评估，校方确认网络、服务器、存储与模型算力承担方式。

上线前须完成：健康与失败作业监控、用量预警、备份校验、恢复演练、升级回退及故障联系人配置。恢复范围包含业务数据、附件版本、报告、授权与配置；向量索引可重建。RPO、RTO、维护窗口、服务时间、故障分级和响应时限填写确认单，不用“每日备份”替代恢复承诺。

交付清单：本期功能与验收证据、部署配置说明、字段及接口文档、管理员与教师手册、备份恢复手册、授权及数据处理清单、培训记录、已知限制、数据导出与退出方案。代码、部署包、配置、学校数据与通用技能的权属和交付方式单独书面确认，不从“免费试点”推导永久维护或全部知识产权承诺。

## 九、初始化、实施与变更

1. 使用获批准的一组试点材料；专业群、专业、成员、周期、任务书、指标规则、报告模板由校方指定负责人核实。
2. 本地账号或已选定 SSO 开通最小权限；至少配置两个不同权限范围用于隔离测试。无正式第二专业群时可用明确标记的测试群，不能冒充真实业务数据。
3. 先导入预览与错误清单，再由人确认入库；同一导入批次重放不重复插入，保留来源、批次号、成功/失败行及回退办法。
4. 模型配置初始禁用，完成连接、权限、出域和预算验证后启用一个已批准方案；不预置看似“可用”的未开通模型。
5. 按“资料核对→原型与字段确认→P0 建设→试点实测→问题修复→验收→推广决策”推进。工期在输入齐备、集成依赖和资源确认后估算，全校推广不自动包含在试点内。
6. 变更记录包含编号、提出人、原因、受影响功能/字段/验收条目、费用工期、数据迁移影响及批准人；两份文档同版更新，不静默扩大范围。

## 十、验收口径与追踪

以下是**建议验收基线，须与需求确认单一并冻结**，本次没有系统运行或验收结果。选配能力只有经确认进入范围才参与验收。安全、事实与审核关键项不得用平均分抵消。

| 编号 | 验收项与对应功能 | 方法及建议通过条件 |
| --- | --- | --- |
| A01 | 范围与基础档案；1.1–1.4、2.1/2.3/2.6/2.7 | 用选定试点群、专业、成员、周期及任务书导入指标；错误行可定位，同批重放不重复；群与专业数量无混淆 |
| A02 | 进度计算与证据；2.4/2.5/2.8、3.5/3.10/3.12、4.1–4.3 | 使用人工标注的至少 10 个指标案例，覆盖数值、定性、跨年、同成果重复、无数据、不适用和修订；预期实际值、分母与状态全部一致 |
| A03 | 素材与 AI 推荐；3.1–3.9 | 建议 100 份脱敏或已授权样例，覆盖约定的 P0 格式，明确各类型数量；至少 20 份含重复、坏文件、空文件、无关内容或无匹配指标。解析成功与失败必须正确呈现；人工复核的指标推荐精确率建议 ≥85%、召回率建议 ≥80%，二者分别统计，不能只少推荐以提高精确率 |
| A04 | 进度问答与权限；9.1/9.2、6.1–6.3 | 固定至少 20 个问题，涵盖时间范围、缺项、无资料、歧义及越权；数据与看板逐项一致，回答显示截止时间与来源；越权与无依据断言为 0 |
| A05 | 报告、引用与改稿；5.1–5.8、9.3 | 生成一份选定模板的完整报告；逐条检查所有事实/数字的依据、版本和定位，关键数字及达成结论错误为 0；正式稿事实引用核验通过率 100%，有缺项则不得按完整正式稿通过；局部改稿不覆盖其他人工内容 |
| A06 | 审核与导出；5.7/5.9/5.10 | 作者自审被拒绝；通过版本再次修改须重新审核；Word/PDF 的章节、表格、页码及引用清单完整无截断；草稿带标识，正式导出匹配审核版本及哈希 |
| A07 | 隔离与撤权；8.1–8.3、8.6 | 用至少两种群范围及受限素材测试列表、搜索、问答、缓存、下载、导出和后台作业；未授权正文、标题、数量及片段泄露为 0，撤权后重新请求不可访问 |
| A08 | 异步作业与成本；8.4/8.5、解析/生成/导出 | 模拟重复提交、并发编辑、超时、取消、外部结果未知、限额耗尽与模型故障；无重复正式记录、无静默覆盖、无越界模型切换；重试受限且费用可追踪 |
| A09 | 数据主权、云端 Action 与恢复；8.6/8.7 | 核对学校对数据资产的完整权利及访问授权、撤销、导出、迁移和删除控制能力；确认数据库、文件、索引、报告和备份位于学校内部服务器或学校租赁并控制的私域远程云服务器；验证云端按授权临时处理并回写结果，学校业务内容不进入服务方云端持久化存储、日志或备份，任务结束及异常后清理；用备份恢复样例，校验原件/报告哈希与授权，达到双方填写的 RPO/RTO；关键审计动作记录齐全 |
| A10 | 性能；查询/生成/导出 | 冻结硬件、网络、并发、数据规模、模型和报告篇幅后测试；建议查询 p95≤2 秒，已完成解析资料的报告生成 p95≤5 分钟、导出 p95≤30 秒；查询至少 100 次、生成/导出各至少 20 次，分别记录成功率和失败耗时，不删掉慢样本 |
| A11 | 试点使用与交付；全部 P0 | 指定教师独立完成一次填报，负责人查缺项并确认进展，审核人完成一次报告定稿；交付手册、培训、恢复记录、限制清单与缺陷处置，双方确认试点结果 |

统计说明：推荐精确率 = 人工确认正确的推荐关联数 / 全部推荐关联数；召回率 = 被正确推荐的关联数 / 标注集中应有关联数。每份材料可有多个正确关联；无匹配样本若被推荐则计入误报。分母为 0 记“不适用”并补足测试样例，不算 100%。样例集、参考答案、判定人及争议裁定人在测试前冻结；P1 OCR/转写须额外增加相应样本及文字、数字、定位核对指标。

验收证据至少包括测试日期、系统/模板/模型版本、样例编号、操作者、预期与实际结果、失败原因及复测结果。未通过条目必须修复复测或形成双方签署的范围调整；越权泄露、关键事实造假、审核绕过、原始证据损坏或恢复失败不按“已知限制”直接放行。

### 10.1 开发前必须关闭的决策

按《需求确认单》D01–D13 逐项关闭与本期相关的任务书、统计口径、模板、数据边界、角色、样例、集成、资源、验收、权属及新增业务事项问题。允许以获批脱敏样例先做原型，不能将原型验证写成生产可用或正式验收通过。

### 10.2 变更记录

| 版本 | 日期 | 内容 | 确认状态 |
| --- | --- | --- | --- |
| v1.0 | 原稿 | 八大模块及初步字段设计 | 待校方确认 |
| v1.1 | 2026-09-17 | 修正范围与优先级，补业务闭环、自然语言入口、进展统计、不可变版本、证据与审核、身份/数据边界、作业与预算、验收定义 | 审核完善稿，待双方确认 |
| v1.2 | 2026-09-18 | 同步需求确认单新增业务事项、周期性总结与计划、业绩分类、申报/任务书/实施方案及其他最终模板、教学管理选配事项；明确学校数据主权与学校数据环境—服务方云端 Action 分工；补充相关字段与验收口径 | 待双方确认 |
