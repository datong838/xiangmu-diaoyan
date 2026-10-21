# -*- coding: utf-8 -*-
"""HTTP regression tests using temporary documents, never original data."""
from pathlib import Path
import hashlib, importlib.util, json, sys, tempfile, threading, unittest
from urllib.request import urlopen
from urllib.error import HTTPError
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('cad_reader_server', HERE/'预览服务.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        (cls.root/'方案导航资料').mkdir()
        cls.original = server.ROOT
        server.ROOT = cls.root
        texts = {'cad-main': '# 阅读样例\n\n|名称|说明|\n|---|---|\n|标题|[下一份](next.md)|\n\n<script>alert(1)</script>\n',
                 'cad-next': '# 下一份\n\n下一份正文',
                 'cad-long': '# 完整文档\n\n'+'长段落。'*30000+'\n\n全文末尾标记'}
        nodes = []
        for key, text in texts.items():
            filename = 'next.md' if key == 'cad-next' else key+'.md'
            p = cls.root/filename
            p.write_text(text)
            nodes.append({'id':key,'source_path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'path':filename,'title':filename})
        cls.pdf = b'%PDF-1.4\nPDF-fixture'
        p = cls.root/'fixture.pdf';p.write_bytes(cls.pdf)
        nodes.append({'id':'cad-pdf','source_path':str(p),'sha256':hashlib.sha256(cls.pdf).hexdigest(),'path':'fixture.pdf','title':'PDF'})
        cls.raw = (cls.root/'cad-main.md').read_bytes()
        (cls.root/'方案导航资料/文档图谱数据.json').write_text(json.dumps({'nodes':nodes}))
        (cls.root/'CAD方案文档地图.html').write_text('<html>map</html>')
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.worker = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.worker.start()
        cls.base = 'http://127.0.0.1:'+str(cls.http.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.worker.join()
        server.ROOT = cls.original;cls.tmp.cleanup()
    def get(self, route):
        with urlopen(self.base+route) as response:
            return response.headers.get_content_type(), response.read()
    def test_formatted_html_has_titles_and_table(self):
        kind, body = self.get('/source/cad-main')
        text = body.decode()
        self.assertEqual(kind, 'text/html');self.assertIn('<table>', text);self.assertIn('<h2>阅读样例</h2>',text)
        self.assertIn('max-width:1240px',text)
    def test_registered_links_stay_in_full_reader(self):
        _, body = self.get('/source/cad-main')
        self.assertIn('href="/source/cad-next"',body.decode())
        self.assertNotIn('data-preview-doc=',body.decode())
    def test_raw_bytes_remain_exact(self):
        kind, body = self.get('/raw/cad-main')
        self.assertEqual(kind,'text/plain');self.assertEqual(body,self.raw)
    def test_full_text_not_truncated(self):
        _, body = self.get('/source/cad-long')
        self.assertIn('全文末尾标记',body.decode());self.assertGreater(len(body.decode()),100000)
    def test_source_html_is_escaped(self):
        _, body = self.get('/source/cad-main')
        self.assertNotIn('<script>',body.decode());self.assertIn('&lt;script&gt;',body.decode())
    def test_pdf_content_and_type_unchanged(self):
        kind, body = self.get('/source/cad-pdf')
        self.assertEqual(kind,'application/pdf');self.assertEqual(body,self.pdf)
    def test_unknown_and_arbitrary_path_denied(self):
        for route in ['/source/not-registered','/../../etc/passwd','/raw/cad-main/extra']:
            with self.assertRaises(HTTPError) as error:self.get(route)
            self.assertEqual(error.exception.code,404)
    def test_changed_source_is_rejected(self):
        p = self.root/'next.md';old=p.read_bytes()
        try:
            p.write_text('changed')
            for route in ['/source/cad-next','/raw/cad-next']:
                with self.assertRaises(HTTPError) as error:self.get(route)
                self.assertEqual(error.exception.code,409)
        finally:p.write_bytes(old)
    def test_home_and_source_navigation_present(self):
        _, body = self.get('/source/cad-main')
        self.assertIn('href="/#doc=cad-main"',body.decode());self.assertIn('href="/raw/cad-main"',body.decode())
        kind, body = self.get('/')
        self.assertEqual(body,b'<html>map</html>')

if __name__ == '__main__':unittest.main(verbosity=2)
