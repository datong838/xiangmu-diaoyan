#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_review_pack.py —— 生成「多方复核包」（交给外部大模型 / 多专家）

设计要点（见 03_依据核准与多方复核_技术方案.md §七）：
  1. 一判据一卡（YAML）；引用文件须一起分发，路径以判据库根目录为基准
  2. 本轮带audit意见是协同复核；真正盲审须剥离audit与管理侧答案
  3. 必给证据：复核者须填 verdict + reason + evidence + suggested_fix
  4. 可靠性探针：掺入已知答案的种子项（一正一误），防敷衍
  5. ★ 卡片一律用 yaml.safe_dump 生成，并在写盘后**回读校验**（非法 YAML 直接失败）

三类卡：
  A. 明文判据卡（basis: standard）  —— 附国标条款 + 逐字引文 + 机器校验
  B. 经验规则卡（basis: convention）—— 附 grounding + counterexample + 案例图纸
  C. 可靠性探针（_probe_*）          —— 已知答案的种子项

用法：
  python tools/build_review_pack.py [--no-probes] [--no-convention]
"""
import argparse, json, os, sys, glob
import yaml

# 明文判据卡头部注释
STD_HEAD = """# 复核卡 {id}（自包含，无需我方上下文）
#   ★ 本类核查的是「引文是否真在声称页上、条款是否适用」——有原文可锚，可机器验。
"""

# 经验规则卡头部注释
CONV_HEAD = "# 经验规则候选：尚待客户专家核准，不能声称所有国标无明文。\n"
NEG_HEAD = "# 限定范围检索审计：零命中不证明不存在，命中须核准语义。\n"
PROBE_NOTE = "# 引文位置核查项，请按普通卡独立核对。\n"

REVIEWER_TEMPLATE = {
    "verdict": "",            # 通过 / 存疑 / 否决 / 无法判定
    "reason": "",             # 须能指向图、条文、教材或工程实例
    "evidence": "",
    "suggested_fix": "",
    "independent_first": "",
}

# 标准号 → (完整标准号, 标准名称)；卡片里必须给全称，复核者才知道引的是哪份标准
STD_NAMES = {
    "1800.1": ("GB/T 1800.1-2020", "产品几何技术规范（GPS） 线性尺寸公差ISO代号体系 第1部分：公差、偏差和配合的基础"),
    "4457.4": ("GB/T 4457.4-2002", "机械制图 图样画法 图线"),
    "4457.5": ("GB/T 4457.5-2013", "机械制图 剖面区域的表示法"),
    "4458.1": ("GB/T 4458.1-2002", "机械制图 图样画法 视图"),
    "4458.4": ("GB/T 4458.4-2003", "机械制图 尺寸注法"),
    "4458.5": ("GB/T 4458.5-2003", "机械制图 尺寸公差与配合注法"),
    "4458.6": ("GB/T 4458.6-2002", "机械制图 图样画法 剖视图和断面图"),
    "4459.1": ("GB/T 4459.1-1995", "机械制图 螺纹及螺纹紧固件表示法"),
    "4459.3": ("GB/T 4459.3-2000", "机械制图 花键表示法"),
}


def parse_clause(c):
    """'4458.4 §5.2' / '4457.4 表1 01.1.21' → (标准号全称, 名称, 条款)"""
    parts = (c or "").split(None, 1)
    key = parts[0] if parts else ""
    rest = parts[1] if len(parts) > 1 else ""
    std, title = STD_NAMES.get(key, ("GB/T " + key, ""))
    return std, title, rest



class LiteralStr(str):
    """多行文本强制以块标量 | 输出，避免被折叠成难读的单引号串"""
    pass


def _lit_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


yaml.SafeDumper.add_representer(LiteralStr, _lit_representer)


def L(v):
    """含换行的字符串 → 块标量；其余原样"""
    return LiteralStr(v) if isinstance(v, str) and "\n" in v else v


def dump(obj):
    return yaml.safe_dump(obj, allow_unicode=True, default_flow_style=False,
                          sort_keys=False, width=10000)


def write_card(path, head, obj):
    """写盘 + 回读校验（非法 YAML 立即失败，不产出坏卡）"""
    txt = head + dump(obj)
    open(path, "w", encoding="utf-8").write(txt)
    back = yaml.safe_load(open(path, encoding="utf-8"))   # ← 自检：必须能读回
    assert isinstance(back, dict) and back.get("id") == obj["id"], "卡片回读校验失败: %s" % path
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default="evidence/batch.json")
    ap.add_argument("--report", default="evidence/cards/verify_report.json")
    ap.add_argument("--claims", default="review/claims.json")
    ap.add_argument("--convention", default="criteria/convention",
                    help="经验判据目录；传空串跳过")
    ap.add_argument("--cases", default="../工程图审核",
                    help="案例图纸目录（相对 评分判据库/）")
    ap.add_argument("--std-dir", default="../国标",
                    help="国标 PDF 目录（相对 评分判据库/），供否证审计卡渲染被否证标准的页面")
    ap.add_argument("--out", default="review/pack_v1")
    ap.add_argument("--probes", type=int, default=1)
    a = ap.parse_args()

    base = os.path.dirname(os.path.dirname(os.path.abspath(a.batch)))  # 评分判据库/
    a.std_dir = a.std_dir if os.path.isabs(a.std_dir) else os.path.normpath(os.path.join(base, a.std_dir))
    def rd(p):
        fp = p if os.path.isabs(p) else os.path.join(base, p)
        return json.load(open(fp, encoding="utf-8"))

    batch = rd(a.batch)
    report = {r["id"]: r for r in rd(a.report)}
    claims = rd(a.claims)
    outdir = os.path.join(base, a.out)
    os.makedirs(outdir, exist_ok=True)

    written, missing_claims = [], []
    # 删除有答案提示的旧探针卡，防止混入当前复核包。
    for old in glob.glob(os.path.join(outdir, "_probe*.yaml")):
        os.remove(old)

    # ── A. 明文判据卡 ────────────────────────────────────────────
    for it in batch:
        cid = it["id"]
        meta = claims.get(cid, {})
        if not meta.get("claim"):
            missing_claims.append(cid)
            print("  [警告] %s 在 claims.json 中缺 claim —— 请补齐" % cid)
        rep = report.get(cid, {})
        status = rep.get("status", "UNKNOWN")
        st = {"OK": "OK（已精确定位）",
              "OK_FUZZY": "OK_FUZZY（命中但有 OCR 字符差异，须目视确认）",
              "FAIL_PAGE": "FAIL_PAGE（页码存疑）",
              "FAIL": "FAIL（未命中）"}.get(status, status)
        page = it.get("page")
        std, title, clause = parse_clause(it.get("clause", ""))
        ev = [
            {"type": "原页图(E0)", "file": "evidence/cards/%s/page_%s.png" % (cid, page)},
            {"type": "条款裁图(E1)", "file": "evidence/cards/%s/clause_crop.png" % cid},
            {"type": "红框整页", "file": "evidence/cards/%s/page_highlight.png" % cid},
            {"type": it.get("quote_kind", "引文（逐字）"), "text": it.get("quote", "")},
            {"type": "条款", "std": std, "title": title, "clause": clause, "pdf_page": page},
            {"type": "机器校验", "status": st},
        ]
        if status == "OK_FUZZY":
            ev[-1]["ocr_read"] = rep.get("ocr_read", "")
        # 不引用已撤销的旧定位图；当前直接提供完整相关页。
        ev = [e for e in ev if e["type"] not in ("条款裁图(E1)", "红框整页", "原页图(E0)")]
        qs = meta.get("question", "1) 裁图条文是否支持该命题？\n2) 条款适用是否贴切？\n3) 有无反例？")
        card = {
            "audit": meta.get("audit", {}),
            "path_base": "评分判据库根目录",
            "id": cid,
            "claim": L(meta.get("claim", "（待补）")),
            "basis_type": meta.get("basis_type", "standard_candidate"),
            "evidence": ev,
            "my_conclusion": "hypothesis",
            "question_for_reviewer": L(qs),
            "reviewer_output": dict(REVIEWER_TEMPLATE),
        }
        import fitz
        with fitz.open(it["pdf"]) as doc:
            for page_no in it.get("context_pages", [page]):
                rel = "evidence/cards/%s/context_%s.png" % (cid, page_no)
                os.makedirs(os.path.dirname(os.path.join(base, rel)), exist_ok=True)
                doc[page_no - 1].get_pixmap(dpi=180).save(os.path.join(base, rel))
                card["evidence"].append({"type": "完整上下文原页", "file": rel, "pdf_page": page_no})
        tid = cid.split("-")[0]
        for kind in ("正确", "错误"):
            matches = glob.glob(os.path.join(base, a.cases, tid + "_*-" + kind + "图纸.pdf"))
            if matches:
                card["evidence"].append({"type": "客户" + kind + "图", "file": os.path.relpath(matches[0], base)})
        card["evidence"].append({"type": "原始标准全文", "file": os.path.relpath(it["pdf"], base)})
        write_card(os.path.join(outdir, cid + ".yaml"), STD_HEAD.format(id=cid), card)
        written.append(cid + ".yaml")

    # ── C. 可靠性探针（一正一误）──────────────────────────────────
    if a.probes:
        import fitz
        pdf = next((it["pdf"] for it in batch if it["id"] == "T05-1"), None)
        pdir = os.path.join(outdir, "_probe")
        os.makedirs(pdir, exist_ok=True)
        if pdf and os.path.exists(pdf):
            d = fitz.open(pdf)
            for pno in (3, 11):
                if 1 <= pno <= len(d):
                    d[pno - 1].get_pixmap(dpi=180).save(os.path.join(pdir, "page_%d.png" % pno))
            d.close()
        rel = (a.out + "/_probe").replace(os.sep, "/")

        pos = {
            "id": "R01",
            "claim": "「标注直径时，应在尺寸数字前加注符号 Φ」位于 GB/T 4458.4-2003 §5.2（PDF p11）",
            "basis_type": "standard",
            "evidence": [
                {"type": "原页图(E0)", "file": rel + "/page_11.png"},
                
                {"type": "引文（逐字）", "text": "标注直径时，应在尺寸数字前加注符号 Φ"},
                {"type": "条款", "std": "GB/T 4458.4-2003", "title": "机械制图 尺寸注法",
                 "clause": "5.2", "pdf_page": 11},
            ],
            "my_conclusion": "hypothesis",
            "question_for_reviewer": L("核对该句是否位于声称的条款与页码；给出原页证据。"),
            "reviewer_output": dict(REVIEWER_TEMPLATE),
        }
        write_card(os.path.join(outdir, "R01.yaml"), PROBE_NOTE, pos)
        written.append("R01.yaml")

        neg = {
            "id": "R02",
            "claim": "「标注直径时，应在尺寸数字前加注符号 Φ」位于 GB/T 4458.4-2003 §5.2（PDF p3）",
            "basis_type": "standard",
            "evidence": [
                {"type": "声称页(E0)", "file": rel + "/page_3.png"},
                {"type": "引文（逐字）", "text": "标注直径时，应在尺寸数字前加注符号 Φ"},
                {"type": "条款", "std": "GB/T 4458.4-2003", "title": "机械制图 尺寸注法",
                 "clause": "5.2", "pdf_page": 3},
            ],
            "my_conclusion": "hypothesis",
            "question_for_reviewer": L("核对该句是否位于声称的条款与页码；给出原页证据。"),
            "reviewer_output": dict(REVIEWER_TEMPLATE),
        }
        write_card(os.path.join(outdir, "R02.yaml"), PROBE_NOTE, neg)
        written.append("R02.yaml")

    # ── B. 经验规则卡（basis: convention）─────────────────────────
    conv_ids = []
    neg_ids = []
    if a.convention:
        import fitz
        cdir = os.path.join(base, a.convention)
        if os.path.isdir(cdir):
            case_dir = os.path.join(outdir, "_cases")
            os.makedirs(case_dir, exist_ok=True)
            cand_root = os.path.normpath(os.path.join(base, a.cases))
            audit_dir = os.path.join(outdir, "_audit")
            os.makedirs(audit_dir, exist_ok=True)

            def render_audit_page(std_key, page_no):
                """把被否证标准的指定页渲染进包内 _audit/，供复核者目视核对"""
                if not std_key:
                    return None
                code = std_key.split("-")[0].replace("GB/T ", "").strip()
                pats = [f for f in glob.glob(os.path.join(base, a.std_dir, "*.pdf")) if code in f]
                if not pats:
                    return None
                try:
                    d = fitz.open(pats[0])
                    if not (1 <= page_no <= d.page_count):
                        d.close()
                        return None
                    rel = "_audit/%s_p%d.png" % (code, page_no)
                    fp = os.path.join(outdir, rel)
                    if not os.path.exists(fp):
                        d[page_no - 1].get_pixmap(dpi=170).save(fp)
                    d.close()
                    return rel.replace(os.sep, "/")
                except Exception:
                    return None

            def render_case(sample):
                """把该案例对应的『错误图纸』首页渲染为 png，返回相对包路径"""
                tid = sample.split("-")[0]
                pats = glob.glob(os.path.join(cand_root, tid + "_*-错误图纸.pdf"))
                if not pats:
                    return None
                rel = "_cases/%s_error.png" % tid
                fp = os.path.join(outdir, rel)
                if not os.path.exists(fp):
                    d = fitz.open(pats[0])
                    d[0].get_pixmap(dpi=170).save(fp)
                    d.close()
                return rel.replace(os.sep, "/")

            for fn in sorted(os.listdir(cdir)):
                if not fn.endswith(".yaml"):
                    continue
                data = yaml.safe_load(open(os.path.join(cdir, fn), encoding="utf-8"))
                rid = data.get("id", fn[:-5])
                cid = "C-" + rid
                samples = data.get("covers_samples", []) or []
                cases = []
                for sample_id in samples:
                    rel = render_case(sample_id)
                    if rel:
                        cases.append({"sample": sample_id, "file": (a.out + "/" + rel).replace(os.sep, "/"),
                                      "note": "客户纠错标签；适用性待逐项核准"})
                card = {
                    "id": cid,
                    "path_base": "评分判据库根目录",
                    "approval_status": data.get("approval_status", "candidate_pending_customer_expert"),
                    "basis_type": data.get("basis", "convention"),
                    "rule_name": data.get("name", ""),
                    "layer": data.get("layer", ""),
                    "severity": data.get("severity", ""),
                    "covers_samples": samples,
                    "claim": L(data.get("claim", "")),
                    "grounding": data.get("grounding", []),
                    "rationale": L(data.get("rationale", "")),
                    "counterexample": L(data.get("counterexample", "")),
                    "fp_risk": L(data.get("fp_risk", "")),
                    "standard_support": data.get("standard_support", []) or "（本条无反例明文支撑）",
                    "case_evidence": cases or "（案例图纸缺失）",
                    "executable_rule": {
                        "input": data.get("input", []),
                        "logic": L(data.get("logic", "")),
                        "outputs": data.get("outputs", []),
                        "detector_hint": L(data.get("detector_hint", "")),
                    },
                    "ocr_dependency": data.get("ocr_dependency", {}),
                    "negative_evidence_summary": {
                        "result": (data.get("negative_evidence", {}) or {}).get("result", ""),
                        "detail": L((data.get("negative_evidence", {}) or {}).get("detail", "")),
                        "audit_card": "N-" + rid,
                    },
                    "my_conclusion": "hypothesis",
                    "question_for_reviewer": L(data.get(
                        "question_for_reviewer",
                        "1) 该规则是否确为工程/教学共识？\n2) 反例清单是否完备？\n3) 出处是否恰当？")),
                    "reviewer_output": dict(REVIEWER_TEMPLATE),
                }
                for tid in sorted({x.split("-")[0] for x in samples}):
                    for kind in ("正确", "错误"):
                        for fp in glob.glob(os.path.join(cand_root, tid + "_*-" + kind + "图纸.pdf")):
                            card["case_evidence"].append({"type": "客户" + kind + "图", "file": os.path.relpath(fp, base)})
                write_card(os.path.join(outdir, cid + ".yaml"), CONV_HEAD, card)
                conv_ids.append(cid)
                written.append(cid + ".yaml")

                # ── D. 否证审计卡（每条 convention 一张）────────────────
                ne = data.get("negative_evidence", {}) or {}
                dep = data.get("ocr_dependency", {}) or {}
                aud_imgs = []
                for page_no in (data.get("audit_pages") or []):
                    rel = render_audit_page(dep.get("negated_standard", ""), page_no)
                    if rel:
                        aud_imgs.append({"page": page_no, "file": (a.out + "/" + rel).replace(os.sep, "/")})
                neg_card = {
                    "id": "N-" + rid,
                    "basis_type": "negative_evidence_audit",
                    "target_rule": cid,
                    "claim_under_audit": L(
                        "限定范围 %s 内是否存在直接支持该命题的条文；未检出不是无明文证明。" %
                        dep.get("negate_scope", dep.get("negated_standard", "范围待核准"))),
                    "negate_result_claimed": ne.get("result", ""),
                    "channel_state": {
                        "channel_A_文本层": dep.get("channel_A", ""),
                        "channel_B_OCR": dep.get("channel_B", ""),
                        "channel_C_目视": dep.get("channel_C", ""),
                        "negate_strength": dep.get("negate_strength", ""),
                    },
                    "search_word_family": dep.get("search_words", []) or
                        "（见 evidence/negative_spec.json）",
                    "residual_risk": L(dep.get("residual_risk", "")),
                    "audit_page_images": aud_imgs or "（未附页图）",
                    "how_to_review": L(
                        "1) 用你自己的标准原文（或权威来源）检索卡内给出的词族；\n"
                        "2) 若检出**实质明文**，判「否决」，并在 suggested_fix 写出标准号+条款+原文；\n"
                        "3) 零命中仅记录限定范围未检出，资料不足判存疑；\n"
                        "4) 可独立目视同一原始PDF；需说明读取范围，不假称独立权威来源。"),
                    "my_conclusion": "hypothesis",
                    "question_for_reviewer": L(ne.get(
                        "question_for_reviewer",
                        "1) 该否定结论是否成立？\n2) 检索词族是否有遗漏（尤其是同义不同词的表述）？\n"
                        "3) 该标准的文本通道是否可靠？")),
                    "reviewer_output": dict(REVIEWER_TEMPLATE),
                }
                write_card(os.path.join(outdir, "N-" + rid + ".yaml"), NEG_HEAD.format(id="N-" + rid), neg_card)
                neg_ids.append("N-" + rid)
                written.append("N-" + rid + ".yaml")

    for card in rd("review/pending_claims.json"):
        write_card(os.path.join(outdir, card["id"] + ".yaml"), "# 补充依据及适用性核准项\n", card)
        written.append(card["id"] + ".yaml")

    # ── 回填模板 ─────────────────────────────────────────────────
    os.makedirs(os.path.join(base, "review/responses"), exist_ok=True)
    open(os.path.join(base, "review/responses/_template.yaml"), "w", encoding="utf-8").write(
        "# 复核结果回填模板：每条判据一段，放 review/responses/<复核者>.yaml\n"
        + dump({"reviewer": "<你的名称/模型名>", "date": "<YYYY-MM-DD>",
                "items": [{"id": "T05-1", "verdict": "", "reason": "",
                           "evidence": "", "suggested_fix": ""}]}))

    # ── MANIFEST ─────────────────────────────────────────────────
    std_cards = [w for w in written
                 if not w.startswith("C-") and not w.startswith("R") and not w.startswith("W-") and not w.startswith("N-")]
    conv_cards = [c + ".yaml" for c in conv_ids]
    neg_cards = [c + ".yaml" for c in neg_ids]
    probes = [w for w in written if w.startswith("R")]
    # 管理侧探针答案不得进入公开包；已阅读答案的复核者不算盲测。
    manager = os.path.join(base, "review/manager")
    os.makedirs(manager, exist_ok=True)
    with open(os.path.join(manager, "probe_key.json"), "w", encoding="utf-8") as fh:
        json.dump({"R01": {"verdict": "通过", "page": 11}, "R02": {"verdict": "否决", "correct_page": 11},
                   "distribution": "管理侧文件，不分发给盲测复核方；本轮审查者已读旧答案，不算盲测"}, fh, ensure_ascii=False, indent=2)
    lines = ["# 复核包清单", "", "路径基准统一为评分判据库根目录；分发应包含原标准、客户图和evidence，单独复制pack_v1不自包含。", "",
             "引文机器匹配不等于条款支持与案例适用。audit字段为本次源资料审查记录，非专家共识。", "",
             "20张条款候选卡、4张经验规则候选卡、4张限定范围检索卡、5张补充依据及适用性核查卡、2张引文位置核查卡，共35张。", ""]
    lines += ["- " + w for w in written]
    lines += ["", "专家复核须记录通过/存疑/否决/无法判定、理由、证据、修正建议。管理侧review/manager不得随包分发。",
              "是否入库取决于原文支持、范围和专家核准，不以多数模型同意替代原页证据。"]
    with open(os.path.join(outdir, "MANIFEST.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("生成复核卡 %d 张 -> %s" % (len(written), outdir))
    print("  明文 %d / 经验规则 %d / 探针 %d" % (len(std_cards), len(conv_cards), len(probes)))
    if missing_claims:
        print("!! 有 %d 条缺 claim（见上）—— 请补 review/claims.json 后重跑" % len(missing_claims))
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
