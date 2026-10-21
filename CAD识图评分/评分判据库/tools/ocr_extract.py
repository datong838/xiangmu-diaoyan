#!/usr/bin/env python3
"""国标 PDF → 文本索引（判据库条款核对用）

背景：18 份国标 PDF 里只有 3 份能直接提取中文文本，其余是
      ① 字体未嵌 ToUnicode（pypdf 提取为乱码）② 纯扫描无文字层。
策略：文本型直接提取；其余走 RapidOCR（pymupdf 渲染 + onnxruntime 识别）。
输出：国标/_ocr_text/<文件名>.txt，按 `===== PAGE n =====` 分页。
用法：/Users/ddt/.workbuddy/binaries/python/envs/default/bin/python ocr_extract.py
"""
import os, re, glob
import fitz
from pypdf import PdfReader

SRC = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(SRC, "国标")):
    SRC = os.path.dirname(SRC)
SRC = os.path.join(SRC, "国标")
OUT = os.path.join(SRC, "_ocr_text")
DPI = 200


def try_pypdf(path):
    try:
        r = PdfReader(path)
    except Exception:
        return None, 0
    pages = [(p.extract_text() or "") for p in r.pages]
    cn = len(re.findall(r"[\u4e00-\u9fff]", "".join(pages)))
    return pages, cn


def ocr_pages(path, ocr):
    doc = fitz.open(path)
    chunks = []
    for i in range(len(doc)):
        pix = doc[i].get_pixmap(dpi=DPI)
        tmp = "/tmp/_ocr_tmp.png"
        pix.save(tmp)
        res, _ = ocr(tmp)
        lines = [t for _, t, _ in (res or [])]
        chunks.append(f"===== PAGE {i + 1} =====\n" + "\n".join(lines))
    return chunks


def main():
    os.makedirs(OUT, exist_ok=True)
    ocr = None
    for f in sorted(glob.glob(os.path.join(SRC, "*.pdf"))):
        base = os.path.splitext(os.path.basename(f))[0]
        out = os.path.join(OUT, base + ".txt")
        if os.path.exists(out) and os.path.getsize(out) > 500:
            print("skip", base, flush=True)
            continue
        pages, cn = try_pypdf(f)
        if pages is not None and cn > 500:
            mode = "text"
            txt = "\n".join(
                f"===== PAGE {i + 1} =====\n{p.strip()}" for i, p in enumerate(pages)
            )
        else:
            mode = "ocr"
            if ocr is None:
                from rapidocr_onnxruntime import RapidOCR

                ocr = RapidOCR()
            txt = "\n".join(ocr_pages(f, ocr))
        with open(out, "w") as fh:
            fh.write(txt)
        print(f"done {base} [{mode}] {len(pages) if pages else '?'}p", flush=True)


if __name__ == "__main__":
    main()
