"""Focused tests of registered read-only navigation; temporary fixtures only."""
import hashlib, importlib.util, json, sys, tempfile, threading, unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import 生成导航 as gen
spec=importlib.util.spec_from_file_location('nav3d_server',HERE/'预览服务.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args):return None

class ReaderTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
  (cls.root/'方案导航资料').mkdir();(cls.root/'材料').mkdir()
  cls.a=cls.root/'a.md';cls.a.write_text('# 长文\n\n| 项目 | 值 |\n|---|---|\n| 孔径 | 10 |\n\n[下一篇](b.md)\n\n[二维依据](two.md)\n\n<script>BAD()</script>\n\n'+'正文'*60000+'\n尾部可见')
  cls.b=cls.root/'b.md';cls.b.write_text('# 第二篇')
  cls.j=cls.root/'材料/x.json';cls.j.write_text('{"design_only":true}')
  def n(id,p,kind='markdown'):
   return {'id':id,'source_path':str(p),'title':id,'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None,'source_kind':kind}
  cls.nodes=[n('cad3-a',cls.a),n('cad3-b',cls.b),n('cad3-dir',cls.root/'材料','directory'),n('cad3-json',cls.j,'attachment'),{'id':'cad3-two','source_path':str(cls.root/'two.md'),'source_kind':'external','href':'http://127.0.0.1:8842/#doc=cad-example','title':'二维原文'}]
  (cls.root/'三维方案文档地图.html').write_text('<h1>三维方案文档地图</h1>')
  (cls.root/'方案导航资料/文档图谱数据.json').write_text(json.dumps({'nodes':cls.nodes}))
  cls.oldroot=server.ROOT;server.ROOT=cls.root
  cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
  cls.url='http://127.0.0.1:'+str(cls.http.server_port)
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.thread.join();server.ROOT=cls.oldroot;cls.temp.cleanup()
 def get(self,path):return urlopen(self.url+path,timeout=3)
 def test_home(self):
  with self.get('/') as r:self.assertIn('三维方案文档地图',r.read().decode())
 def test_wide_reader_is_complete_and_keeps_internal_external_links(self):
  with self.get('/source/cad3-a') as r:
   body=r.read().decode();self.assertIn('text/html',r.headers['Content-Type']);self.assertIn('<table>',body);self.assertIn('尾部可见',body)
   self.assertIn('href="/source/cad3-b"',body);self.assertIn('http://127.0.0.1:8842/#doc=cad-example',body)
   self.assertNotIn('<script>BAD()',body);self.assertIn('&lt;script&gt;',body)
 def test_raw_bytes_unchanged(self):
  with self.get('/raw/cad3-a') as r:self.assertEqual(r.read(),self.a.read_bytes())
 def test_unknown_paths(self):
  for path in ['/source/missing','/etc/passwd','/source/../../etc/passwd','/raw/a.md']:
   with self.subTest(path=path):
    with self.assertRaises(HTTPError) as e:self.get(path)
    self.assertEqual(e.exception.code,404)
 def test_changed_source_409(self):
  original=self.b.read_bytes()
  try:
   self.b.write_text('changed')
   with self.assertRaises(HTTPError) as e:self.get('/source/cad3-b')
   self.assertEqual(e.exception.code,409)
  finally:self.b.write_bytes(original)
 def test_two_dimensional_redirect(self):
  with self.assertRaises(HTTPError) as e:build_opener(NoRedirect()).open(self.url+'/source/cad3-two')
  self.assertEqual(e.exception.code,302);self.assertEqual(e.exception.headers['Location'],'http://127.0.0.1:8842/#doc=cad-example')
 def test_registered_directory_and_json(self):
  with self.get('/source/cad3-dir') as r:self.assertIn('/source/cad3-json',r.read().decode())
  with self.get('/raw/cad3-json') as r:self.assertEqual(r.read(),self.j.read_bytes())

class GeneratorTests(unittest.TestCase):
 def test_current_corpus_and_relations(self):
  data,reg,ledger,pending,report=gen.build();self.assertTrue(report['ok'])
  ids={n['id'] for n in data['nodes']};self.assertEqual(len(ids),len(data['nodes']))
  self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in data['edges']))
  self.assertEqual({str(p) for p in gen.KB.glob('*.md')},{n['source_path'] for n in data['nodes'] if n['source_kind']=='markdown' and Path(n['source_path']).parent==gen.KB})
  external=[n for n in data['nodes'] if n['source_kind']=='external'];self.assertTrue(any(n['href']==gen.BASE2 for n in external))
  self.assertTrue(any('28-' in n['source_path'] for n in external))
  self.assertTrue(all(n['href'].startswith(gen.BASE2) and len(n['body'])<500 for n in external))
 def test_stable_ids_and_safe_rendering(self):
  first=gen.build()[0];second=gen.build()[0]
  self.assertEqual([(n['id'],n['sha256']) for n in first['nodes']],[(n['id'],n['sha256']) for n in second['nodes']])
  rendered=gen.render_markdown('<script>BAD()</script>\n[bad](javascript:alert(1))',Path('/tmp/x.md'),{})
  self.assertNotIn('<script>',rendered);self.assertNotIn('href="javascript:',rendered)

if __name__=='__main__':unittest.main()
