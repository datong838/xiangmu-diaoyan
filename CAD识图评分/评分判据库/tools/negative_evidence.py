#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
限定资料与关键词检索器：命中仅为候选，零命中不证明不存在条款。
缺资料或OCR不记作零命中；通道来源相同不能声称独立验证。
GB/T4458.4 §5.7仅是半径派生表达，不能直接推导普遍禁止闭合链。
"""
import argparse, json, os, re, unicodedata
import fitz  # pymupdf


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", "", s)


def cjk_ratio(s: str) -> float:
    if not s:
        return 0.0
    return len(re.findall(r"[\u4e00-\u9fff]", s)) / len(s)


def channel_a(pdf_path: str):
    """通道 A：PDF 文本层全文（若为乱码则返回 None）"""
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return None, 0.0
    txt = "".join(p.get_text("text") for p in doc)
    doc.close()
    n = norm(txt)
    if cjk_ratio(n) < 0.15:
        return None, cjk_ratio(n)   # 假文本层，不可用
    return n, cjk_ratio(n)


def channel_b(ocr_dir: str, pdf_name: str):
    """通道 B：已产出的 OCR 文本"""
    base = os.path.splitext(pdf_name)[0]
    if not os.path.isdir(ocr_dir):
        return ""
    for f in os.listdir(ocr_dir):
        if os.path.splitext(f)[0] == base:
            with open(os.path.join(ocr_dir, f), encoding="utf-8", errors="ignore") as fh:
                return norm(fh.read())
    return ""


def find_contexts(hay: str, needle: str, span: int = 40, limit: int = 3):
    out, start = [], 0
    while len(out) < limit:
        i = hay.find(needle, start)
        if i < 0:
            break
        out.append(hay[max(0, i - span): i + len(needle) + span])
        start = i + 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    L = ["# 限定资料与词族检索记录", "",
         "命中仅是候选原文；零命中不证明无条款。文本汉字比例不证明数字、符号完整。",
         "A为文本层，B为已有文本缓存，来源及独立性待核；C须查看完整原页上下文。", ""]

    summary = []
    for rule in spec["rules"]:
        rid = rule["id"]
        L += [f"## {rid} · {rule['name']}", "",
              f"- 待否证命题：**{rule['claim_to_negate']}**",
              f"- 反查范围：{'、'.join(rule['scope'])}",
              f"- 概念词族：{'、'.join(rule['word_family'])}", "",
              "| 标准 | 通道A | 通道B | 词 | A命中 | B命中 | 判定 |",
              "|---|---|---|---|---|---|---|"]

        rule_hits = []
        missing_inputs = []
        for std_key in rule["scope"]:
            hit_pdf = None
            for fn in os.listdir(args.root):
                if std_key in fn and fn.lower().endswith(".pdf"):
                    hit_pdf = fn
                    break
            if not hit_pdf:
                L.append(f"| {std_key} | — | — | — | — | — | 文件缺失 |")
                missing_inputs.append(std_key + ":PDF缺失")
                continue

            a_txt, a_cjk = channel_a(os.path.join(args.root, hit_pdf))
            b_txt = channel_b(args.ocr, hit_pdf)
            if not a_txt or not b_txt:
                missing_inputs.append(std_key + ":读取通道不齐全")
            a_state = "可用" if a_txt else f"不可用(中文{a_cjk:.0%})"

            for w in rule["word_family"]:
                an = a_txt.count(norm(w)) if a_txt else None
                bn = b_txt.count(norm(w)) if b_txt else None
                if an:
                    verdict = "★ 候选命中待语义核准"
                    rule_hits.append((hit_pdf, "A", w, find_contexts(a_txt, norm(w))))
                elif bn:
                    verdict = "★ 候选命中待语义核准"
                    rule_hits.append((hit_pdf, "B", w, find_contexts(b_txt, norm(w))))
                else:
                    verdict = "限定词表未命中" if (a_txt or b_txt) else "无可用输入，无法判定"
                L.append(f"| {std_key} | {a_state} | {len(b_txt)}字符 | {w} | "
                         f"{'—' if an is None else an} | {bn} | {verdict} |")

        # 结论
        if rule_hits:
            L += ["", "### ⚠️ 检出候选内容，须目视判定支持范围", ""]
            for pdf, ch, w, ctxs in rule_hits:
                L.append(f"**{pdf}**（通道{ch}）· 词「{w}」命中 {len(ctxs)} 处：")
                L.append("")
                for c in ctxs:
                    L.append(f"> …{c}…")
                L.append("")
            L += [f"**处置**：关键词命中不直接决定basis，需核准条文是否支持整个命题或仅支持例外。",
                  "须由通道 C（目视原页裁图）确认命中是否为实质明文：",
                  "　- 若为实质明文 → 改判 `basis: standard`（补 cite）或 `basis: hybrid`（判定属经验、处置有明文）；",
                  "　- 若为噪声（目次/图注残片）→ 可维持 convention，但须在卡内记录该次检索与裁决理由。", ""]
            summary.append((rid, "候选命中待核", len(rule_hits)))
        elif missing_inputs:
            L += ["", "### 输入不足，无法完整判断", "、".join(missing_inputs), ""]
            summary.append((rid, "输入不足", "未知"))
        else:
            # 判断通道强度
            all_a = True
            for std_key in rule["scope"]:
                for fn in os.listdir(args.root):
                    if std_key in fn and fn.lower().endswith(".pdf"):
                        a_txt, _ = channel_a(os.path.join(args.root, fn))
                        if not a_txt:
                            all_a = False
                        break
            if all_a:
                L += ["", "### ✅ 限定词表未检出（文本通道可用，OCR独立性和覆盖待核）",
                      "零命中不证明不存在条款；B可能复用A提取文本，不据此宣称独立双通道。", ""]
                summary.append((rid, "未检出-范围待核", 0))
            else:
                L += ["", "### ⚠️ 限定词表未检出（读取覆盖与缺失输入待核）",
                      "输入完整性待核；未读取、OCR缺失与无命中必须区别记录，不能判定条款不存在。", ""]
                summary.append((rid, "未检出-输入待核", 0))
        L += ["---", ""]

    L += ["## 总表", "", "| 规则 | 检索状态 | 候选命中数 |", "|---|---|---|"]
    for rid, v, n in summary:
        L.append(f"| {rid} | {v} | {n} |")
    L += ["", "## 纪律（写回 01/03 文档）", "",
          "1. **否证的检索单位是概念词族**，单一术语检索不得作为否证依据。",
          "2. 关键词命中只提供线索，核准语义与适用范围后决定basis。",
          "3. 输入缺失或读取覆盖不全须记录，不用固定降一级替代证据核准。",
          "4. 每次否证必须留**检索词表 + 命中上下文**，否则不可复核。", ""]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write("\n".join(L))
    print(f"[ok] {args.out}")
    for rid, v, n in summary:
        print(f"  {rid:<26} {v}  命中={n}")


if __name__ == "__main__":
    main()
