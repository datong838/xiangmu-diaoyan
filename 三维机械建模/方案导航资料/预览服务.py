#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loopback-only map and formatted reader for registered source IDs."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit
import argparse, hashlib, html, json, mimetypes, re, sys
sys.dont_write_bytecode = True
from 生成导航 import render_markdown, redact

ROOT = Path(__file__).resolve().parent.parent
READER_CSS = '''
:root{color-scheme:light dark;--bg:#f5f7fb;--paper:#fff;--ink:#17243d;--muted:#78869c;--line:#e4e9f1;--link:#446be7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}a:focus-visible{outline:2px solid var(--link);outline-offset:4px}
.reader-bar{position:sticky;top:0;z-index:2;padding:16px 28px;background:var(--paper);border-bottom:1px solid var(--line);display:flex;gap:22px;align-items:center;flex-wrap:wrap;font-size:14px}.reader-bar strong{margin-right:auto}
main{max-width:1240px;margin:28px auto;padding:32px 48px 64px;border:1px solid var(--line);border-radius:16px;background:var(--paper)}
.source-meta{font-size:12px;color:var(--muted);line-height:1.8;overflow-wrap:anywhere;border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:24px}
.rendered{font-size:17px;line-height:1.95;overflow-wrap:anywhere}.rendered h2{font-size:29px;line-height:1.5;margin:24px 0}.rendered h3{font-size:23px;margin:36px 0 16px;line-height:1.6}.rendered h4{font-size:20px;margin-top:28px}.rendered p{margin:10px 0}
.rendered table{display:block;width:100%;overflow:auto;border-collapse:collapse;font-size:15px;line-height:1.85;margin:20px 0}.rendered td{padding:11px 14px;border:1px solid var(--line);min-width:100px;vertical-align:top}.rendered tr:first-child{background:var(--bg);font-weight:600}
.rendered code{font-family:ui-monospace,"SFMono-Regular",monospace;font-size:.88em;background:var(--bg);border-radius:4px;padding:2px 4px}.rendered pre{white-space:pre-wrap;overflow:auto;background:var(--bg);padding:18px;border-radius:8px}.rendered pre code{padding:0}
@media(prefers-color-scheme:dark){:root{--bg:#151c29;--paper:#202a3a;--ink:#e4eaf5;--muted:#a3b1c6;--line:#344055;--link:#a9bdff}}
@media(max-width:1300px){main{margin:24px 20px}}@media(max-width:650px){main{margin:12px 8px;padding:20px 18px;border-radius:10px}.rendered{font-size:16px}.rendered h2{font-size:24px}.reader-bar{padding:12px 16px;gap:14px}}
@media print{.reader-bar{display:none}main{margin:0;padding:0;border:0;max-width:none}body{background:white;color:black}.rendered table{display:table;font-size:11px}.source-meta{font-size:10px}}
'''

def reading_page(node, raw, nodes):
    """Use the sidebar's renderer with the full, hash-checked original text."""
    bypath = {n['source_path']: n for n in nodes.values()}
    body = render_markdown(redact(raw.decode('utf-8')), Path(node['source_path']), bypath)
    # Preview links select a node in the map; reader links open that document here.
    body = re.sub(r'href="#doc=(cad3-[a-z0-9]+)" data-preview-doc="\1"', r'href="/source/\1"', body)
    esc = html.escape
    identity = esc(node['id'], quote=True)
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(node["title"])} · 三维方案阅读</title><style>{READER_CSS}</style></head>'
            f'<body><nav class="reader-bar" aria-label="阅读页导航"><strong>三维机械建模 · 文档阅读</strong>'
            f'<a href="/#doc={identity}">返回文档地图</a>'
            f'<a href="/raw/{identity}" target="_blank" rel="noopener">查看原始 Markdown ↗</a></nav>'
            f'<main><div class="source-meta">{esc(node["path"])}<br>'
            f'完整原文排版 · 来源指纹 {esc(node["sha256"][:12])} · 保留原文件</div>'
            f'<article class="rendered">{body}</article></main></body></html>').encode('utf-8')

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        data = json.loads((ROOT / '方案导航资料/文档图谱数据.json').read_text())
        nodes = {n['id']: n for n in data['nodes']}
        if path in ['/', '/三维方案文档地图.html']:
            return self.reply((ROOT / '三维方案文档地图.html').read_bytes(), 'text/html; charset=utf-8')
        route = path.split('/')
        if len(route) != 3 or route[1] not in ('source', 'raw') or route[2] not in nodes:
            return self.send_error(404)
        node = nodes[route[2]]
        if node['source_kind'] == 'external':
            self.send_response(302)
            self.send_header('Location', node['href'])
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        p = Path(node['source_path'])
        if p.is_dir():
            children = [(key, n) for key, n in nodes.items() if Path(n['source_path']).parent == p]
            links = ''.join('<li><a href="/source/' + key + '">' + html.escape(n['title']) + '</a></li>' for key, n in children)
            body = ('<!doctype html><meta charset="utf-8"><title>材料目录</title><a href="/">返回文档地图</a><h1>' + html.escape(node['title']) + '</h1><p>' + html.escape(str(p)) + '</p><p>以下仅列本地图已登记的直接子项；完整工件请在本机打开原目录。</p><ul>' + links + '</ul>').encode()
            return self.reply(body, 'text/html; charset=utf-8')
        if not p.is_file():
            return self.send_error(404)
        raw = p.read_bytes()
        if node['sha256'] and hashlib.sha256(raw).hexdigest() != node['sha256']:
            return self.send_error(409, 'Source changed; rebuild map')
        if p.suffix.lower() == '.md':
            if route[1] == 'source':
                return self.reply(reading_page(node, raw, nodes), 'text/html; charset=utf-8')
            return self.reply(raw, 'text/plain; charset=utf-8')
        self.reply(raw, mimetypes.guess_type(p.name)[0] or 'application/octet-stream')

    def reply(self, body, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8843)
    a = ap.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    print(f'三维地图 http://127.0.0.1:{a.port}', flush=True)
    server.serve_forever()
