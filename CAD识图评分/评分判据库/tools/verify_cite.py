#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_cite.py —— 判据依据「逐字引文锚定」验证器（v2）

针对「OCR 可能看错」的治理：
  每条 cite 必须附一句**逐字引文**(quote)，本工具在声称页上定位它。
  但逐字匹配有一个致命盲区：分不清「我引错了」与「OCR 读错了」。
  故 v2 引入三级判定 + 双通道：

  通道 A：PDF 文本层（pymupdf search_for）—— 独立于 OCR，可读文本通道（数字/符号仍须回看图像）
  通道 B：渲染页面 + RapidOCR 取坐标框 —— 扫描/字体无映射 PDF 的唯一文本通道
  通道 C（人/多模型）：完整原页及图例核对；裁图可能漏上下文，不能单独裁决

  判定状态：
    OK         精确定位（引文在该页存在）
    OK_FUZZY   模糊定位（相似度≥阈值，通常= OCR 字符级误读；附 OCR 实读文本供核对）
    FAIL_PAGE  引文不在声称页，但在其它页 -> 页码错
    FAIL       声称页及邻页未检出 -> 引文存疑，非全文无条款证明
    AMBIGUOUS  多处命中 -> 引文不够独特，需消歧
    ERROR      运行异常

用法：
    python verify_cite.py --pdf <p> --page <n> --quote "..." --out <dir>
    python verify_cite.py --batch <json> --outroot <root>
"""
import argparse, json, os, re, sys, unicodedata, difflib
import fitz  # pymupdf

FUZZY_TH = 0.86          # 模糊匹配阈值
SWEEP_RADIUS = 4         # 全文档回查：先扫 ±N 页

def norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u3000", " ")
    s = re.sub(r"\s+", "", s)
    for a, b in [("—", "-"), ("－", "-"), ("–", "-"), ("／", "/"), ("：", ":")]:
        s = s.replace(a, b)
    return s

def sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()

def _has_text_layer(page: fitz.Page) -> bool:
    txt = re.sub(r"\s", "", page.get_text("text"))
    return len(txt) > 15 and len(re.findall(r"[\u4e00-\u9fff]", txt)) / len(txt) >= 0.15

def _tl_search(page: fitz.Page, quote: str):
    """通道A：返回 (rects, how)"""
    rects = page.search_for(quote)
    if rects:
        return rects, "textlayer-exact"
    parts = [p for p in re.split(r"[，。；、（）()]+", quote) if len(p) >= 4]
    for p in parts[:3]:
        r = page.search_for(p)
        if r:
            return r, "textlayer-partial"
    return [], "textlayer-miss"

_OCR = None
_OCR_CACHE = {}
def _ocr_blocks(page: fitz.Page, dpi: int = 200):
    """通道B：返回 [(rect_pdfcoord, text)]（带页面级缓存，防重复 OCR 爆内存）"""
    global _OCR
    key = (page.parent.name, page.number, dpi)
    if key in _OCR_CACHE:
        return _OCR_CACHE[key], "ocr-cached"
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as e:
        return [], "ocr-unavailable"
    if _OCR is None:
        _OCR = RapidOCR()
    import tempfile, gc
    zoom = dpi / 72.0
    pix = page.get_pixmap(dpi=dpi)
    tmp = tempfile.mktemp(suffix=".png")
    pix.save(tmp)
    del pix
    try:
        res, _ = _OCR(tmp)
    finally:
        try: os.remove(tmp)
        except OSError: pass
        gc.collect()
    out = []
    for box, text, score in (res or []):
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        r = fitz.Rect(min(xs)/zoom, min(ys)/zoom, max(xs)/zoom, max(ys)/zoom)
        out.append((r, text))
    _OCR_CACHE[key] = out
    return out, "ocr"

def _segments(q: str, n: int = 5):
    """把引文切成重叠小段，抗 OCR 丢字/分块"""
    if len(q) <= n:
        return [q]
    out, step = [], max(1, n - 1)
    for s in range(0, len(q) - n + 1, step):
        out.append(q[s:s + n])
    if (len(q) - n) % step:
        out.append(q[-n:])
    return out

def _seg_match(joined: str, idxmap, q: str):
    """分段召回：每段在整页文本里模糊找最相似窗口；返回 (min_sim, 命中字符位置列表)"""
    segs = _segments(q)
    mins, poss = 1.0, []
    for sg in segs:
        W = len(sg); best, bp = 0.0, 0
        for s in range(0, max(1, len(joined) - W + 1)):
            v = sim(sg, joined[s:s + W])
            if v > best:
                best, bp = v, s
        mins = min(mins, best)
        poss.append(bp)
    return mins, poss

def _lcs_len(a: str, b: str) -> int:
    """最长公共子序列长度（抗 OCR 丢字/插字）"""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1])
        prev = cur
    return prev[len(b)]

COVERAGE_TH = 0.85

def _ocr_search(page: fitz.Page, quote: str, dpi: int = 200):
    """通道B定位：完整匹配或连续窗口近似；不启用跨位置拼凑。"""
    blocks, state = _ocr_blocks(page, dpi)
    if not blocks:
        return [], state if state == "ocr-unavailable" else "ocr-empty", "", 0.0
    nq = norm(quote)
    for r, t in blocks:
        if nq and nq in norm(t):
            return [r], "ocr-block", t, 1.0
    joined, idxmap = "", []
    for i, (r, t) in enumerate(blocks):
        nt = norm(t); joined += nt; idxmap += [i] * len(nt)
    pos = joined.find(nq) if nq else -1
    if pos >= 0:
        i0, i1 = idxmap[pos], idxmap[min(pos + len(nq) - 1, len(idxmap) - 1)]
        rr = [blocks[i][0] for i in range(i0, i1 + 1)]
        r = rr[0]
        for x in rr[1:]:
            r = r | x
        return [r], "ocr-joined", "".join(blocks[i][1] for i in range(i0, i1 + 1)), 1.0
    # 仅连续窗口近似召回；禁用全页LCS和跨位置分句拼凑。
    W = max(len(nq), 8); best = (0.0, None, "")
    for s in range(0, max(1, len(joined) - W + 1), 2):
        v = sim(nq, joined[s:s + W])
        if v > best[0]:
            bi = idxmap[min(s, len(idxmap) - 1)]
            bj = idxmap[min(s + W - 1, len(idxmap) - 1)]
            region = blocks[bi][0]
            for k in range(bi + 1, bj + 1):
                region = region | blocks[k][0]
            best = (v, region, joined[s:s + W])
    if best[1] is not None and best[0] >= FUZZY_TH:
        return [best[1]], "ocr-window", best[2], best[0]
    return [], "ocr-miss", best[2], best[0]

def _card(page: fitz.Page, r: fitz.Rect, outdir: str, page_no: int, dpi=200):
    page.get_pixmap(dpi=dpi).save(os.path.join(outdir, "page_%d.png" % page_no))
    pad = 10
    clip = fitz.Rect(r.x0-pad, r.y0-pad, r.x1+pad, r.y1+pad)
    clip &= page.rect
    page.get_pixmap(clip=clip, dpi=300).save(os.path.join(outdir, "clause_crop.png"))
    # 整页高亮图（红框）：复制该页后直接 draw_rect，避免 show_pdf_page 叠加失效
    nd = fitz.open()
    nd.insert_pdf(page.parent, from_page=page.number, to_page=page.number)
    np_ = nd[0]
    np_.draw_rect(r, color=(1, 0, 0), width=1.5)
    np_.get_pixmap(dpi=dpi).save(os.path.join(outdir, "page_highlight.png"))
    nd.close()

def verify_one(pdf_path, page_no, quote, outdir, dpi=200):
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    n = len(doc)
    rec = {"pdf": os.path.basename(pdf_path), "page": page_no,
           "quote": quote, "n_pages": n}
    if not (1 <= page_no <= n):
        rec.update(status="ERROR", reason="页码越界"); doc.close(); return rec
    page = doc[page_no-1]
    if not norm(quote):
        rec.update(status="ERROR", reason="空引文不能校验")
        doc.close(); return rec

    rects, how, otext, osim = [], "none", "", 0.0
    chans = []
    if _has_text_layer(page):
        rects, how = _tl_search(page, quote)
        if rects: chans.append("A-textlayer")
    if not rects:
        rects, how, otext, osim = _ocr_search(page, quote, dpi)
        if rects: chans.append("B-ocr-" + how.split("-")[-1])
    rec["channel"] = "+".join(chans) if chans else "A+B(claimed-page miss)"
    if otext:
        rec["ocr_read"] = otext[:80]
        rec["ocr_sim"] = round(osim, 3)

    if rects:
        exact = how in {"textlayer-exact", "ocr-block", "ocr-joined"}
        repeated = norm(page.get_text()).count(norm(quote)) > 1 if how.startswith("textlayer") else norm(otext).count(norm(quote)) > 1
        rec.update(status="AMBIGUOUS" if repeated or len(norm(quote)) < 8 else ("OK" if exact else "OK_FUZZY"), how=how, semantic_support="not_checked")
        region = rects[0]
        for rect in rects[1:]:
            region = region | rect
        _card(page, region, outdir, page_no, dpi)
        rec["card"] = ["page_%d.png" % page_no, "clause_crop.png", "page_highlight.png"]
        doc.close(); return rec

    if how == "ocr-unavailable":
        rec.update(status="ERROR", reason="OCR依赖不可用，不能据此认定引文不存在")
        doc.close(); return rec

    # 全文档回查（文本层 + OCR 模糊）——先扫邻近页，控成本
    found = []
    sweep = [p for p in range(max(1, page_no-SWEEP_RADIUS), min(n, page_no+SWEEP_RADIUS)+1) if p != page_no]
    for pno in sweep:
        pg = doc[pno-1]
        hit = False
        if _has_text_layer(pg) and pg.search_for(quote):
            hit = True
        if not hit:
            r2, how2, t2, s2 = _ocr_search(pg, quote, dpi=min(dpi, 150))
            if r2 and how2 in {"ocr-block", "ocr-joined"}: hit = True
        if hit: found.append(pno)
    if found:
        rec.update(status="FAIL_PAGE", reason="引文不在声称页，但出现在邻近页",
                   found_on_pages=found, hint="页码可能应为第 %s 页" % found,
                   swept="±%d" % SWEEP_RADIUS)
    else:
        rec.update(status="FAIL",
                   reason="邻近页(±%d)内未命中：引文或条款存疑（疑似引用错误，或 OCR 严重失真需通道C复核）" % SWEEP_RADIUS,
                   swept="±%d" % SWEEP_RADIUS)
    doc.close(); return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf"); ap.add_argument("--page", type=int); ap.add_argument("--quote")
    ap.add_argument("--out", default=".")
    ap.add_argument("--batch"); ap.add_argument("--outroot", default="evidence")
    a = ap.parse_args()
    if a.batch:
        items = json.load(open(a.batch, encoding="utf-8"))
        results = []
        for it in items:
            cid = it.get("id", "item")
            od = os.path.join(a.outroot, cid)
            pdf = it["pdf"]
            if not os.path.isabs(pdf):
                pdf = os.path.join(os.path.dirname(a.batch), pdf)
            try:
                r = verify_one(pdf, int(it["page"]), it["quote"], od)
            except Exception as e:
                r = {"status": "ERROR", "reason": str(e)}
            r["id"] = cid; r["clause"] = it.get("clause", "")
            results.append(r)
            flag = {"OK": "✅", "OK_FUZZY": "🟡", "FAIL_PAGE": "🔶",
                    "FAIL": "❌", "AMBIGUOUS": "⚠️", "ERROR": "💥"}.get(r["status"], "?")
            extra = ""
            if r["status"] == "OK_FUZZY":
                extra = " | OCR实读: %s (sim %.2f)" % (r.get("ocr_read", "")[:24], r.get("ocr_sim", 0))
            elif r["status"] == "FAIL_PAGE":
                extra = " | 应在 p%s" % r.get("found_on_pages")
            print("%s %-8s %-9s %s%s" % (flag, cid, r["status"], r.get("channel", ""), extra))
        json.dump(results, open(os.path.join(a.outroot, "verify_report.json"), "w"),
                  ensure_ascii=False, indent=1)
        from collections import Counter
        c = Counter(r["status"] for r in results)
        print("\n合计 %d 条：" % len(results) + " / ".join("%s %d" % (k, v) for k, v in c.items()))
        print("报告 -> %s/verify_report.json" % a.outroot)
        sys.stdout.flush()
        os._exit(0)   # 规避 onnxruntime 析构期崩溃
        return
    r = verify_one(a.pdf, a.page, a.quote, a.out)
    print(json.dumps(r, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
