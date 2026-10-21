# Carbon 各业务域数据库表设计 · E-R 关系总览

> 数据来源：本地运行库直连（`pg8000 → localhost:49746`，public schema），非 README/类型推断。
> 提取时间：2026-10-04。库内共 **398 张表**（含 1 张运行期索引表 `searchIndex_*`，基础业务表约 397）。
> 行数（rows=）为当前 satellite seed 真实数据，用于验证"非空仓库"，非 mock。

## 0. 域分布总览（按表名前缀聚类）

| 业务域 | 表数 | 性质 | 与四合一关系 |
|---|---|---|---|
| 生产工单域 Production/Job | 19 | 四合一核心 | ERP+MES 制造执行主链路 |
| 生产事件/产量域 ProductionEvent | 2 | 四合一核心 | MES 执行层流水 |
| 工序/工艺域 Process/Procedure | 7 | 四合一核心 | 工艺路线主数据 |
| 库存/物料域 Inventory/MRP | 29 | 四合一核心 | MRP 物料主数据+库存账 |
| 质量/QMS 域 Quality | 27 | 四合一核心 | QMS 贯穿全链路 |
| 销售/CRM 域 Sales | 48 | ERP 周边 | 生产工单的**源头**（salesOrder→job） |
| 采购域 Purchasing | 30 | ERP 周边 | 物料补货的**源头**（purchaseOrder→item） |
| 零件/BOM 域 Parts | 15 | 主数据 | 制造方法/物料主数据 |
| 设备/资源域 Resources(MES) | 8 | MES 主数据 | 工作中心→工序排程 |
| 人员/组织域 People | 23 | 基座 | 多租户根 company + 用户/员工 |
| 财务域 Accounting | 11 | ERP | 库存过账→总账 |
| 文档域 Documents | 7 | 公用 | 附件/规范文档 |
| 开票/收款域 Invoicing | 3 | ERP | 应收/应付结算 |
| 配置域 Settings | 6 | 系统 | 租户级参数 |

> 其余 163 张"other"表为横切能力（审批 approval、工作流 workflow、标签 tag、审计 auditLog、SSO、通知、序列号 sequence、单位制 unitOfMeasure、地址 address 等），几乎被所有域引用，属"平台底座"。

---

## 1. 生产工单域（Production / Job）—— 19 表

**域定位**：ERP 制造订单 → MES 排程执行的聚合根。`job` 是整个四合一系统的**物理枢纽**，上接销售订单、右挂物料 BOM、下接工序排程、内嵌质量文档。

| 表名 | 行数 | 用途 | 业务链路位置 | 关键关联表（FK 目标） |
|---|---|---|---|---|
| `job` | 21 | 生产工单（制造订单），聚合产品的完整制造上下文 | 链路根：salesOrder → **job** → jobOperation → productionEvent → productionQuantity → inspection | item, quote, salesOrder, salesOrderLine, customer, location, unitOfMeasure |
| `jobFavorite` | 1 | 用户收藏的工单 | 个人视图层 | job, user |
| `jobMakeMethod` | 46 | 工单的"制造方法/工艺路线"(route)，含 BOM 层级 parentMaterial | job 下的工艺路线定义 | job, item, jobMaterial(父物料), trackedEntity |
| `jobMaterial` | 154 | 工单物料需求（BOM 展开行），逐工序消耗 | job ↔ item 的物料桥 | job, item, jobOperation, jobMakeMethod, storageUnit, unitOfMeasure |
| `jobMaterialStep` | 0 | 物料步骤（物料在工序中的分步投入） | 工序物料细粒度 | jobMaterial, jobOperationStep |
| `jobOperation` | 119 | **工序级排程单元**（MES 排程板核心），每工单含多条工序 | 排程核心：jobOperation ← procedure/process/workCenter/inspectionDocument | job, procedure, process, workCenter, inspectionDocument, assemblyInstruction, jobOperationBatch, rework |
| `jobOperationBatch` | 1 | 工序生产批次（含工作中心/库位/工艺） | 工序→批次→事件 | workCenter, process, location, jobOperation |
| `jobOperationDependency` | 76 | 工序间的先后依赖（自引用前置工序） | 排程约束 | jobOperation(dependsOnId→自身), job |
| `jobOperationNote` | 2 | 工序备注，可挂到产量记录 | 执行备注 | productionQuantity, user |
| `jobOperationParameter` | 31 | 工序运行参数（如温度/转速） | 工序参数 | jobOperation, user |
| `jobOperationStep` | 49 | 工序操作步骤（关联装配指导步骤） | 操作 SOP | jobOperation, assemblyInstructionStep, nonConformanceActionTask |
| `jobOperationStepRecord` | 10 | 步骤执行记录（谁做的） | 操作留痕 | jobOperationStep, user |
| `jobOperationStepSlide` | 0 | 步骤的 3D/模型幻灯片 | 可视化指导 | jobOperationStep, modelUpload |
| `jobOperationTool` | 5 | 工序所用工具（工具本身也是 item） | 工序↔工具 | jobOperation, item(工具), tool |
| `jobOperationToolStep` | 0 | 工具在步骤中的使用 | 工具细粒度 | jobOperationTool, jobOperationStep |
| `nonConformanceJobOperation` | 1 | 工单工序关联的不合格(NCR) | 质量↔生产工序 | jobOperation, nonConformance |
| `assemblyPlanJob` | 0 | 装配计划工单（预留） | 装配域 | modelUpload, user, company |
| `employeeJob` | 1 | 员工-工单分配（谁负责哪个工单/班次/部门） | 人员↔工单 | user, department, location, shift |
| `printJob` | 5 | 工单/标签打印任务 | 输出层 | company, user |

**域 ER 小结**：`job` 1→N `jobOperation`（排程），`jobOperation` 1→N `jobMaterial`（物料按工序消耗）；`jobOperationDependency` 自引用构建 DAG 排程图；`jobMakeMethod` 承载 route，`jobMaterial` 是其 BOM 展开。NCR 通过 `nonConformanceJobOperation` 反向挂到工序。

---

## 2. 生产事件/产量域（Production Event）—— 2 表

**域定位**：MES 执行层的实时流水，把"排程"变成"实绩"。

| 表名 | 行数 | 用途 | 业务链路位置 | 关键关联表 |
|---|---|---|---|---|
| `productionEvent` | 27 | 产线事件（setup/labor/machine/scrap 等节拍事件） | 执行实绩：jobOperationBatch/JobOperation → **event** → quantity | jobOperation, jobOperationBatch, workCenter, employee(user) |
| `productionQuantity` | 12 | 产量记录（良品/废品），废品挂报废原因 | 实绩汇总：event → **quantity**(good+scrap) | jobOperation, inspection, inspectionSample, scrapReason, productionEvent(setup/labor/machine) |

**域 ER 小结**：一个 `productionEvent` 可派生一条 `productionQuantity`（良品 + 废品）；废品通过 `scrapReason` 进入质量域归因。

---

## 3. 工序/工艺域（Process / Procedure）—— 7 表

**域定位**：工艺路线主数据，是"制造方法"的可复用模板，被工单工序、工作中心、供应商共享。

| 表名 | 行数 | 用途 | 业务链路位置 | 关键关联表 |
|---|---|---|---|---|
| `process` | 12 | 通用"工艺/过程"定义（最小制造单元） | 工艺根：被 procedure/workCenterProcess/supplierProcess/jobOperationBatch 引用 | company |
| `procedure` | 4 | 工艺规程（含步骤的正式工艺文档） | 工艺模板：jobOperation.procedureId | process, user |
| `procedureParameter` | 9 | 规程参数 | 工艺参数 | procedure |
| `procedureStep` | 19 | 规程步骤（带单位/工时） | 工艺步骤 | procedure, unitOfMeasure |
| `workCenterProcess` | 15 | 工作中心可执行的工艺（能力矩阵） | 工作中心↔工艺 | workCenter, process |
| `supplierProcess` | 3 | 供应商可执行的工艺（外协） | 供应商↔工艺 | supplier, process |
| `nonConformanceActionProcess` | 1 | 不合格处置动作关联的工艺 | 质量↔工艺 | nonConformanceActionTask, process |

**域 ER 小结**：`process` 是工艺原子；`workCenterProcess`/`supplierProcess` 分别声明"谁能做这个工艺"（内作/外协）；`procedure` 把多个 `process` 编排成可重复工艺规程，被工单工序直接引用。

---

## 4. 库存/物料域（Inventory / MRP）—— 29 表

**域定位**：MRP 物料主数据 + 库存分类账，`item` 是仅次于 `job` 的被引用之王（被 74 张表引用）。

| 表名 | 行数 | 用途 | 业务链路位置 | 关键关联表 |
|---|---|---|---|---|
| `item` | 37 | 物料/零件主数据（库存核心，被 74 表引用） | 物料根：jobMaterial/quoteMaterial/purchaseOrderLine/inspection 都指向它 | unitOfMeasure, modelUpload, changeOrder, user |
| `itemCost` | 37 | 物料成本（标准/实际） | 成本 | item, itemPostingGroup |
| `itemPlanning` | 74 | 物料计划（MRP 计算后的计划订单） | MRP 输出 | item, location |
| `itemReplenishment` | 37 | 补货规则（含首选供应商） | 补货：→purchaseOrder | item, supplier(首选), unitOfMeasure |
| `itemPostingGroup` | 5 | 库存过账组（映射到会计科目） | 库存↔财务 | company |
| `itemUnitSalePrice` | 37 | 物料销售单价（多币种） | 销售定价 | item, currencyCode, unitOfMeasure |
| `itemStockQuantities` | 20 | 库存数量汇总（无 FK，冗余汇总表） | 实时库存视图 | （汇总） |
| `itemLedger` | 40 | 物料分类账（库存收发明细流水） | 库存流水：→scrapReason | item, location, storageUnit, scrapReason, trackedEntity |
| `itemShelfLife` | 1 | 保质期规则（触发工艺） | 效期 | item, process(触发) |
| `itemSerialSequence` | 2 | 序列号规则 | 序列追踪 | item |
| `itemSupersession` | 1 | 物料替代（旧→新 successor） | 工程变更 | item, successorItem |
| `itemInspectionDocumentAssignment` | 2 | 物料→检验文档分配 | 质量↔物料 | item, inspectionDocument |
| `inventoryCount` / `inventoryCountLine` | 2 / 11 | 库存盘点单 + 行 | 盘点 | location, item, user |
| `location` | 2 | 库位（被 53 表引用） | 仓储位置根 | company |
| `stockTransfer` / `stockTransferLine` | 3 / 3 | 库存转移单 + 行（可关联工单/物料） | 移库 | location, storageUnit, item, job, jobMaterial |
| `customerItemPriceOverride` / `Break` | 1 / 2 | 客户级物料价格覆盖+断点 | 客户定价 | customer, item, customerType |
| `customerLocation` | 4 | 客户收货地址 | 客户↔地址 | customer, address |
| `customerPartToItem` | 2 | 客户零件号→本司 item 映射 | 客户物料映射 | customer, item |
| `changeOrderAffectedItem` | 3 | 工程变更影响的物料 | 变更↔物料 | changeOrder, item, makeMethod |
| `enforcementRuleItemAssignment` | 8 | 执行规则(合规)→物料分配 | 合规 | enforcementRule, item |
| `maintenanceDispatchItem` / `TrackedEntity` | 2 / 0 | 设备维护派工用料 | 维护↔物料 | maintenanceDispatch, item, trackedEntity |
| `maintenanceScheduleItem` | 1 | 维护计划物料 | 维护计划 | maintenanceSchedule, item |
| `nonConformanceItem` / `TrackedEntity` | 6 / 0 | 不合格物料 + 其追踪实体 | 质量↔物料 | nonConformance, item, trackedEntity |
| `supplierLocation` | 10 | 供应商地址 | 供应商↔地址 | supplier, address |

**域 ER 小结**：`item` 是物料主数据根；`itemPlanning`/`itemReplenishment` 是 MRP 计划与补货，`itemReplenishment.preferredSupplierId` 直接驱动采购；`itemLedger` 是库存流水（事件溯源式），`itemStockQuantities` 是其冗余汇总；`location` 是仓储位置根，被全库 53 表引用。

---

## 5. 质量/QMS 域（Quality）—— 27 表

**域定位**：QMS 核心。`nonConformance`(NCR) 是质量域的放射状枢纽，贯穿采购-库存-生产-销售-发运全链路；`inspection` 是执行层检验记录。

| 表名 | 行数 | 用途 | 业务链路位置 | 关键关联表 |
|---|---|---|---|---|
| `qualityDocument` | 3 | 质量文档（SOP/规范） | 质量文档根 | user |
| `qualityDocumentStep` | 3 | 质量文档步骤 | 文档步骤 | qualityDocument, unitOfMeasure |
| `inspectionDocument` | 3 | 检验文档模板（partId→item） | 检验模板：jobOperation.inspectionDocumentId | item(零件), user |
| `inspectionFeature` | 6 | 检验特性（尺寸/外观等，带量具类型） | 检验特性 | inspectionDocument, gaugeType |
| `inspection` | 4 | 实际检验记录（含处置人/供应商） | 检验执行：→inspectionMeasurement | inspectionDocument, item, supplier, user |
| `inspectionSample` | 6 | 检验样本 | 抽样 | inspection, trackedEntity |
| `inspectionMeasurement` | 12 | 测量值（特性×样本） | 测量数据 | inspection, inspectionFeature, inspectionSample, user |
| `inspectionSamplingPlan` | 8 | 抽样方案（AQL 等） | 抽样规则 | inspection, inspectionFeature, gauge |
| `inspectionHistory` | 2 | 检验历史 | 历史 | inspection, item, supplier |
| `nonConformance` | 5 | **不合格单 NCR**（质量枢纽） | NCR 根：放射状关联各业务单据 | nonConformanceType, nonConformanceWorkflow, location, user |
| `nonConformanceType` | 10 | 不合格类型（分类） | NCR 分类 | company |
| `nonConformanceWorkflow` | 3 | 不合格处置工作流 | NCR 流程 | company |
| `nonConformanceRequiredAction` | 12 | 要求采取的措施（措施库） | 措施定义 | company |
| `nonConformanceActionTask` | 7 | 措施任务（执行） | 措施执行：→process | nonConformance, nonConformanceRequiredAction, supplier, user |
| `nonConformanceApprovalTask` | 1 | NCR 审批任务 | 审批 | nonConformance, user |
| `nonConformanceReviewer` | 2 | NCR 评审人 | 评审 | nonConformance, user |
| `scrapReason` | 3 | 报废原因（被 productionQuantity/itemLedger 引用） | 报废归因 | company |
| `nonConformanceCustomer` | 1 | NCR 关联客户 | 质量↔客户 | nonConformance, customer |
| `nonConformanceSupplier` | 2 | NCR 关联供应商（含外部链接） | 质量↔供应商 | nonConformance, supplier, externalLink |
| `nonConformanceInspection` | 1 | NCR 关联检验 | 质量↔检验 | nonConformance, inspection |
| `nonConformanceJobOperation` | 1 | NCR 关联生产工序 | 质量↔生产 | nonConformance, jobOperation |
| `nonConformanceItem` / `TrackedEntity` | 6 / 1 | NCR 关联物料 + 追踪实体 | 质量↔物料 | nonConformance, item, trackedEntity |
| `nonConformancePurchaseOrderLine` | 1 | NCR 关联采购订单行（来料不良） | 质量↔采购 | nonConformance, purchaseOrder, purchaseOrderLine |
| `nonConformancePurchaseReturnOrderLine` | 1 | NCR 关联采购退货行 | 质量↔采购退货 | nonConformance, purchaseReturnOrderLine |
| `nonConformanceReceiptLine` | 0 | NCR 关联收货行 | 质量↔收货 | nonConformance, receipt, receiptLine |
| `nonConformanceSalesOrderLine` | 1 | NCR 关联销售订单行（客诉） | 质量↔销售 | nonConformance, salesOrder, salesOrderLine |
| `nonConformanceSalesReturnOrderLine` | 1 | NCR 关联销售退货行 | 质量↔销售退货 | nonConformance, salesReturnOrderLine |
| `nonConformanceShipmentLine` | 0 | NCR 关联发运行 | 质量↔发运 | nonConformance, shipment, shipmentLine |
| `nonConformanceActionProcess` | 1 | NCR 措施关联工艺 | 质量↔工艺 | nonConformanceActionTask, process |

**域 ER 小结（质量贯穿全链路）**：`nonConformance`(NCR) 通过一组 `nonConformance{Source}` 表放射状挂接到 **采购订单行 / 采购退货 / 收货 / 销售订单行 / 销售退货 / 发运 / 客户 / 供应商 / 检验 / 生产工序 / 物料**——证明 QMS 不是独立模块，而是横切采购-库存-生产-销售的质量闭环。`inspection`(执行) 由 `inspectionDocument`(模板) 驱动，`productionQuantity.scrapReasonId` 把废品归因到 `scrapReason`。

---

## 6. 四合一跨域主链路 E-R（核心结论）

Carbon 把 ERP/MRP/MES/QMS 压进**同一 schema、同一租户、同一工单对象**，通过外键而非微服务边界耦合：

```
[销售] salesOrder ──salesOrderId──▶ job ◀──itemId── [库存] item
                                        │
        job ──jobOperation──▶ jobOperation ──workCenterId──▶ workCenter (MES)
                                        │  ├──procedureId──▶ procedure ──processId──▶ process (工艺)
                                        │  ├──inspectionDocumentId──▶ inspectionDocument (质量模板)
                                        │
        jobOperation ──jobOperationBatch──▶ productionEvent ──▶ productionQuantity
                                        │                        └──scrapReasonId──▶ scrapReason
                                        │
        jobOperation ──jobMaterial──▶ item (BOM 消耗) ◀──itemReplenishment.preferredSupplierId── [采购] supplier
                                        │
        nonConformance(NCR) ──放射状──▶ {salesOrderLine, purchaseOrderLine, receiptLine,
                                           shipmentLine, jobOperation, item, customer, supplier, inspection}
```

**一个 `job` 同时是**：ERP 制造单据（含销售订单/报价溯源）、MES 排程单元（jobOperation+workCenter+process）、QMS 检验对象（inspectionDocument+productionQuantity.scrapReason）、MRP 物料消费者（jobMaterial→item）。这就是"四合一"在数据库层的实质。

---

## 7. 其余业务域核心表与四合一关联

> 以下域为 ERP 周边与主数据，不逐表展开（完整表名见第 0 章）。仅列与四合一直接耦合的核心表。

### 7.1 销售/CRM 域（48 表）—— 生产的源头
| 核心表 | 用途 | 与四合一关联 |
|---|---|---|
| `salesOrder` / `salesOrderLine` | 销售订单/行 | `job.salesOrderId` / `job.salesOrderLineId` 驱动生产 |
| `quote` / `quoteLine` / `quoteMakeMethod` | 报价+BOM(制造方法) | `job.quoteId`；报价即"预生产 BOM" |
| `customer` | 客户主数据 | `job.customerId`；`customerItemPriceOverride` 定价 |
| `opportunity` | 商机 | 销售漏斗 |
| `salesInvoice` / `salesReturnOrder` | 销售发票/退货 | 财务应收；退货可触发 NCR |
| `supplierQuote` | 供应商报价 | 采购比价 |

### 7.2 采购域（30 表）—— 物料补货的源头
| 核心表 | 用途 | 与四合一关联 |
|---|---|---|
| `purchaseOrder` / `purchaseOrderLine` | 采购订单/行 | `itemReplenishment.preferredSupplierId` 驱动；来料不良→`nonConformancePurchaseOrderLine` |
| `supplier` | 供应商主数据 | `itemReplenishment`、外协 `supplierProcess`、NCR |
| `receipt` / `receiptLine` | 收货 | 收货不良→`nonConformanceReceiptLine` |
| `purchaseInvoice` / `purchaseReturnOrder` | 采购发票/退货 | 财务应付 |
| `purchasingRfq` | 采购询价 | 比价 |

### 7.3 零件/BOM 域（15 表）—— 主数据
| 核心表 | 用途 | 与四合一关联 |
|---|---|---|
| `part` | 零件主数据 | `inspectionDocument.partId`(零件→检验模板) |
| `material` / `material*`(grade/type/finish/form) | 原材料主数据+属性 | 物料定义 |
| `makeMethod` | 制造方法(route)模板 | `changeOrderAffectedItem.baseMakeMethodId`；job/quote 复用 |
| `department` / `partner` | 部门/合作方 | `employeeJob.departmentId` |

### 7.4 设备/资源域（MES，8 表）
| 核心表 | 用途 | 与四合一关联 |
|---|---|---|
| `workCenter` | 工作中心（被 53 表引用） | `jobOperationBatch.workCenterId`；MES 排程资源 |
| `tool` / `workCenterShift` | 工具/班次 | `jobOperationTool`；排程资源 |
| `workCenterReplacementPart` / `methodOperationTool` | 工作中心替换件/工艺工具 | 维护与工艺 |

### 7.5 人员/组织域（23 表）—— 多租户基座
| 核心表 | 用途 | 与四合一关联 |
|---|---|---|
| `company` | **多租户根**（每张业务表都有 companyId） | 全局隔离根 |
| `user` / `employee` / `team` / `department` | 用户/员工/团队 | `job.assignee`、`productionEvent.employeeId`、审批人 |
| `companyGroup` / `userToCompany` | 集团/用户-公司映射 | 多租户 |

### 7.6 财务域（11 表）/ 文档域（7 表）/ 开票域（3 表）/ 配置域（6 表）
| 域 | 核心表 | 与四合一关联 |
|---|---|---|
| 财务 | `account`/`journal`/`journalLine`/`itemPostingGroup` | `itemPostingGroup` 把库存过账映射到 `account`；库存流水→总账 |
| 文档 | `document`/`documentTemplate` | 质检报告/工艺文档附件 |
| 开票 | `invoice`/`payment`/`paymentTerm` | 应收应付结算 |
| 配置 | `config`/`configurationParameter`/`configurationRule` | 租户级参数（Edition 门控、合规规则） |

---

## 8. 全局设计纪律（写设计笔记时复用）

1. **单 schema 多租户**：每张业务表带 `companyId`，`company` 是隔离根。
2. **审计四列**：`createdBy`/`createdAt`/`updatedBy`/`updatedAt` 几乎全表具备。
3. **自定义前缀 ID**：`id('job')`/`xid()` 生成可读业务单号（J000001 等），非裸 UUID。
4. **枚举状态机**：`jobStatus`/`qualityDocumentStatus`/`nonConformanceStatus`/`disposition` 等用 Postgres 枚举，状态机驱动流程，非软删。
5. **jsonb 逃逸舱**：`customFields` 承接租户定制字段，避免频繁加列。
6. **事件溯源式账本**：`itemLedger`/`productionEvent`/`productionQuantity` 用流水记录而非仅存余额，`itemStockQuantities` 是冗余汇总。
7. **1092 迁移线性演进**：2023-01 → 2026-10 时间戳迁移，add column 不重建表，契约即迁移。

> 对栖月汇订单域的 6 条借鉴点见《Carbon 数据库设计笔记.md》。本文件是其 E-R 展开版。
