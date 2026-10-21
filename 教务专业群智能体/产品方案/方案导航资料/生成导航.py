#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成专业群 AI 工作站本地方案文档地图；不修改任何方案正文。"""
from pathlib import Path
import argparse, datetime, hashlib, json, re, sys, urllib.parse

E = Path(__file__).resolve().parent
PLAN = E.parent
ROOT = PLAN.parent
OUTPUT = PLAN / "专业群AI工作站方案文档地图.html"
TEMPLATE = E / "导航模板.html"
REGISTRY = E / "稳定节点ID.json"
DATA = E / "文档图谱数据.json"
LEDGER = E / "来源阅读与分类台账.jsonl"
REPORT = E / "导航核查记录.json"

GROUPS = [
    ("business", "业务依据与校方沟通", "学校原始信息、需求确认、沟通口径和功能范围", "#db7355"),
    ("product", "核心产品设计", "产品总方案、智能体、知识库、工作台及详细设计", "#2d74bf"),
    ("assurance", "设计校核与追踪", "一致性、字段差异、跨页面流程和多专业样例", "#6d59a8"),
    ("review", "当前方案评审稿", "本轮技术评审、追踪、试点、学校准备和会议入口", "#159b7d"),
    ("prototype", "视觉原型与页面验证", "信息架构、页面办理、角色视角和原型验证", "#cb8a2c"),
    ("techdraft", "首版技术初稿", "编码前形成但未经正式评审的技术思路", "#587f9b"),
    ("history", "历史实现与验证材料", "编码后形成的实现、验证、候选版和试点准备记录", "#8a8f9e"),
    ("support", "项目辅助资料", "资料索引、选型和早期探索材料", "#9b6b7b"),
]

SUBNAMES = {
    "raw": "面谈原始材料与整理",
    "school": "需求确认与校方沟通",
    "scope": "功能范围与字段",
    "overview": "总体方案与建设路线",
    "special": "智能体、知识库与工作台",
    "detail": "核心对象与办理流程",
    "check": "一致性与字段校核",
    "journey": "T01—T18 跨页面流程",
    "review-main": "评审总入口",
    "review-domain": "技术分方案",
    "review-trace": "追踪、会议与未决事项",
    "review-pilot": "学校准备、试点与视觉输入",
    "prototype-doc": "视觉设计说明",
    "prototype-test": "页面与角色验证",
    "tech": "首版技术设计",
    "tech-gate": "开发波次与编码门槛",
    "w9-base": "W9 基础、身份与文件底座",
    "w9-knowledge": "W9 建设依据与知识库",
    "w9-work": "W9 任务、指标与智能体",
    "w9-result": "W9 查询、成果与实践",
    "w9-pilot": "W9/W10 候选版与试点",
    "w9-workbench": "W9-9 正式工作台收口",
    "index": "项目资料索引",
    "explore": "工具选型与早期探索",
}

CURRENT_REVIEW = set(range(122, 139))
PROTOTYPE = set(range(27, 38))
TECH_DRAFT = set(range(38, 45))
HISTORY = set(range(45, 122))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def title_of(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem

def number_of(path: Path):
    if path.parent != PLAN:
        return None
    m = re.match(r"^(\d+)-", path.name)
    return int(m.group(1)) if m else None

def classify(path: Path):
    rel = path.relative_to(ROOT).as_posix()
    n = number_of(path)
    if path.parent == ROOT:
        if path.name in {"09-16 校企共建AI工作站及专业群建设.md", "会议原始资料.md", "方案梳理.md"}:
            return "business", "raw", "业务依据", "原始信息或早期整理材料"
        if path.name in {"专业群AI工作站需求确认单.md", "专业群AI工作站校方沟通展示稿.md", "专业群AI工作站校方沟通展示稿-结构调整方案.md"}:
            return "business", "school", "业务依据", "需求确认或校方沟通材料"
        if path.name == "专业群AI工作站功能清单与字段设计.md":
            return "business", "scope", "业务依据", "功能范围与字段整理"
        if path.name == "项目资料与交付物索引.md":
            return "support", "index", "辅助资料", "已有项目资料索引"
        return "support", "explore", "辅助资料", "工具选型或早期探索"
    if path.parent.name == "demo":
        return "prototype", "prototype-doc", "原型反馈", "视觉稿设计或核查说明"
    if n is None:
        return "support", "index", "辅助资料", "未编号资料"
    if n <= 12:
        sub = "overview" if n in {0, 1, 9, 10, 11, 12} else "special"
        return "product", sub, "产品设计", "核心产品方案；已编制、待评审、未冻结"
    if n <= 18:
        return "product", "detail", "产品设计", "核心对象、状态、智能体或跨页面办理详细设计"
    if n <= 26:
        sub = "journey" if n in {21, 22, 25} else "check"
        return "assurance", sub, "校核材料", "用于发现遗漏与冲突，不单独决定范围"
    if n in PROTOTYPE:
        return "prototype", "prototype-test", "原型反馈", "页面与角色验证，不等于需求或验收通过"
    if n in TECH_DRAFT:
        sub = "tech-gate" if n in {43, 44} else "tech"
        return "techdraft", sub, "历史技术稿", "编码前技术初稿，供当前评审参考"
    if n in HISTORY:
        if n <= 53: sub = "w9-base"
        elif n <= 59: sub = "w9-knowledge"
        elif n <= 70: sub = "w9-work"
        elif n <= 87: sub = "w9-result"
        elif n <= 96: sub = "w9-pilot"
        else: sub = "w9-workbench"
        return "history", sub, "实现参考", "编码后形成，只说明历史实现或验证事实"
    if n in CURRENT_REVIEW:
        if n in {122, 128, 138}: sub = "review-main"
        elif n in {123, 124, 125, 126, 129, 130}: sub = "review-domain"
        elif n in {127, 131, 132, 133, 134}: sub = "review-trace"
        else: sub = "review-pilot"
        return "review", sub, "当前评审稿", "已完成本轮编制、等待评审、未冻结"
    return "support", "index", "辅助资料", "未归入现行评审主线"

def source_paths():
    paths = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("产品方案/方案导航资料/"):
            continue
        if rel.startswith("demo/node_modules/"):
            continue
        if path.name == "AGENTS.md":
            continue
        paths.append(path)
    return sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix())

def first_summary(text: str) -> str:
    lines = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        s = line.strip()
        if in_code or not s or s.startswith(("#", ">", "|", "- [")):
            continue
        s = re.sub(r"[*_`]", "", s)
        lines.append(s)
        if sum(map(len, lines)) > 260:
            break
    return " ".join(lines)[:280]

def build():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {}
    next_id = max([int(v.split("-")[-1]) for v in registry.values() if re.fullmatch(r"PGDOC-\d+", v)] or [0]) + 1
    nodes, ledger = [], []
    for path in source_paths():
        rel = path.relative_to(ROOT).as_posix()
        if rel not in registry:
            registry[rel] = f"PGDOC-{next_id:04d}"
            next_id += 1
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        title = title_of(path, text)
        group, sub, role, reason = classify(path)
        headings = [re.sub(r"^#{1,4}\s+", "", x).strip() for x in text.splitlines() if re.match(r"^#{1,4}\s+", x)][:100]
        summary = first_summary(text)
        n = number_of(path)
        current = group == "review"
        node = {
            "id": registry[rel], "path": rel, "title": title, "group": group, "sub": sub,
            "tags": [role, SUBNAMES[sub]], "reason": reason, "headings": headings,
            "summary": summary, "body": summary + "\n" + "\n".join(headings), "truncated": False,
            "reference": False, "current": current, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "role": role, "number": n,
            "status": "已完成本轮编制、待评审" if group == "review" else reason,
            "assets": []
        }
        nodes.append(node)
        ledger.append({"id": node["id"], "path": rel, "title": title, "group": group, "sub": sub,
                       "role": role, "classification_basis": reason, "sha256": node["sha256"],
                       "reading_scope": "读取标题、章节和开头摘要用于导航分类；正文仍以原文件为准"})
    by_path = {n["path"]: n for n in nodes}
    by_name = {Path(n["path"]).name: n for n in nodes}
    edges = {}

    def add(src_name, dst_name, kind, evidence):
        src, dst = by_name.get(src_name), by_name.get(dst_name)
        if not src or not dst or src["id"] == dst["id"]:
            return
        key = (src["id"], dst["id"], kind)
        edges[key] = {"id": "PGREL-" + hashlib.sha256("|".join(key).encode()).hexdigest()[:12],
                      "source": src["id"], "target": dst["id"], "kind": kind, "evidence": evidence}

    # Markdown 显式链接。
    link_rx = re.compile(r"\[[^\]]*\]\((<[^>]+>|[^)]+)\)")
    for node in nodes:
        path = ROOT / node["path"]
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw_target in link_rx.findall(text):
            target = urllib.parse.unquote(raw_target.strip("<> ").split("#", 1)[0].split("?", 1)[0])
            if not target or re.match(r"^[a-zA-Z]+:", target):
                continue
            resolved = (path.parent / target).resolve()
            if resolved.is_relative_to(ROOT):
                rel = resolved.relative_to(ROOT).as_posix()
                if rel in by_path:
                    dst = by_path[rel]
                    key = (node["id"], dst["id"], "正文引用")
                    edges[key] = {"id": "PGREL-" + hashlib.sha256("|".join(key).encode()).hexdigest()[:12],
                                  "source": node["id"], "target": dst["id"], "kind": "正文引用", "evidence": "Markdown 显式链接"}

    # 业务依据到产品总方案。
    total = "01-专业群AI工作站产品总方案.md"
    for name in ["09-16 校企共建AI工作站及专业群建设.md", "专业群AI工作站需求确认单.md",
                 "专业群AI工作站校方沟通展示稿.md", "专业群AI工作站功能清单与字段设计.md"]:
        add(name, total, "业务依据支撑", "来源分层索引与产品总方案")
    # 产品总方案的专项分解。
    for i in range(2, 19):
        target = next((n["path"] for n in nodes if n.get("number") == i and n["path"].startswith("产品方案/")), None)
        if target:
            add(total, Path(target).name, "产品方案分解", "00 导航与 01 产品总方案")
    # 当前技术承载关系。
    mapping = {
        2: 124, 3: 125, 4: 123, 5: 123, 6: 123, 7: 123, 8: 126, 9: 135,
        10: 137, 11: 132, 13: 129, 14: 129, 15: 124, 16: 125, 17: 132,
        21: 132, 22: 132, 25: 132,
    }
    num_name = {n["number"]: Path(n["path"]).name for n in nodes if n.get("number") is not None and n["path"].startswith("产品方案/")}
    for src_n, dst_n in mapping.items():
        if src_n in num_name and dst_n in num_name:
            add(num_name[src_n], num_name[dst_n], "技术承载" if dst_n not in {132, 135, 137} else "验收追踪", "当前评审稿映射")
    for dst_n in [123, 124, 125, 126, 129, 130, 135]:
        add(num_name[122], num_name[dst_n], "技术方案分解", "122 技术方案评审总稿")
    for dst_n in [122, 127, 132, 133, 128]:
        add(num_name[138], num_name[dst_n], "评审入口", "138 评审交付顺序")
    add(num_name[133], num_name[127], "评审入口", "评审会议记录未决事项")
    add(num_name[133], num_name[132], "评审入口", "评审会议核对追踪矩阵")

    # 历史材料仅作为当前方案参考，按标题主题连接，不表示现行设计继承。
    for node in nodes:
        if node["group"] not in {"prototype", "techdraft", "history"}:
            continue
        title = node["title"]
        if re.search(r"智能体|Agent|动作网关", title, re.I): dst = 124
        elif re.search(r"知识|依据|资料吸收|检索|关系追溯", title): dst = 125
        elif re.search(r"权限|身份|隔离|数据主权|多专业群", title): dst = 126
        elif re.search(r"对象|版本|账本|数据模型", title): dst = 129
        elif re.search(r"接口|失败|恢复|后台|性能|安全|可用", title): dst = 130
        elif re.search(r"试点|验收|候选版", title): dst = 135
        else: dst = 123
        if dst in num_name:
            add(Path(node["path"]).name, num_name[dst], "历史参考", "按材料主题连接当前评审分方案")

    group_counts = {g[0]: sum(n["group"] == g[0] for n in nodes) for g in GROUPS}
    payload = {
        "revision": "评审资料截点 2026-10-21", "phase": "方案已编制，待评审，未冻结",
        "model": "未授权继续编码", "root_label": "专业群 AI 工作站方案",
        "groups": [{"id": a, "label": b, "description": c, "color": d} for a, b, c, d in GROUPS],
        "subnames": SUBNAMES, "nodes": nodes, "edges": list(edges.values()),
        "shortcuts": {"start": by_name[num_name[138]]["id"], "status": by_name[num_name[122]]["id"]},
        "stats": {"documents": len(nodes), "product_design": group_counts["product"],
                  "current_review": group_counts["review"], "historical": group_counts["history"],
                  "relations": len(edges), "source_bytes": sum(n["bytes"] for n in nodes)},
    }
    payload["source_fingerprint"] = hashlib.sha256(json.dumps(
        [(n["path"], n["sha256"], n["group"], n["sub"]) for n in nodes], ensure_ascii=False
    ).encode()).hexdigest()
    return payload, registry, ledger

def check():
    if not all(p.exists() for p in [OUTPUT, DATA, REPORT, REGISTRY]):
        print(json.dumps({"ok": False, "error": "导航产物缺失"}, ensure_ascii=False))
        return 1
    current, _, _ = build()
    saved = json.loads(DATA.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    ids = {n["id"] for n in saved["nodes"]}
    checks = {
        "source_fingerprint": current["source_fingerprint"] == saved["source_fingerprint"],
        "coverage_paths": {n["path"] for n in current["nodes"]} == {n["path"] for n in saved["nodes"]},
        "unique_primary_membership": len({n["path"] for n in saved["nodes"]}) == len(saved["nodes"]),
        "unique_stable_ids": len(ids) == len(saved["nodes"]),
        "edge_endpoints": all(e["source"] in ids and e["target"] in ids for e in saved["edges"]),
        "source_links_exist": all((ROOT / n["path"]).exists() for n in saved["nodes"]),
        "html_fingerprint": sha(OUTPUT) == report.get("html_sha256"),
    }
    print(json.dumps({"ok": all(checks.values()), "checks": checks, "stats": saved["stats"]}, ensure_ascii=False))
    return 0 if all(checks.values()) else 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    payload, registry, ledger = build()
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count("__PG_DATA__") != 1:
        raise RuntimeError("导航模板的数据占位符数量不为 1")
    html = template.replace("__PG_DATA__", encoded)
    OUTPUT.write_text(html, encoding="utf-8")
    dump(REGISTRY, registry)
    dump(DATA, payload)
    with LEDGER.open("w", encoding="utf-8") as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
        "phase": payload["phase"], "stats": payload["stats"],
        "source_fingerprint": payload["source_fingerprint"], "html_sha256": sha(OUTPUT),
        "document_tree_primary_memberships": len(payload["nodes"]),
        "all_target_markdown_included": True, "legacy_sources_modified": False,
        "classification": "依据 128 来源分层索引和 138 评审交付顺序人工编排；编号不自动视为父子关系",
        "visual_review": "pending"
    }
    dump(REPORT, report)
    print(json.dumps({"ok": True, "output": str(OUTPUT), "stats": payload["stats"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
