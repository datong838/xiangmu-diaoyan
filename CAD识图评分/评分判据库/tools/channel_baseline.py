#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
channel_baseline.py —— 国标文本「通道可信度」基线测定

背景：
  判据库对每条 convention（经验）判据都下了一个**否定结论**——「国标查无明文」。
  否定结论的可靠性完全取决于文本通道本身是否完整：
  若通道丢字，就会出现「其实有明文，我却判成经验规则」的**伪 convention**，
  后果比漏检更严重（对外报告引了不存在的经验、或漏引真实条款）。

  因此必须先把「每份标准里，哪条通道可信、可信到什么程度」测出来。

通道定义（与 verify_cite.py 一致）：
  A = PDF 文本层（pymupdf get_text）—— 独立于 OCR；文字型 PDF 的权威通道
  B = 渲染 200dpi + RapidOCR —— 字体无 ToUnicode 映射 / 纯扫描件时的唯一通道
  C = 人读裁图 —— 终审

本工具输出：
  每份 PDF 的 A 通道字符数、B 通道字符数、A/B 比值、判定等级。

用法：
  python channel_baseline.py --root <国标目录> --ocr <_ocr_text目录> --out <报告路径>
"""
import argparse, os, re, sys, unicodedata
import fitz  # pymupdf


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", "", s)


def cjk_ratio(s: str) -> float:
    if not s:
        return 0.0
    cjk = len(re.findall(r"[\u4e00-\u9fff]", s))
    return cjk / len(s)


def grade(a_len: int, b_len: int, a_cjk: float) -> tuple:
    """返回 (等级, 说明)

    ★ 关键纪律：中文占比才是「文本层是否可用」的判据，不是字符数。
      字体无 ToUnicode 映射时，get_text 会返回大量**乱码 ASCII**（字符数很高、中文占比≈0）——
      这种「假文本层」比纯扫描件更危险：它会让人误以为存在独立通道，
      实际上它与 OCR 无关也读不出任何中文，**不构成交叉验证**。
    """
    if a_cjk >= 0.5 and a_len >= 2000:
        return "A-权威", "文本层可用且中文占比正常，通道A为准，OCR仅作交叉校验"
    if a_cjk >= 0.25 and a_len >= 800:
        return "A-部分", "文本层可提取但中文占比偏低（可能仅标题/符号层），通道A可辅助、不能单独下否定结论"
    if a_cjk >= 0.15:
        return "A-弱", "文本层残缺（多为字体无 ToUnicode 映射），否定结论必须由通道B承担并标注风险"
    if a_len >= 200:
        return "A-乱码", "★ 假文本层：字符数虚高但中文占比≈0（字体无 ToUnicode 映射）——不构成独立通道，实为单通道 B"
    return "B-唯一", "文本层不可用（纯扫描件），通道B是唯一文本通道，否定结论为单通道、需人工抽查"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    for fn in sorted(os.listdir(args.root)):
        if not fn.lower().endswith(".pdf"):
            continue
        path = os.path.join(args.root, fn)
        try:
            doc = fitz.open(path)
        except Exception as e:
            rows.append((fn, -1, -1, 0.0, "ERROR", str(e)))
            continue

        a_pages, a_chars = [], 0
        for i, page in enumerate(doc):
            t = page.get_text("text")
            n = len(norm(t))
            if n > 15:
                a_pages.append(i + 1)
            a_chars += n
        npages = doc.page_count
        a_cjk = cjk_ratio(norm("".join(p.get_text("text") for p in doc)))
        doc.close()

        # B 通道：读已产出的 OCR 文本
        base = os.path.splitext(fn)[0]
        cand = [f for f in os.listdir(args.ocr) if os.path.splitext(f)[0] == base]
        b_chars = 0
        if cand:
            with open(os.path.join(args.ocr, cand[0]), "r", encoding="utf-8", errors="ignore") as fh:
                b_chars = len(norm(fh.read()))

        g, why = grade(a_chars, b_chars, a_cjk)
        rows.append((fn, npages, a_chars, b_chars, a_cjk, g, why, len(a_pages)))

    # 报告
    L = ["# 国标文本通道可信度基线（channel_baseline.py 产出）", "",
         "> 用途：为 convention（经验）判据的**否定结论**提供可信度依据。",
         "> 通道 A = PDF 文本层（独立于 OCR）｜通道 B = 200dpi + RapidOCR｜通道 C = 人读裁图（终审）", "",
         "## 一、逐份测定", "",
         "| 标准 PDF | 页数 | 有文本层页 | A 字符 | B 字符 | A 中文占比 | 判定 | 含义 |",
         "|---|---|---|---|---|---|---|---|"]

    def clean(fn):
        return fn.replace("|", "/")

    for r in rows:
        if r[2] == -1:
            L.append(f"| {clean(r[0])} | — | — | — | — | — | ERROR | {r[5]} |")
            continue
        fn, npg, a, b, acjk, g, why, apg = r
        L.append(f"| {clean(fn)} | {npg} | {apg} | {a} | {b} | {acjk:.0%} | **{g}** | {why} |")

    # 统计
    from collections import Counter
    cnt = Counter(r[5] for r in rows if r[2] != -1)
    L += ["", "## 二、判定分布", "",
          "| 等级 | 份数 | 对否定结论的含义 |", "|---|---|---|",
          f"| A-权威 | {cnt.get('A-权威',0)} | 双通道可交叉验证，否定结论可信 |",
          f"| A-部分 | {cnt.get('A-部分',0)} | 通道A残缺，否定结论须通道B承担 |",
          f"| A-弱 | {cnt.get('A-弱',0)} | 同 A-部分 |",
          f"| A-乱码 | {cnt.get('A-乱码',0)} | ★ 假文本层，不构成交叉验证 → 等同 B-唯一 |",
          f"| B-唯一 | {cnt.get('B-唯一',0)} | 单通道，否定结论需人工抽查 |", ""]

    # 重点关注：convention 依赖的标准
    focus = ["4458.4", "4458.1", "4457.5", "4458.6", "4457.4"]
    L += ["## 三、convention 判据所依赖标准的通道情况（关键）", "",
          "| 依赖标准 | 对应 convention 规则 | 通道等级 | 否定结论是否可双通道验证 |", "|---|---|---|---|"]
    rule_map = {
        "4458.4": "L2-DIMCOMPLETE-001 / L1-CLOSEDCHAIN-001",
        "4458.1": "L2-PROJECTION-001",
        "4457.5": "（辅助：剖面区域，供 L3 参考）",
        "4458.6": "（辅助：剖视断面，供 L3/L2 参考）",
        "4457.4": "（辅助：图线，供 L1 参考）",
    }
    for key in focus:
        hit = [r for r in rows if key in r[0]]
        if not hit:
            L.append(f"| {key} | {rule_map.get(key,'')} | — | 未找到 |")
            continue
        r = hit[0]
        lvl = r[5]
        if lvl == "A-权威":
            verdict = "✅ 是（A 文本层 + B OCR 双通道）"
        elif lvl in ("A-部分", "A-弱"):
            verdict = "⚠️ 部分（A 残缺，以 B 为主，须 C 抽查）"
        elif lvl == "A-乱码":
            verdict = "❌ 否（假文本层，实为单通道 B，**须 C 目视抽查**）"
        else:
            verdict = "❌ 否（单通道 B，须 C 抽查）"
        L.append(f"| {key} | {rule_map.get(key,'')} | **{lvl}** | {verdict} |")

    L += ["", "## 四、纪律", "",
          "1. **A-权威**的标准：否定结论可由文本层独立验证，可信。",
          "2. **A-部分 / A-弱 / B-唯一**的标准：否定结论为**单通道或弱通道**，",
          "   必须在判据条目的 `ocr_dependency` 字段显式标注，并列入人工抽查清单。",
          "3. 任何**新增** convention 判据，入库前必须过本基线——",
          "   若其反查标准是 B-唯一，则该条 convention 定性的置信度自动降一级。", ""]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"[ok] 写入 {args.out}")
    for r in rows:
        if r[2] == -1:
            print(f"  ERROR {r[0]}: {r[5]}")
        else:
            print(f"  {r[5]:<8} A={r[2]:>6} B={r[3]:>6} cjk={r[4]:.0%}  {r[0]}")


if __name__ == "__main__":
    main()
