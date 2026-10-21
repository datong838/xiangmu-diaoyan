#!/usr/bin/env python3
"""Generate a snapshot 3D reading map; canonical 2D content remains on port 8842."""
from pathlib import Path
import argparse, datetime, hashlib, html, json, os, re, sys
from urllib.parse import quote, unquote, urlsplit
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
HERE=Path(__file__).resolve().parent
KB=ROOT/'三维机械建模知识库方案'
TWO=ROOT.parent/'CAD识图评分/方案导航资料'
BASE2='http://127.0.0.1:8842/'
GROUPS=[('overview','总体架构与共同底座','#446be7'),('facts','工程对象与设计意图','#009d85'),('modeling','建模执行与资源','#9262d8'),('validation','装配、验证与修改','#d49025'),('contracts','接口合同与局部核验','#d46377'),('delivery','开工待办与交付记录','#55758c'),('foundation','二维制图与共用知识基础','#478a7e'),('kernel','usd-brep工具资料','#758795'),('navigation','入口与导航维护','#6477b1')]
SUB={'design':'方案设计','contract':'可校验设计附件','receipt':'阶段回执/有范围的验证','todo':'待办与实施路线','record':'历史编写与自查','cost':'用量与费用','entry':'阅读入口','two':'二维原文入口 · 在8842维护','tool':'工具说明与操作索引','artifact':'JSON及设计工件','directory':'工件目录入口'}
RX=re.compile(r'\[[^\]]*\]\((<[^>]+>|[^)\s]+)\)')
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def classify(p):
 n=p.name;m=re.match(r'(\d\d)-',n);i=int(m[1]) if m else -1
 if p.is_dir():return 'contracts','directory','工件目录'
 if n.startswith('README') or p.parent==HERE:return 'navigation','entry','导航说明'
 if 'Token' in n:return 'delivery','cost','费用记录 · 非账单'
 if i in {0,8,18,21}:return 'delivery','record','编写/阶段交付快照'
 if i in {7,19}:return 'delivery','todo','实施路线/未完成事项'
 if i in {10,14,15,17}:return 'contracts','receipt','范围化核验与接口记录'
 if i in {9,16}:return 'contracts','design','合同设计'
 if i in {1,3,6,20}:return ('modeling' if i==6 else 'overview'),'design','设计 · 非功能验收'
 if i in {2,11}:return 'facts','design','工程事实/意图设计'
 if i==4:return 'modeling','design','执行适配设计'
 if i in {5,12,13}:return 'validation','design','验证/装配/修改设计'
 if '契约' in p.parts:return 'contracts','contract','离线设计Schema'
 return 'contracts','artifact' if p.suffix=='.json' else 'design','模拟样例/历史回执 · 按原文范围'
def paths():
 files=sorted(KB.glob('*.md'))+[ROOT/'README.md',HERE/'README.md',HERE/'导航生成与维护方案.md']
 for folder in ['契约','设计样例','验证']:
  d=KB/folder
  files.append(d);files+=sorted(d.glob('*.json'))
 files.append(KB/'成本记录')
 for rel in ['README.md','详细使用说明.md','.agents/operations/INDEX.md']:
  files.append(Path('/Users/ddt/work/projects/ai_agent/cad/usd-brep')/rel)
 return sorted(set(files))
def build():
 registry_file=HERE/'稳定节点ID.json';reg=json.loads(registry_file.read_text()) if registry_file.exists() else {}
 two_data=json.loads((TWO/'文档图谱数据.json').read_text());two_by={n['source_path']:n for n in two_data['nodes']}
 nodes=[];ledger=[];missing=[]
 def external(path,title,url,headings=None):
  key='external:'+str(path)
  reg.setdefault(key,'cad3-'+sha(key.encode())[:16])
  n={'id':reg[key],'path':'二维基础 / '+title,'source_path':str(path),'title':title,'group':'foundation','sub':'two','role':'二维原入口 · 不复制正文','sha256':None,'headings':headings or [],'body':'此内容在二维导航统一维护。请点击“打开二维原入口”。\n\n'+url+'\n\n本三维导航不嵌入其正文，也不声称其全部能力已实现。','reference':False,'current':False,'truncated':False,'tags':['two'],'reason':'共用基础由二维原站点维护','assets':[],'href':url,'source_kind':'external'}
  nodes.append(n);return n
 external('two-dimensional-main','二维机械制图 · 总入口',BASE2)
 external_by={}
 for suffix in ['28-持续知识编译与工程Wiki设计.md','26-分阶段文件任务与大容量验收实施清单.md']:
  other=next((x for x in two_data['nodes'] if x['source_path'].endswith('/'+suffix)),None)
  if other:external_by[other['source_path']]=external(other['source_path'],other['title'],BASE2+'#doc='+other['id'],other.get('headings'))
 for f in paths():
  if not f.exists():missing.append(str(f));continue
  raw=f.read_bytes() if f.is_file() else b'';md=f.is_file() and f.suffix=='.md';txt=raw.decode('utf-8') if md else ''
  key=str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f);reg.setdefault(key,'cad3-'+sha(key.encode())[:16]);g,s,role=classify(f)
  if not f.is_relative_to(ROOT):g,s,role='kernel','tool','工具资料 · 非本机运行证明'
  heads=re.findall(r'^#{1,6}\s+(.+)$',txt,re.M);body=redact(txt)[:100000] if md else '这是设计附件或工件入口，本导航未解析或核准其工程内容。\n\n'+str(f)
  node={'id':reg[key],'path':key,'source_path':str(f),'title':heads[0] if heads else f.name,'group':g,'sub':s,'role':role,'sha256':sha(raw) if f.is_file() else None,'headings':heads,'body':body,'reference':False,'current':f==KB/'README.md','truncated':len(txt)>100000,'tags':[s],'reason':'按三维文档职责分类；不从标题推断实现状态','assets':[],'href':quote(os.path.relpath(f,ROOT),safe='/'),'source_kind':'markdown' if md else 'directory' if f.is_dir() else 'attachment'}
  nodes.append(node);ledger.append({'id':node['id'],'path':str(f),'sha256':node['sha256'],'bytes':len(raw),'headings':heads,'group':g,'role':role,'reading_scope':'全部正文扫描/来源性质与分类复核；不声称重新核准全部工程主张' if md else '仅工件入口'})
 # Register only actually referenced canonical 2D sources, without embedding their text.
 for node in list(nodes):
  if node['source_kind']!='markdown':continue
  for match in RX.finditer(node['body']):
   url=urlsplit(match[1].strip('<>'))
   if url.scheme or not url.path:continue
   target=os.path.abspath(Path(node['source_path']).parent/unquote(url.path))
   other=two_by.get(target)
   if other and target not in external_by:
    external_by[target]=external(target,other['title'],BASE2+'#doc='+other['id'],other.get('headings'))
 bypath={n['source_path']:n for n in nodes};byid={n['id']:n for n in nodes};edges=[];pending=[];seen=set()
 for node in nodes:
  if node['source_kind']!='markdown':continue
  for match in RX.finditer(node['body']):
   target=match[1].strip('<>');u=urlsplit(target)
   if u.scheme or not u.path:continue
   path=os.path.abspath(Path(node['source_path']).parent/unquote(u.path));other=bypath.get(path)
   if other and node['id']!=other['id']:
    pair=(node['id'],other['id'])
    if pair not in seen:edges.append({'source':pair[0],'target':pair[1],'kind':'原文显式引用'+(' · 二维原入口' if other['source_kind']=='external' else ''),'evidence':node['path']+' · Markdown链接'});seen.add(pair)
   elif not other:pending.append({'source':node['id'],'target':target,'reason':'范围外工件入口' if Path(path).exists() else '原文链接目标待核'})
 for n in nodes:n['preview_html']=render_markdown(n['body'],Path(n['source_path']),bypath)
 data={'revision':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d'),'model':'来源快照 · 设计/回执/待办分列','groups':[{'id':i,'label':l,'color':c} for i,l,c in GROUPS],'subnames':SUB,'nodes':nodes,'edges':edges,'stats':{'system':sum(n['source_kind']=='markdown' and n['group'] not in ['kernel','navigation'] for n in nodes),'database':sum(n['source_kind']=='external' for n in nodes),'documents':len(nodes),'reference':0,'relations':len(edges)},'canonical_2d':BASE2,'canonical_2d_map_sha256':sha((TWO/'文档图谱数据.json').read_bytes())}
 report={'ok':not missing,'missing_inputs':missing,'nodes':len(nodes),'local_sources':len(ledger),'canonical_2d_links':data['stats']['database'],'relations':len(edges),'pending_links':len(pending),'unique_ids':len(byid)==len(nodes),'source_reading_scope':'作者已有编写/阅读基础；本轮全量扫描与分组复核；原附件不作工程核准','generated_at':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
 return data,reg,ledger,pending,report

def redact(text):
 return '\n'.join('[凭据内容不进入导航预览，请核对原文]' if re.search(r'(?:password|passwd|api[_-]?key|secret|密码)\s*[:=]\s*\S+',line,re.I) else line for line in text.splitlines())

def render_markdown(text,source,bypath):
 def inline(s):
  # Escape before applying a small formatting subset; never render source HTML.
  s=html.escape(s)
  def lk(m):
   label,target=m[1],html.unescape(m[2]).strip('<>');u=urlsplit(target)
   if u.scheme not in ('','http','https'):return label+'（链接未启用）'
   if not u.scheme:
    p=Path(os.path.abspath(source.parent/unquote(u.path)));node=bypath.get(str(p))
    if node and node['source_kind']=='external':return '<a target="_blank" rel="noopener noreferrer" href="'+html.escape(node['href'],quote=True)+'">'+label+' ↗</a>'
    if node:return '<a href="#doc='+node['id']+'" data-preview-doc="'+node['id']+'">'+label+'</a>'
    return label+'（见原文附件）'
   return '<a target="_blank" rel="noopener noreferrer" href="'+html.escape(target,quote=True)+'">'+label+'</a>'
  s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lk,s)
  s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s);s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
  return s
 out=[];code=False;table=False
 for line in text.splitlines():
  if line.startswith('```'):
   if table:out.append('</table>');table=False
   out.append('</code></pre>' if code else '<pre><code>');code=not code;continue
  if code:out.append(html.escape(line)+'\n');continue
  if line.startswith('|') and line.endswith('|'):
   if re.match(r'^\|[\s:|\-]+\|$',line):continue
   if not table:out.append('<table>');table=True
   out.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in line.strip('|').split('|'))+'</tr>');continue
  if table:out.append('</table>');table=False
  h=re.match(r'^(#{1,6})\s+(.+)',line)
  if h:level=min(len(h[1])+1,6);out.append(f'<h{level}>'+inline(h[2])+f'</h{level}>')
  elif line.strip():out.append('<p>'+inline(line)+'</p>')
 if table:out.append('</table>')
 if code:out.append('</code></pre>')
 return ''.join(out)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
 data,reg,ledger,pending,report=build()
 assert len({n['id'] for n in data['nodes']})==len(data['nodes'])
 if a.check:
  old=json.loads((HERE/'文档图谱数据.json').read_text())
  signature=lambda d:([(n['id'],n['sha256'],n['href'],n['title']) for n in d['nodes']],d['canonical_2d_map_sha256'])
  ok=signature(data)==signature(old);print(json.dumps({'ok':ok,'scope':'三维来源增删改与二维跳转映射快照'},ensure_ascii=False));return 0 if ok else 1
 assert report['ok'],report
 for n in data['nodes']:
  if n['source_kind']=='external':ledger.append({'id':n['id'],'path':n['source_path'],'canonical_url':n['href'],'group':'foundation','reading_scope':'仅二维原站点链接及标题元数据，不嵌入正文'})
 template=(HERE/'导航模板.html').read_text()
 encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
 page=template.replace('__CAD_DATA__',encoded);assert '__CAD_DATA__' not in page
 for name,x in [('文档图谱数据.json',data),('稳定节点ID.json',reg),('原文引用待核列表.json',pending)]:dump(HERE/name,x)
 (HERE/'来源阅读与分类台账.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in ledger)+'\n')
 target=ROOT/'三维方案文档地图.html';tmp=HERE/'navigation.tmp';tmp.write_text(page);tmp.replace(target)
 report['artifact_sha256']=sha(target.read_bytes());dump(HERE/'导航核查记录.json',report);print(json.dumps(report,ensure_ascii=False));return 0
if __name__=='__main__':sys.exit(main())
