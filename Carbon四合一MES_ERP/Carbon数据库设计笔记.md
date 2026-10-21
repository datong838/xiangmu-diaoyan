# Carbon 数据库设计笔记（job / inventory / qualityDocument 三域精读）

- **来源**：直连本机运行库 `postgresql://postgres:postgres@localhost:49746/postgres`（Carbon `crbn up` 栈），`information_schema` + `pg_constraint` 实测提取。非照抄迁移 SQL，是**当前真实 schema**。
- **总览**：`public` schema 共 **368 张基表**，由 **1092 个时间戳迁移**（2023-01-23 → 2026-10-03，约 3.7 年线性演进）逐步长出。本笔记聚焦生产/库存/质量三域核心表 + 三域互联关系。
- **证据（真数据行数）**：`job`=21、`jobOperation`=119、`item`=37、`qualityDocument`=3、`nonConformance`=5（= satellite seed 数据集，与 MCP `production_getJobsList` 返回一致）。
- **边界**：纯研究笔记，未改 aos-platform、未改 Carbon 库结构。

---

## 0. 跨所有表的全局设计纪律（先读这段）

Carbon 把"单 schema 多域"做到极致，几乎所有业务表共享同一套约定：

| 约定 | 形态 | 说明 |
|---|---|---|
| **多租户隔离** | `companyId text NOT NULL` | 368 表里绝大多数业务表都带此列，RLS 据此按公司隔离。是"单库多公司"的基石。 |
| **审计四列** | `createdAt timestamptz NOT NULL DEFAULT now()` / `createdBy text` / `updatedAt` / `updatedBy` | 几乎每张表都有，强一致审计轨迹。 |
| **自定义 ID 生成器** | `id text NOT NULL DEFAULT id('job'::text)` | 前缀式可读 ID：`job_`(job) / `jo`(jobOperation) / `jmat`(jobMaterial) / `pro`(procedure) / `wc`(workCenter) / `item` / `ipg`(itemPostingGroup) / `qdoc`(qualityDocument) / `qds` / `nc`(nonConformance) / `sr`(scrapReason)。部分表用 `xid()`（如 nonConformanceItem）。 |
| **枚举驱动状态机** | `status USER-DEFINED NOT NULL DEFAULT 'Draft'::"jobStatus"` | 大量 Postgres ENUM：`jobStatus`/`deadlineType`/`factor`/`methodOperationOrder`/`operationType`/`jobOperationStatus`/`methodType`/`procedureStatus`/`itemReplenishmentSystem`/`itemTrackingType`/`sourcingType`/`itemRevisionStatus`/`itemReorderingPolicy`/`qualityDocumentStatus`/`nonConformanceStatus`/`disposition`/`samplingPlanType` 等。 |
| **扩展逃逸舱** | `customFields jsonb` / `configuration jsonb` / `notes jsonb` + `tags text[]` | 每公司自定义字段不走迁移，直接进 jsonb；标签用数组。 |
| **软状态而非软删** | `status` 枚举（Draft/Registered/.../Complete） | 找不到 `deleted_at`，废弃用状态枚举表达，历史可追溯。 |
| **时间统一** | 全部 `timestamp with time zone` | 无 `timestamp without tz`，避免时区歧义。 |

> 关键启示：Carbon 用 **`companyId` 列级隔离 + `customFields` jsonb 逃逸 + 枚举状态机** 三件套，在不分裂 schema 的前提下同时满足了"多租户"和"每客户定制"，这是它敢把 ERP/MES/QMS 压进单库还能长 1092 迁移的工程底气。

---

## 1. 生产（PRODUCTION）域

**枢纽表 `job`（41 列）**——一张工单聚合了来源、对象、数量、排程、成本：

```
job: id(job_), jobId, itemId→item, customerId→customer, locationId→location,
     status(enum jobStatus), dueDate, deadlineType(enum), quantity, scrapQuantity,
     quantityComplete, quantityShipped, quantityReceivedToInventory,
     salesOrderId→salesOrder, salesOrderLineId, quoteId→quote, quoteLineId,
     notes jsonb, configuration jsonb, priority, scheduled/completed 时间字段,
     companyId, createdAt/By, updatedAt/By, customFields jsonb, tags[]
```

**子表群**：
- `jobOperation`（50 列，119 行）：工序级。带 `order`(工序序)、`processId→process`、`workCenterId→workCenter`、`procedureId→procedure`、`inspectionDocumentId→inspectionDocument`、`setupTime/laborTime/machineTime`+对应 `factor` 枚举、`status`(jobOperationStatus)、`quantityComplete/Scrapped/Reworked`、`manuallyScheduled`/`hasConflict`(排程冲突标记)。
- `jobMaterial`（30 列）：工单物料需求（BOM 消耗）。`itemId→item`、`itemType`(Part/Raw)、`methodType`(enum Make to Order)、`jobOperationId→jobOperation`(可精确到工序)、`quantity`/`quantityIssued`。
- `jobOperationParameter`：工序参数。
- `productionEvent`（执行事件）/ `productionQuantity`（产量，含 `scrapReasonId→scrapReason`、`inspectionId→inspection`、`labor/machine/setupProductionEventId→productionEvent`）：把"做了多少、废了多少、为什么废"落到事件溯源式明细。

**路由/资源**：`procedure`(工艺规程, content json) + `procedureStep`(步骤, min/max/listValues 质检阈值) ↔ `process` ↔ `workCenter`(工作中心, laborRate/machineRate/overheadRate/batchCapacity, `requiredAbilityId→ability`)。

> 设计要点：生产域是**事件溯源 + 工序树**结构——`job → jobOperation[] → jobMaterial[]/jobOperationParameter[]`，产量与废料拆成 `productionEvent/productionQuantity` 不可变明细，而非在 job 上累加。排程冲突用 `hasConflict/conflictReason/scheduleOutdatedReason` 显式标记，符合 MES 甘特排程的实需。

---

## 2. 库存（INVENTORY）域

**枢纽表 `item`（27 列，37 行）**——物料主数据：

```
item: id(item), readableId, name, type(enum), replenishmentSystem(enum Buy/Make),
      defaultMethodType(enum methodType), itemTrackingType(enum), unitOfMeasureCode,
      sourcingType(enum Specified), mpn, revision/revisionStatus(enum), changeOrderId→changeOrder,
      modelUploadId(3D模型), thumbnailPath, notes jsonb, companyId, 审计四列, customFields
```

**计划/成本/补货** 拆成独立从表（避免主数据膨胀）：
- `itemCost`：`itemId→item` + `itemPostingGroupId→itemPostingGroup` + `costingMethod`(enum) + `standardCost`/`unitCost`。→ 与会计域 `postingGroup` 桥接。
- `itemPlanning`：补货策略全集——`reorderingPolicy`(enum)、`reorderPoint`/`reorderQuantity`/`minimumOrderQuantity`/`maximumOrderQuantity`/`orderMultiple`、`demandAccumulationPeriod`/`safetyStock`/`minimumReserveQuantity`。
- `itemReplenishment`：`preferredSupplierId→supplier`、`leadTime`、`conversionFactor`、`scrapPercentage`、`purchasingBlocked`/`manufacturingBlocked`。
- `itemPostingGroup`：库存过账组（连接会计）。
- `itemUnitSalePrice` / `itemStockQuantities`（库存量快照）/ `inventoryCount`+`inventoryCountLine`（盘点单头/行）。

> 设计要点：库存域把**主数据(item) / 计划(itemPlanning) / 成本(itemCost) / 补货(itemReplenishment) / 过账组(itemPostingGroup)** 纵向切分，每张从表以 `itemId` 关联。这是经典 MRP"物料主数据 + 计划参数 + 成本"三元组，且 `reorderingPolicy`/`costingMethod` 等用枚举固化业务规则。

---

## 3. 质量（QUALITY）域

- `qualityDocument`（13 列，3 行）：检验规范头。`id('qdoc')`、`version`、`status`(enum qualityDocumentStatus)、`content json`、`assignee`。
- `qualityDocumentStep`（17 列）：规范步骤。`type`(enum)、`minValue/maxValue/listValues`(判定阈值)、`required`、`sortOrder`、`fileTypes`(附件要求)。
- `inspectionDocument`（21 列）：图纸/检验文档。`partId→part`、`drawingNumber`、`version`、`samplingPlanType`/`samplingSampleSize`/`samplingPercentage`/`samplingAql`/`samplingInspectionLevel`(抽样方案，全套 AQL 字段)。
- `nonConformance`（25 列，5 行）：不合格品单（NCR）。`id('nc')`、`nonConformanceId`、`source`(enum)、`status`(enum nonConformanceStatus)、`nonConformanceWorkflowId`(审批流)、`nonConformanceTypeId`、`priority`(enum)、`locationId`、`quantity`、`content json`、`approvalRequirements[]`/`requiredActionIds[]`、`customFields jsonb`。
- `nonConformanceItem`（10 列）：NCR 关联物料。`nonConformanceId→nonConformance` + `itemId→item` + `disposition`(enum 处置: Pending/...)。
- `nonConformanceType` / `scrapReason`（8 列，`id('sr')`）：不合格类型与报废原因字典。

> 设计要点：质量域用 **`qualityDocument`(规范) + `inspectionDocument`(图纸抽样) + `nonConformance`(不合格单) + `scrapReason`(报废因)** 四角，且 `jobOperation.inspectionDocumentId` 与 `productionQuantity.scrapReasonId` 把质量直接挂到生产工序与产量上——质量不是独立模块，而是嵌入生产执行链。

---

## 4. 三域互联（ER 要点，证明"四合一"是真耦合）

```
                  salesOrder / quote
                        │ (job.salesOrderId / quoteId)
                        ▼
   ┌─────────────────── job (工单枢纽) ───────────────────┐
   │  job.itemId ──────► item (库存主数据, 37行)            │
   │  job.customerId ──► customer                          │
   │  job.locationId ──► location                           │
   └───────────────────────────────────────────────────────┘
        │ jobOperation[] (工序, 119行)        ▲ jobMaterial[].itemId ──► item
        ├─ jobOperation.workCenterId ──────► workCenter (MES 资源)
        ├─ jobOperation.processId ─────────► process   (路由)
        ├─ jobOperation.procedureId ───────► procedure  (质量工艺规程)
        ├─ jobOperation.inspectionDocumentId ► inspectionDocument (质量图纸)
        └─ productionQuantity[].scrapReasonId ─► scrapReason (质量报废因)
                                   productionQuantity[].inspectionId ─► inspection
   nonConformanceItem.itemId ──────────────► item  (不合格关联物料)
```

**一句话结论**：`job` 是四域的物理枢纽——向上接销售(`salesOrder/quote`)、向右接库存(`item`/`jobMaterial`)、向下接 MES(`workCenter`/`process`)、向内嵌质量(`procedure`/`inspectionDocument`/`scrapReason`)。一个工单同时是 ERP 单据、MES 排程单元、QMS 检验对象。这正是"四合一"不是四个库拼起来的证据。

---

## 5. 迁移组织纪律（1092 个文件怎么长出来的）

- **线性时间戳文件名**：`20230123003711_xid.sql` … `20261003142107_set-inngest-event-config.sql`。每个变更一个文件，按提交时刻排序，无"合并迁移/重置迁移"。
- **演进不重建**：新增列走 `ALTER TABLE ... ADD COLUMN`（如 `scheduleOutdatedReason`/`reworkId` 都是后期补的），不丢数据、不重建表。
- **schema-as-code 单源**：SQL 迁移同时生成 `packages/database/src/types.ts`（87,808 行 Supabase `Database` 类型）→ 再生成 oRPC operations（1483 个）与 MCP 工具面。改一处 schema，类型/接口/文档全链更新。
- **对照我们的 5 分支并行打法**：Carbon 用"单时间轴线性迁移"保证 schema 永远可向前滚；我们 `m1 + 4 worker` worktree 并行后需 `merge m1` 再让 worker 接新基线——两者都在解决"并行开发下 schema/基线不分裂"，只是 Carbon 靠时间轴、我们靠分支重基准。可互相借鉴：Carbon 的"迁移即契约"值得我们的 D-waves 清单参照。

---

## 6. 对 AOS / 栖月汇可借鉴点

1. **单 schema 多租户 + `companyId` 隔离**：栖月汇作为首个租户接入，可直接沿用"列级 companyId + RLS"，不必每租户独立库。
2. **`customFields jsonb` 逃逸舱**：租户定制字段不进迁移，降低我们"每接一个电商平台就加列"的迁移负担。
3. **枚举状态机替代软删**：订单/履约状态用枚举(`orderStatus`)而非 `deleted_at`，历史完整可追溯——契合电商订单全生命周期审计。
4. **审计四列 + 自定义前缀 ID**：`createdBy/createdAt/updatedBy/updatedAt` + 可读 ID（`order_`/`so_`），可直接照搬。
5. **事件溯源式产量/库存**：`productionQuantity`/`productionEvent` 的不可变明细思路，可映射为栖月汇"订单流水/履约事件"的设计范式。
6. **迁移即契约**：把 DDL 迁移当一等公民，驱动类型与接口生成，减少"文档漂移"（我们 tare 踩过的坑）。

> 注：第 1/6 项与 `709-…Carbon研究波次.md` 的"可借鉴点 a/d"同源，此处给出落地到表结构的证据。是否提炼为 AOS 设计库 ADR（原清单第 1 项），待大同决策。
