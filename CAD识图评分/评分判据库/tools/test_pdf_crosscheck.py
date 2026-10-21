"""几何/CTM反例自测，不检测客户图违规。"""
import unittest,tempfile
from pathlib import Path
import fitz
from pdf_crosscheck import path_record,miner_transformed_paths,bezier_length,raster_box_to_pdf
class Checks(unittest.TestCase):
 def rec(self,items,close=False):return path_record({'items':items,'rect':fitz.Rect(0,0,10,10),'width':2,'closePath':close,'type':'s','color':(0,0,0)},0)
 def test_line(self):
  r=self.rec([('l',fitz.Point(0,0),fitz.Point(3,4))]);self.assertEqual(r['length_pt'],5);self.assertFalse(r['subpaths'][0]['geometric_closed'])
 def test_rect(self):
  r=self.rec([('re',fitz.Rect(0,0,3,4),1)]);self.assertEqual(r['length_pt'],14);self.assertTrue(r['subpaths'][0]['geometric_closed'])
 def test_separate_subpaths(self):
  r=self.rec([('l',fitz.Point(0,0),fitz.Point(3,4)),('l',fitz.Point(8,8),fitz.Point(9,9))],True)
  self.assertEqual(len(r['subpaths']),2);self.assertFalse(r['subpaths'][0]['geometric_closed']);self.assertAlmostEqual(r['implicit_closing_edge_pt'],2**.5)
 def test_curve(self):
  self.assertAlmostEqual(bezier_length([[0,0],[1,0],[2,0],[3,0]]),3)
 def test_zero_width(self):
  d=fitz.open();p=d.new_page();p.draw_line((1,1),(5,5));x=p.get_contents()[0];d.update_stream(x,b'q 0 w 1 1 m 5 5 l S Q');self.assertEqual(p.get_drawings()[0]['width'],0);d.close()
 def test_ctm(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'test.pdf';d=fitz.open();p=d.new_page(width=100,height=100);p.draw_line((10,10),(50,50),width=2);xref=p.get_contents()[0];d.update_stream(xref,b'q 0.75 0 0 0.75 0 0 cm\n'+d.xref_stream(xref)+b'\nQ');d.save(f);d.close()
   x=miner_transformed_paths(f)[0][0];self.assertEqual(x['raw_width'],2);self.assertAlmostEqual(x['page_width_pt'],1.5)
   with fitz.open(f) as d:self.assertAlmostEqual(d[0].get_drawings()[0]['width'],x['page_width_pt']);self.assertAlmostEqual(x['bbox'][0],7.5)
 def test_nonuniform_ctm(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'test.pdf';d=fitz.open();p=d.new_page();p.draw_line((1,1),(5,5));x=p.get_contents()[0];d.update_stream(x,b'q 2 0 0 1 0 0 cm\n'+d.xref_stream(x)+b'\nQ');d.save(f);d.close();self.assertIsNone(miner_transformed_paths(f)[0][0]['page_width_pt'])
 def test_scan_no_vector(self):
  d=fitz.open();p=d.new_page();pix=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,10,10));pix.clear_with(255);p.insert_image(p.rect,stream=pix.tobytes('png'));self.assertEqual(p.get_drawings(),[]);d.close()
 def test_rotation_coord(self):
  self.assertEqual(raster_box_to_pdf([70,160,80,170],200,300,100,150,True),[15,35,20,40])
  self.assertEqual(raster_box_to_pdf([[20,40],[30,40],[30,60],[20,60]],200,300,100,150),[10,20,15,30])
if __name__=='__main__':unittest.main()
