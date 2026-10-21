#!/usr/bin/env python3
"""原始PDF文字/OCR/矢量交叉证据。无客户资料外发，不自动判规范违规。"""
import argparse,collections,hashlib,json,math,os,re,subprocess,tempfile,time
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/crosscheck_20261009'

def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
    with os.fdopen(fd,'w',encoding='utf-8') as fh:fh.write(json.dumps(x,ensure_ascii=False,indent=2))
    os.replace(tmp,p)

def norm(s):return re.sub(r'\s+','',s)
def point(p):return [round(p.x,6),round(p.y,6)]
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def bezier_length(pts,n=128):
    # 近似值：折线细分，不能冒充精确CAD圆弧长。
    prev=pts[0];length=0
    for i in range(1,n+1):
        t=i/n;u=1-t;q=[u**3*pts[0][j]+3*u*u*t*pts[1][j]+3*u*t*t*pts[2][j]+t**3*pts[3][j] for j in (0,1)]
        length+=dist(prev,q);prev=q
    return length

def path_record(path,idx):
    segments=[];subpaths=[];current=[]
    def flush():
        nonlocal current
        if current:
            subpaths.append({'segment_indices':current,'first':segments[current[0]]['start'],'last':segments[current[-1]]['end'],'geometric_closed':dist(segments[current[0]]['start'],segments[current[-1]]['end'])<=1e-4})
        current=[]
    for it in path['items']:
        kind=it[0]
        if kind in ('re','qu'):
            flush()
            pts=[point(x) for x in ([it[1].tl,it[1].tr,it[1].br,it[1].bl] if kind=='re' else [it[1].ul,it[1].ur,it[1].lr,it[1].ll])]
            for a,b in zip(pts,pts[1:]+pts[:1]):
                current.append(len(segments));segments.append({'type':'l','start':a,'end':b,'length_pt':dist(a,b),'origin':kind})
            flush();continue
        if kind not in ('l','c'):continue
        pts=[point(x) for x in it[1:]];a=pts[0];b=pts[-1]
        if current and dist(segments[current[-1]]['end'],a)>1e-4:flush()
        current.append(len(segments));seg={'type':kind,'start':a,'end':b,'length_pt':dist(a,b) if kind=='l' else bezier_length(pts),'length_method':'exact_line' if kind=='l' else 'bezier_128_chords'}
        if kind=='c':seg['control_points']=pts
        segments.append(seg)
    flush()
    # closePath只记录原操作；多子路径情况下不能推断所有子路径闭合。
    return {'index':idx,'bbox':list(path['rect']),'stroke_width_pt':path.get('width'),'paper_width_mm':path.get('width')*25.4/72 if path.get('width') is not None else None,'dashes':path.get('dashes'),'draw_type':path.get('type'),'fill':path.get('fill'),'stroke':path.get('color'),'closePath_operator':path.get('closePath'),'subpaths':subpaths,'segments':segments,'length_pt':sum(s['length_pt'] for s in segments),'implicit_closing_edge_pt':dist(subpaths[-1]['first'],subpaths[-1]['last']) if path.get('closePath') and subpaths else 0,'length_scope':'显式路径段之和；仅末子路径closePath边另列，不把填充闭合当轮廓闭合','warning':'绘制路径不是CAD实体；填充字形和箭头可能闭合；closePath不证明零件轮廓闭合。纸面pt/mm不等于零件尺寸。'}

def inventory():
    old=json.loads((ROOT/'evidence/source_inventory_20261008.json').read_text());known={x['sha256'] for x in old};allrows=[]
    for f in sorted((ROOT.parent/'国标').glob('*.pdf'))+sorted((ROOT.parent/'工程图审核').glob('*.pdf')):
        pages=[]
        with fitz.open(f) as d:
            for p in d:
                t=p.get_text();paths=p.get_drawings();pages.append({'page':p.number+1,'size_pt':list(p.rect),'rotation':p.rotation,'text_chars':len(t),'cjk_chars':len(re.findall(r'[\u4e00-\u9fff]',t)),'paths':len(paths),'images':len(p.get_images())})
            sha=hashlib.sha256(f.read_bytes()).hexdigest();row={'file':f.name,'path':str(f),'sha256':sha,'pages':len(d),'new_standard':f.parent.name=='国标' and sha not in known,'page_channels':pages};allrows.append(row)
            folder=OUT/'documents'/f.stem;folder.mkdir(parents=True,exist_ok=True)
            (folder/'text_layer.txt').write_text('\n'.join(f'===== PDF PAGE {i+1} =====\n'+p.get_text() for i,p in enumerate(d)))
    write(OUT/'inventory.json',allrows);return allrows

def miner_transformed_paths(filename):
    """PDFMiner独立读取每个paint_path的CTM，解决pdfplumber原始线宽未缩放。"""
    from pdfminer.converter import PDFPageAggregator
    from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
    from pdfminer.pdfpage import PDFPage
    class Device(PDFPageAggregator):
        def __init__(self,rsrc):
            super().__init__(rsrc);self.audit=[]
        def paint_path(self,gstate,stroke,fill,evenodd,path):
            before=len(self.cur_item._objs)
            super().paint_path(gstate,stroke,fill,evenodd,path)
            a,b,c,d,e,f=self.ctm; sx=math.hypot(a,b);sy=math.hypot(c,d)
            uniform=abs(sx-sy)<1e-8 and abs(a*c+b*d)<1e-8
            for item in self.cur_item._objs[before:]:
                self.audit.append({'bbox_bottom_origin':list(item.bbox),'raw_width':float(gstate.linewidth),'ctm':list(self.ctm),'uniform_scale':sx if uniform else None,'page_width_pt':float(gstate.linewidth)*sx if uniform else None,'stroke':stroke,'fill':fill,'kind':type(item).__name__})
    rsrc=PDFResourceManager();device=Device(rsrc);interpreter=PDFPageInterpreter(rsrc,device);pages=[]
    with open(filename,'rb') as fh:
        for page in PDFPage.get_pages(fh):
            device.audit=[];interpreter.process_page(page);layout=device.get_result()
            # 此次实图rotation均0；PDFMiner布局为左下原点，统一到左上。
            for x in device.audit:
                x0,y0,x1,y1=x.pop('bbox_bottom_origin');x['bbox']=[x0,layout.height-y1,x1,layout.height-y0]
            pages.append(device.audit)
    device.close();return pages

def vectors():
    import pdfplumber
    rows=[]
    for f in sorted((ROOT.parent/'工程图审核').glob('*.pdf')):
        miner_pages=miner_transformed_paths(f)
        with fitz.open(f) as d,pdfplumber.open(f) as other:
            for pi,p in enumerate(d):
                records=[path_record(x,i) for i,x in enumerate(p.get_drawings())];spans=[{'text':s['text'],'bbox':s['bbox'],'size':s['size']} for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
                op=other.pages[pi];objects=op.lines+op.rects+op.curves
                wa=collections.Counter(round(x['stroke_width_pt'],5) for x in records if x.get('stroke') is not None and x['stroke_width_pt'] is not None)
                wb=collections.Counter(round(float(x.get('linewidth',0)),5) for x in objects if x.get('stroke'))
                corrected=miner_pages[pi]
                wc=collections.Counter(round(x['page_width_pt'],5) for x in corrected if x['stroke'] and x['page_width_pt'] is not None)
                diff=[]
                # 比较每个plumber对象到MuPDF路径bbox、stroke width的最近值；两库拆路径粒度不同，不要求计数一致。
                for x in corrected:
                    bbox=x['bbox'];w=x['page_width_pt']
                    if w is None:
                        diff.append({'bbox':bbox,'warning':'非等比CTM，线宽需按方向分析，不能单标量比较'});continue
                    best=min((sum(abs(a-b) for a,b in zip(bbox,r['bbox']))+abs(w-(r['stroke_width_pt'] or 0)),r['index']) for r in records) if records else (None,None)
                    if best[0] is None or best[0]>.01:diff.append({'bbox':bbox,'linewidth':w,'closest_path':best[1],'combined_delta':best[0]})
                meta={'file':f.name,'page':pi+1,'coordinate_system':'PDF页面pt，左上角原点，MuPDF未旋转坐标；当前客户PDFrotation均0','page_size':list(p.rect),'rotation':p.rotation,'mupdf_paths':len(records),'pdfplumber_objects':len(objects),'mupdf_stroke_width_histogram':dict(wa),'pdfplumber_raw_width_histogram':dict(wb),'pdfminer_ctm_corrected_width_histogram':dict(wc),'ctm_correction_method':'PDFMiner实际paint_path CTM，等比缩放独立转换；非等比留待分析','bbox_width_unmatched_objects':len(diff),'diff_samples':diff[:30],'semantic_checked':False}
                write(OUT/'vectors'/f'{f.stem}_p{pi+1}.json',{'metadata':meta,'paths':records,'independent_pdfminer_paths':corrected,'text_spans':spans});rows.append(meta)
    write(OUT/'vector_summary.json',rows)

def raster_box_to_pdf(box,W,H,pdf_width,pdf_height,rotate=False):
    pts=box if isinstance(box[0],list) else [[box[0],box[1]],[box[2],box[3]]]
    pts=[[W-y,x] for x,y in pts] if rotate else pts
    return [min(x for x,y in pts)/W*pdf_width,min(y for x,y in pts)/H*pdf_height,max(x for x,y in pts)/W*pdf_width,max(y for x,y in pts)/H*pdf_height]

def ocr(engine='v4',dpi=180):
    import numpy as np
    if engine=='v5':
        from rapidocr import RapidOCR,OCRVersion,ModelType
        runner=RapidOCR(params={'EngineConfig.onnxruntime.intra_op_num_threads':2,'EngineConfig.onnxruntime.inter_op_num_threads':1,'Det.ocr_version':OCRVersion.PPOCRV5,'Det.model_type':ModelType.MOBILE,'Rec.ocr_version':OCRVersion.PPOCRV5,'Rec.model_type':ModelType.MOBILE,'Global.log_level':'warning'})
    else:
        from rapidocr_onnxruntime import RapidOCR
        runner=RapidOCR(intra_op_num_threads=2,inter_op_num_threads=1)
    inv=json.loads((OUT/'inventory.json').read_text());batch=json.loads((ROOT/'evidence/batch.json').read_text());requests={}
    for row in inv:
        f=Path(row['path'])
        if row['new_standard'] or f.parent.name=='工程图审核':requests[f]=list(range(1,row['pages']+1))
    for b in batch:requests.setdefault(Path(b['pdf']),[]).extend(b.get('context_pages',[b['page']]))
    # 经验候选与螺纹对照页
    for key,extra in [('4458.4',[4,11,12]),('4459.1',[3,4,5,6])]:
        f=next((ROOT.parent/'国标').glob('*'+key+'*.pdf'));requests.setdefault(f,[]).extend(extra)
    log=[]
    for f,numbers in requests.items():
        folder=OUT/'documents'/f.stem;folder.mkdir(parents=True,exist_ok=True)
        with fitz.open(f) as d:
            for no in sorted(set(numbers)):
                target=folder/f'p{no:03d}_{engine}.json';vision=folder/f'p{no:03d}_vision.json'
                if target.exists() and vision.exists():continue
                start=time.time();p=d[no-1];pix=p.get_pixmap(dpi=dpi,alpha=False);im=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n);W,H=pix.width,pix.height
                rotate=f.parent.name=='工程图审核'
                if rotate:im=np.rot90(im).copy()
                from PIL import Image
                imagefile=folder/f'p{no:03d}_render.png';Image.fromarray(im).save(imagefile)
                def bbox_to_pdf(box):return raster_box_to_pdf(box,W,H,p.rect.width,p.rect.height,rotate)
                if not target.exists():
                    if engine=='v5':
                        res=runner(im);raw=zip(res.boxes.tolist() if res.boxes is not None else [],res.txts or [],list(res.scores) if res.scores is not None else [])
                    else:raw=(runner(im)[0] or [])
                    rec=[{'text':t,'confidence':float(sc),'bbox_pt':bbox_to_pdf(np.asarray(box).tolist())} for box,t,sc in raw]
                    write(target,{'file':f.name,'page':no,'engine':engine,'dpi':dpi,'render_rotation_ccw':90 if rotate else 0,'coordinate_system':'原PDF页左上角pt','status':'OK' if rec else 'EMPTY','records':rec})
                if not vision.exists():
                    try:
                        result=subprocess.run(['/tmp/cad_vision_ocr',str(imagefile)],capture_output=True,text=True,timeout=45);v=json.loads(result.stdout.strip().splitlines()[-1]);vr=[{'text':x['text'],'confidence':x['confidence'],'bbox_pt':bbox_to_pdf(x['bbox'])} for x in v.get('records',[])];write(vision,{'file':f.name,'page':no,'engine':'Apple Vision','revision':v.get('revision'),'dpi':dpi,'render_rotation_ccw':90 if rotate else 0,'status':('EMPTY' if not vr and v.get('status')=='OK' else v.get('status')),'records':vr,'reason':v.get('reason')})
                    except Exception as ex:write(vision,{'file':f.name,'page':no,'status':'ERROR','reason':str(ex),'records':[]})
                # 图像留关键页，长文件原页仍随页渲染缓存可核查。
                log.append({'file':f.name,'page':no,'seconds':round(time.time()-start,3)});print(f'{f.name[:20]} p{no} {log[-1]["seconds"]}s',flush=True)
        for eng in (engine,'vision'):
            chunks=[]
            for no in sorted(set(numbers)):
                jp=folder/f'p{no:03d}_{eng}.json'
                if jp.exists():chunks.append(f'===== PDF PAGE {no} =====\n'+'\n'.join(x['text'] for x in json.loads(jp.read_text()).get('records',[])))
            (folder/f'{eng}_text.txt').write_text('\n'.join(chunks))
    write(OUT/f'ocr_run_{engine}.json',{'engine':engine,'dpi':dpi,'requests':{str(k):sorted(set(v)) for k,v in requests.items()},'processed_this_run':log})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['inventory','vectors','ocr']);ap.add_argument('--engine',default='v4');ap.add_argument('--dpi',type=int,default=180);a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if a.action=='inventory':inventory()
    elif a.action=='vectors':vectors()
    else:ocr(a.engine,a.dpi)
