# CAD 知识工程与审查系统衔接

KB-DESIGN-001；2026-10-16。参考目标态方案 v1.1，不修改其文件；历史实验数值只作为指定文档陈述，不代表本轮复现实验。

## 1. 建设目标：优先补 C2，不把 RAG 当识图器

参考方案 v1.1 指出 C1 的有限条目已有人工闭环，C2 对象与关联仍是重点；不能把命题与应用的数量差全部归因 C2。本方案将知识服务对准对象证据、条件、例外和正反案例，而不是继续单纯堆图片描述。

| 能力 | 知识库提供 | 审查系统仍负责 |
|---|---|---|
| C1 看清 | 符号字形/码位候选、解析器已知盲区、定位原图 | DXF/PDF/OCR 提取及交叉核对 |
| C2 看懂 | 零件/装配、孔/轴、标准件、视图特征及对照案例 | 对当前图的对象识别和几何/语境确认 |
| C3 知因 | 工程原理、工艺解释、可复用处理经验 | 针对当前对象解释与修正建议 |
| C4 判合规 | 已核条款、适用条件、例外、原文证据 | 确定性判据执行、PENDING/人工闭环 |

文件下载完整、语义相似、图像相似都不能自动完成 C2，更不能自动得到 C4。

**PDF 是客户主输入，DWG/DXF 是可选增强。** PDF-only 独立验收；逐页/区域区分原生字符、转曲、扫描及隐藏 OCR 层，原图和坐标始终可回查。CAD 增强先核图号、版本、变体及与 PDF 的配准，不能拿错误变体替代待审图。获取原生结构是解析优先原则，不是强制用户提供 CAD 源文件。

## 2. 与原四资产库的对应

| 原资产库 | 本方案对象 | 发布门槛 |
|---|---|---|
| 判据库 | Rule + Clause + Conditions + Exceptions | 原页/条款/版本核验，规则表达式独立审核 |
| 案例库 | Case + Positive/Negative + Object/Context | 图纸证据、配对完整、专家确认范围明确 |
| 知识库 | Explanation + Fact + Experience | 来源和适用范围；经验附复现证据 |
| 符号词典 | SymbolEntry + Shape + Codepoint + Context | 检索别名与判定等价分别核验 |

这四类共享资产身份和来源定位，不混为一个无类型的文本集合。

## 3. 对象与语境作为一等知识

ObjectEvidence 保存 drawing_kind、part_family、feature_kind、view_kind、assembly_role、geometry_evidence、annotation_evidence、units、coordinate_frame、support_status、counter_evidence。

每个标签允许 UNKNOWN 和 CONFLICTED。用户说“孔”不自动等于程序确认孔；图层名、块名、合成标签属于证据线索，不能自动成为图纸真值。几何关系必须附变换和定位，不把屏幕上相近的对象当拓扑相邻。

视图关系、剖切区域、件号/BOM 和同一零件跨视图关联应能定位原始依据。R1—R4 可分别利用这些知识，不要求先实现一个万能识别器。

对象库优先建立容易混淆的对照：孔/外圆、装配/零件、剖视/断面、滚动轴承/普通件、中心线/轮廓线、直径/半径、沉孔/埋头孔。检索至少取一个近似但不适用的反例，检验判别条件。

## 4. CAD 事实原子与定位

DrawingFact 建议保存：asset_version、layout、entity_handle、block_instance_path、transform、raw_type、raw_text/control_codes、measurement、override_text、display_value、unit_source、layer/linetype、bbox、extractor、parse_errors。

必须同时保留 DIMENSION 几何测量、显式覆盖文字和显示结果；用户覆盖尺寸文字可能导致几何值与标注值不一致，不能只取一项当“绝对真值”。图层线型只是编码事实，其工程含义还需对象/图层继承、BYBLOCK/BYLAYER 和局部上下文验证。

DWG→DXF 的损失报告与未解析代理实体进入 CoverageGap，关联受影响规则；不能因为主体实体无漏就声明符号类全部可判。

## 5. 符号词典：检索扩展不等于判定等价

保留 raw_glyph/crop、raw_codepoint、CAD_control_code、ocr_candidates、semantic_candidates、position、context、verified_mapping、mapping_source。

检索时可以对 Ø、⌀、φ 等候选扩展召回，但不能把检索别名无条件升级为标准允许的写法。ψ 等疑似 OCR/排版异常先挂争议，标准原图复核前不纳入自动等价。H7/h7、js、正负偏差、数量和螺距不得因转小写、去标点或普通分词丢失。

符号、数值和单位单独建精确字段；中文全文索引不能承担一个字符符号或两字符代号的全部召回责任。度、直径、深度和沉孔等词也需与位置/形态绑定。

初读 v1.0 时发现“埋头孔 ∨U+2227”的字符/码位疑点；当前 v1.1 已明确 ∨ 为 U+2228、∧ 为 U+2227，并将 ψ 放入 OCR 混淆候选。本方案采用该修订边界；具体工程形态仍需原页核准，不从码位名称直接推导适用性。

## 6. 规则与案例最小合同

Rule：rule_id、basis_type、basis_source/version、clause_id（仅国标类需要）、source_page/region、basis_verified、conditions、exceptions、required_object_evidence、executable_rule_ref/version、reviewer、status。国标、专家/手册、教材、参考答案和项目约定分型，不虚构条款号。

Case：case_id、task_type（READ_ERROR/REFERENCE_DIFF/RULE_VIOLATION）、source_versions、drawing_kind、part/feature/view、positive/negative_refs、raw_observation、object_evidence、rule_refs、expert_confirmation_scope、expected_verdict、limitations、split_group。

Experience：problem、environment、symptoms、hypothesis、confirmed_cause、steps、inputs、outcomes、validation、failure_cases、applicability、status。

只有“格式读到 H7”和“对象确认为孔”都成立，才允许尝试适用孔公差规则。v1.0 的 H7→h7 标签与对象待确认存在冲突；v1.1 已将其改为 PENDING。本方案采用新版状态，且进一步要求该标注与孔/轴对象的关联证据，直至图号/变体、显示及适用依据齐备。

case status=CONFIRMED 必须说明确认了什么：图面差异、对象身份、规则适用、结果哪个层级；不能一处确认覆盖全案例所有字段。缺反例的案例可以服务解释，但不能伪称已配对验证。

## 7. 三类数据集如何吸收

| 来源 | 已验收下载范围 | 知识库角色 | 不得自动推断 |
|---|---|---|---|
| ParaCAD 新版 | 37 文件，104899788120 字节 | 标注/几何结构候选、抽样分析、检索样本 | 宣传中的千万样本已逐件核验、全部符合国标 |
| TriView2CAD | 5 文件，12423539704 字节；PNG/DXF/metadata 配对已核 | 跨视图/几何-图像检索候选 | 已取得论文六模态或单独真实 3000 包 |
| TrOCR 工程图 | 1 原包，169991162 字节；1800/200 图文对已核 | 工程字符串、符号 OCR 评测与检索词典候选 | 含标准条款或有工程对象语义真值 |

下载身份与数字依据当前验收文件，不把原目标态表的宣传描述当落盘清单。三者都不能替代专家正误案例库和已核标准库。

TriView2CAD 当前元数据许可 CC-BY-NC-4.0；商业用途配置应阻断对应内容、派生摘要及向量进入商业任务检索，待获授权后再发布。ParaCAD Apache-2.0、TrOCR CC-BY-4.0 的具体归属、声明和使用条件在纳管时保留原许可记录；本方案不替代具体用途的授权核查。

教材、国标原文、企业图纸、专家经验分别登记使用范围；不能将“买了书”或“人工提炼”自动标成任意数字化、再分发和商用都获准。资料取得与用途授权是不同字段。

## 8. 审查系统接口边界

设计接口：retrieve_object_evidence、retrieve_applicable_rules、retrieve_contrast_cases、read_source_units、record_review_feedback。返回同一个 generation 与证据定位；具体 API 形态后续实施确定。

L0g/L1—L3 输出原始事实与候选对象；L4 调用本服务取得规则/案例证据；L4b 检查 mandatory 证据和 coverage gaps；不足进入 L5。知识服务不直接修改评分报告或用户图纸。

专家反馈先追加 review event；候选新案例完成来源、语境、配对和确认范围检查后发布新代际。反例进入评测保留集时不得同时进入检索提示库造成评测泄漏。

## 9. CAD 首批闭环

优先四个主题：装配与零件图的剖面线差异、轴承剖视例外、孔/轴公差语境、直径符号丢失。每个主题准备原图/实体证据、已核适用规则、正确样例、错误样例、近似不适用样例和未知语境样例。

T03 正确变体缺失、代理实体原生参数未核准、标准页只读部分、疑似符号映射等都保留待补，不因公开大数据量增加而自动关闭。C1 的 35/35、21 项含部分/子命题等只是原方案报告的局部历史分母，泛化验收必须用独立新图。

USD BRep 仅作为三维几何处理与未来案例工具候选，不强行放入当前二维判规主链。源码/API 知识可以入资料库，但能调用建模工具不代表具备图纸审查能力。

## 10. 与 v1.1 的任务和交付范围对齐

单图规范审查、参考答案对照、解释改进三类任务分开；案例差异标签不直接用于违规结论。知识包记录 task_type 与依据类型。产品输出问题位置、依据、建议及无法判定范围，评分与权重不作为本期知识库的前置交付。

PDF-only 与 CAD 增强、机器自动与专家闭环分别评测；某一知识主题通过不能替代整图产品验收。原文 v1.1 已纠正符号层 116 个实体为 94 代理+22普通，本方案按“可解析普通实体/可见显示/原生参数未核准”分层登记，而不是把整层都标不可达；本轮未复核源 DWG，数字仍标原文陈述。
