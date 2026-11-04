import unittest
from pathlib import Path
from app import parse_pdf

class ParserTests(unittest.TestCase):
    def test_real_orders(self):
        root = Path('/workspace/attachments')
        paths = [next(root.rglob('*11499*'), None), next(root.rglob('*11525*'), None)]
        if not all(paths):
            self.skipTest('PDFs de exemplo não disponíveis nesta máquina')
        orders = [parse_pdf(p.read_bytes(), p.name) for p in paths]
        self.assertEqual([d['order'] for d in orders], ['11499', '11525'])
        self.assertTrue(all(not d['warnings'] for d in orders))
        actual = {}
        for d in orders:
            for i in d['items']:
                key = (i['color'], i['size'])
                actual[key] = actual.get(key, 0) + i['quantity']
        self.assertEqual(actual, {('Verde','M'):1,('Verde','G'):2,('Verde','GG'):2,('Branca','G'):1,('Branca','GG'):4,('Azul-marinho','M'):3,('Azul-marinho','G'):7,('Azul-marinho','GG'):5})
        self.assertEqual(sum(actual.values()),25)

if __name__ == '__main__':
    unittest.main()
