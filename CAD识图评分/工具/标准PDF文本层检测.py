#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准 PDF 质量分级检测工具
判据：① 字体是否嵌入（emb=yes=原生排版；no=后加OCR层）
     ② 是否整页扫描图（图像像素 >> 页面面积）
     ③ 文本层页数与字符数
用法：python3 标准PDF文本层检测.py <文件或目录>
"""
import sys, os, subprocess, glob
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

def check(path):
    r = {"file": os.path.basename(path)}
    try:
        d = pymupdf.open(path); n = len(d)
        pages_text = sum(1 for p in d if len(p.get_text().strip()) >= 50)
        chars = sum(len(p.get_text().strip()) for p in d)
        drawings = sum(len(p.get_drawings()) for p in d)
        r.update(页数=n, 文本页=pages_text, 字符=chars, 矢量=drawings)
        # 字体嵌入情况
        emb = noemb = 0
        for i in range(min(n, 6)):
            for f in d[i].get_fonts():
                if len(f) > 3 and f[3] == "TrueType" or (len(f) > 2 and str(f[2]).endswith(("TrueType","Type0"))):
                    pass
        try:
            for i in range(min(n, 8)):
                for f in d[i].get_fonts(full=True):
                    # f = (xref, ext, type, basename, name, encoding)
                    nm = (f[3] or "") + " " + (f[4] or "")
                    out = subprocess.run(["pdffonts","-f",str(i+1),"-l",str(i+1),path],
                                         capture_output=True,text=True,timeout=30).stdout
                    for l in out.splitlines()[2:]:
                        tk = l.split()
                        # emb 列在最后一个 object ID 前第3位
                        if len(tk) >= 6 and tk[-3] in ("yes","no"):
                            if tk[-3] == "yes": emb += 1
                            else: noemb += 1
                    break
        except Exception: pass
        # 整页图检测（取中间页）
        mid = d[n // 2] if n else None
        if mid:
            R = mid.rect; area = R.width * R.height
            ia = sum((im[2] * im[3]) for im in mid.get_images(full=True))
            r["图倍率"] = round(ia / area, 1) if area else 0
        else:
            r["图倍率"] = 0
        # 分级
        if pages_text == 0:
            if drawings > 100:
                r["类型"] = "🔷 矢量图·文字转曲"
            else:
                r["类型"] = "❌ 纯扫描件"
        elif emb > 0 and r.get("图倍率", 0) < 3:
            r["类型"] = "✅ 原生电子版（排版导出，可信）"
        else:
            r["类型"] = "🟠 扫描图+OCR文字层（有识别错误风险）"
        r["字体"] = f"嵌入{emb}/未嵌{noemb}"
    except Exception as e:
        r["类型"] = f"读取失败 {e}"
    return r

def main(targets):
    files = []
    for t in targets:
        if os.path.isdir(t):
            files += glob.glob(os.path.join(t, "*.pdf")) + glob.glob(os.path.join(t, "*.PDF"))
        else: files.append(t)
    files = sorted(set(files))
    print(f"{'文件':<40}{'类型':<32}{'页':>4}{'文本页':>7}{'字符':>8}{'图倍':>6}  字体")
    print("-" * 116)
    for f in files:
        r = check(f)
        if not r["file"].startswith("T0"):
            print(f"{r['file'][:38]:<40}{r.get('类型','?'):<32}{r.get('页数','?'):>4}"
                  f"{r.get('文本页','?'):>7}{r.get('字符','?'):>8}{r.get('图倍率','?'):>6}  {r.get('字体','')}")
if __name__ == "__main__":
    main(sys.argv[1:] if len(sys.argv) > 1 else ["."])
