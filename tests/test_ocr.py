import shutil
from pathlib import Path
import unittest
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from ocr import parse_order_text, read_image

BARCO='Barco\n2 branca p\n2 marinho p\n1 branca m\n1 marinho m\n2 brancas g\n2 marinho g Editada 10:43'
NEO='neocooler\ntodas azul\np 6\nm 8\ng 10\ngg 12\ng1 4\ng2 4\n15:32'

class OCRTests(unittest.TestCase):
    def test_examples_text(self):
        a=parse_order_text(BARCO,'barco.png');b=parse_order_text(NEO,'neo.png')
        self.assertEqual(a['customer'],'Barco')
        self.assertEqual(b['customer'],'neocooler')
        self.assertEqual(sum(i['quantity'] for i in a['items']),10)
        self.assertEqual(sum(i['quantity'] for i in b['items']),44)
        self.assertTrue(all(i['color']=='Azul-marinho' for i in b['items']))
        self.assertEqual([i['size'] for i in b['items']],['P','M','G','GG','G1','G2'])
        self.assertEqual(a['order'],'')
        self.assertFalse(b['reviewed'])

    def test_incomplete_and_unrecognized_lines(self):
        r=parse_order_text('Cliente: José\nPedido 123\np 6\ntexto estranho 9','print.png')
        self.assertEqual(r['customer'],'José')
        self.assertEqual(r['order'],'123')
        self.assertEqual(r['items'][0]['color'],'')
        self.assertTrue(any('não interpretadas' in w for w in r['warnings']))
        self.assertFalse(parse_order_text('sem pedido legível','x')['items'])

    @unittest.skipUnless(shutil.which('tesseract'),'Tesseract não disponível')
    def test_real_ocr_pipeline(self):
        # Synthetic fixtures reflect supplied messages; original inline images are not local files.
        for text,expected in [(BARCO,10),(NEO,44)]:
            image=Image.new('RGB',(500,420),'white')
            draw=ImageDraw.Draw(image)
            font_path=next((p for p in [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('C:/Windows/Fonts/arial.ttf')] if p.is_file()),None)
            if font_path is None:self.skipTest('Fonte de teste não disponível')
            font=ImageFont.truetype(str(font_path),23)
            draw.multiline_text((20,20),text,font=font,fill='black',spacing=10)
            data=BytesIO();image.save(data,format='PNG')
            result=read_image(data.getvalue(),'fixture.png')
            self.assertEqual(sum(i['quantity'] for i in result['items']),expected,result)

    def test_bad_image(self):
        with self.assertRaises(ValueError):read_image(b'not an image','bad.png')
