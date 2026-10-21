#!/usr/bin/env python3
"""Generate an offline, evidence-linked CAD reading map. No source writes."""
from pathlib import Path
import argparse, collections, datetime, hashlib, html, json, os, re, sys
from urllib.parse import quote, unquote, urlsplit
from zoneinfo import ZoneInfo
ROOT=Path('/Users/ddt/work/projects/ai_agent/docs/项目调研/CAD识图评分')
HERE=Path(__file__).resolve().parent
KB='CAD图纸智能审查系统_全套建设文档/知识库重点建设方案/'
GROUPS=[('system','项目目标与系统方案','#446be7'),('knowledge','工程知识库长期设计','#009d85'),('experiments','实验方案与验证结果','#9262d8'),('materials','标准、图纸与公开数据','#d49025'),('criteria','判据与复核资产','#d46377'),('management','采购、成本与对外材料','#55758c'),('process','调研、评审与治理记录','#758795'),('history','历史版本与旧交付包','#8b8d99'),('navigation','入口与阅读导航','#6477b1')]
SUB={'scope':'目标与总体设计','construction':'判据、案例与建设','kbmain':'知识职责与总体架构','kbbase':'治理、检索与部署','kbsource':'资料吸收与实例覆盖','kbroute':'验收路线与文件任务','kbplan':'知识库局部实验方案','kbresult':'知识库实验结果','ocr':'OCR识图实验','prototype':'知识库验证原型','standard':'标准原件','drawing':'客户图纸与要求','dataset':'公开数据集入口','asset':'候选判据与复核包','criterionplan':'判据复核方案','criterionresult':'判据审计与结果','purchase':'成本与采购','external':'对外说明与配图','record':'调研与阅读记录','review':'编制、自查与评审','governance':'目录治理','historical':'历史快照与旧稿','index':'项目与专题入口','machine':'设计数据与机器回执'}
RX=re.compile(r'\[[^\]]*\]\((<[^>]+>|[^)\s]+)\)')
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def classify(p):
 r=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix();n=p.name
 if '历史版本/' in r or '历史方案与交付包/' in r or '历史快照/' in r:return 'history','historical','历史资料'
 if n.startswith('README') or n in ['文档职责索引.md','文档分类索引.md']:return 'navigation','index','阅读入口'
 if KB in r:
  m=re.match(r'(\d\d)-',n);i=int(m[1]) if m else -1
  if i in {16,18,20,22,24}:return 'experiments','kbplan','局部实验设计'
  if i in {17,19,21,23,25}:return 'experiments','kbresult','阶段验证记录'
  if i in {0,9,15,27,29,30}:return 'process','review','编制与自查记录'
  if i in {1,10,11,28}:return 'knowledge','kbmain','长期建设设计'
  if i in {2,3,4,5,31}:return 'knowledge','kbbase','长期建设设计'
  if i in {12,14}:return 'knowledge','kbsource','资料吸收设计'
  if i in {6,7,26}:return 'knowledge','kbroute','路线与设计依据'
  return 'knowledge','machine','设计数据/历史机器回执'
 if 'CAD图纸智能审查系统_全套建设文档/' in r:return 'system','scope' if '目标态' in n or '实施' in n else 'construction','项目建设设计'
 if n=='CAD识图规范检查_第一阶段任务与目标.md':return 'system','scope','首期目标'
 if '/mybuddy/refs/ocr/' in r:return 'experiments','ocr','OCR实验入口' if p.suffix=='.md' else '实验工件目录'
 if '/cad/engineering-kb/' in r:return 'experiments','prototype','离线原型入口' if p.suffix=='.md' else '原型工件目录'
 if '/cad/dataset/' in r:return 'materials','dataset','数据集说明' if p.suffix=='.md' else '原始数据入口'
 if r.startswith('国标/'):return 'materials','standard','标准资料/提取说明'
 if r.startswith('工程图审核/'):return 'materials','drawing','素材核查' if p.suffix=='.md' else '原图与来源材料'
 if r.startswith('评分判据库/'):
  m=re.match(r'(\d\d)_',n)
  if m and int(m[1]) in {1,3,5,7,9,11}:return 'experiments','criterionplan','判据复核方案'
  if m:return 'experiments','criterionresult','阶段审计/映射记录'
  return 'criteria','asset','候选判据/复核资料'
 if r.startswith('项目管理/') or 'Token' in n:return 'management','purchase','费用与管理记录'
 if r.startswith('对外材料/'):return 'management','external','对外材料'
 if '文档治理/' in r:return 'process','governance','治理记录'
 if '评审与修订记录/' in r:return 'process','review','阶段评审记录'
 return 'process','record','过程记录'
def redact(text):
 return '\n'.join('[凭据内容不进入导航预览，请核对原文]' if re.search(r'(?:password|passwd|api[_-]?key|secret|密码)\s*[:=]\s*\S+',line,re.I) else line for line in text.splitlines())
def paths():
 files=[p for p in ROOT.rglob('*.md') if '方案导航资料' not in p.relative_to(ROOT).parts]
 for folder,exts in [('国标',{'.pdf','.csv'}),('工程图审核',{'.pdf','.dwg','.dxf','.docx'}),('项目管理/成本与采购',{'.xlsx','.csv'})]:
  files += [p for p in (ROOT/folder).iterdir() if p.is_file() and p.suffix.lower() in exts]
 files += [p for p in (ROOT/KB).iterdir() if p.is_file() and p.suffix in {'.csv','.json'}]
 for rel in ['评分判据库/criteria','评分判据库/data','评分判据库/evidence','评分判据库/review','评分判据库/tools']:
  files.append(ROOT/rel)
 external={
 '/Users/ddt/work/projects/ai_agent/mybuddy/refs/ocr':['README.md','OCR总体方案-MASTER.md','USAGE.md','EXPERIENCE-DATA.md','R3-CHECKLIST.md','文档/README.md','文档/脚本治理/新增实验规范.md','testdata/README_实验数据导航.md','state/README_运行状态说明.md','testdata','state'],
 '/Users/ddt/work/projects/ai_agent/cad/engineering-kb':['README.md','contracts','fixtures','reports','tests'],
 '/Users/ddt/work/projects/ai_agent/cad/dataset':['数据集下载与使用说明.md','ParaCAD/详细使用说明.md','TriView2CAD/详细使用说明.md','TrOCR-engineering/详细使用说明.md','NBSDC-刀具二维图纸/获取说明.md','NBSDC-逆向喷流样机/获取说明.md']}
 for base,rels in external.items():files += [Path(base)/rel for rel in rels]
 return sorted(set(files))
def build(out):
 regpath=out/'方案导航资料/稳定节点ID.json';reg=json.loads(regpath.read_text()) if regpath.exists() else {};nodes=[];ledger=[];missing=[]
 for p in paths():
  if not p.exists():missing.append(str(p));continue
  key=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
  reg.setdefault(key,'cad-'+sha(key.encode())[:16]);isdoc=p.suffix.lower()=='.md' and p.is_file();raw=p.read_bytes() if p.is_file() else b''
  text=raw.decode('utf-8') if isdoc else '';group,sub,role=classify(p)
  heads=re.findall(r'^#{1,6}\s+(.+)$',text,re.M);title=heads[0].strip() if heads else p.stem if p.is_file() else p.name+' · 目录'
  body=redact(text);body=body[:100000]
  if not isdoc:body='这是原始材料或工件入口。\n\n类型：'+('目录' if p.is_dir() else p.suffix.upper())+'\n位置：'+str(p)+'\n\n本导航未解析或核准该附件正文，请通过“打开原文件”查看。'
  node={'id':reg[key],'path':key,'source_path':str(p),'title':title,'group':group,'sub':sub,'role':role,'sha256':sha(raw) if p.is_file() else None,'headings':heads,'body':body,'truncated':len(text)>100000,'reference':False,'current':False,'tags':[sub],'reason':'按文档职责索引及路径编排；不代表实现状态','assets':[], 'href':quote(os.path.relpath(p,ROOT),safe='/'), 'source_kind':'markdown' if isdoc else 'directory' if p.is_dir() else 'attachment'}
  nodes.append(node);ledger.append({'id':node['id'],'path':str(p),'sha256':node['sha256'],'bytes':len(raw) if p.is_file() else None,'headings':heads,'group':group,'sub':sub,'role':role,'coverage':'正文扫描并提取导航，不声称全文工程理解' if isdoc else '仅材料入口，未解析正文'})
 bypath={n['source_path']:n for n in nodes};byid={n['id']:n for n in nodes};edges=[];pending=[];seen=set()
 for n in nodes:
  for match in RX.finditer(n['body'] if n['source_kind']=='markdown' else ''):
   target=match[1].strip('<>');url=urlsplit(target)
   if url.scheme or target.startswith('#'):continue
   p=(Path(n['source_path']).parent/unquote(url.path));p=Path(os.path.abspath(str(p)))
   other=bypath.get(str(p))
   if other and other['id']!=n['id']:
    pair=(n['id'],other['id'],'原文显式引用')
    if pair not in seen:edges.append({'source':n['id'],'target':other['id'],'kind':pair[2],'evidence':n['path']+' · Markdown链接'});seen.add(pair)
   elif not other:pending.append({'source':n['id'],'target':target,'reason':'未在本导航范围' if p.exists() else '原文链接目标待核'})
 for i,j in [(16,17),(18,19),(20,21),(22,23),(24,25)]:
  a=next(n for n in nodes if n['path'].startswith(KB+f'{i:02}-'));b=next(n for n in nodes if n['path'].startswith(KB+f'{j:02}-'))
  edges.append({'source':a['id'],'target':b['id'],'kind':'实验方案→配套结果（阅读编排）','evidence':'20261020知识库文档职责索引；不是自动推断的实现证明'})
 for n in nodes:n['preview_html']=render_markdown(n['body'],Path(n['source_path']),bypath)
 stats={'system':sum(n['group']=='system' for n in nodes),'database':sum(n['group']=='knowledge' for n in nodes),'documents':len(nodes),'reference':sum(n['group']=='history' for n in nodes),'relations':len(edges)}
 data={'revision':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat(),'model':'来源快照 · 非产品验收','groups':[{'id':i,'label':l,'color':c} for i,l,c in GROUPS],'subnames':SUB,'nodes':nodes,'edges':edges,'stats':stats}
 report={'ok':not missing,'missing_inputs':missing,'nodes':len(nodes),'relations':len(edges),'pending_links':len(pending),'unique_ids':len(byid)==len(nodes),'snapshot':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat(),'source_reading_scope':'目录、标题/正文/显式链接扫描与分类复核，非全文工程核准','generated_at':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
 return data,reg,ledger,pending,report

def render_markdown(text,source,bypath):
 def inline(s):
  # Escape before applying a small formatting subset; never render source HTML.
  s=html.escape(s)
  def lk(m):
   label,target=m[1],html.unescape(m[2]).strip('<>');u=urlsplit(target)
   if u.scheme not in ('','http','https'):return label+'（链接未启用）'
   if not u.scheme:
    p=Path(os.path.abspath(source.parent/unquote(u.path)));node=bypath.get(str(p))
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
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=ROOT);ap.add_argument('--check',action='store_true');args=ap.parse_args();out=args.output_dir.resolve();folder=out/'方案导航资料'
 data,reg,ledger,pending,report=build(out)
 if args.check:
  old=json.loads((folder/'文档图谱数据.json').read_text());current={(n['id'],n['sha256']) for n in data['nodes']};prior={(n['id'],n['sha256']) for n in old['nodes']};print(json.dumps({'ok':current==prior,'source_changes':len(current^prior),'scope':'只读来源指纹检查'},ensure_ascii=False));return 0 if current==prior else 1
 folder.mkdir(parents=True,exist_ok=True)
 template=(HERE/'导航模板.html').read_text();encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026');page=template.replace('__CAD_DATA__',encoded)
 assert '__CAD_DATA__' not in page
 target=out/'CAD方案文档地图.html';tmp=folder/'navigation.tmp';tmp.write_text(page);tmp.replace(target)
 dump(folder/'文档图谱数据.json',data);dump(folder/'稳定节点ID.json',reg);dump(folder/'原文引用待核列表.json',pending)
 (folder/'来源阅读与分类台账.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in ledger)+'\n')
 report['artifact_sha256']=sha(target.read_bytes());dump(folder/'导航核查记录.json',report);print(json.dumps(report,ensure_ascii=False));return 0 if report['ok'] else 1
if __name__=='__main__':sys.exit(main())
