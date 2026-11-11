import os
import tempfile
import unittest
from pathlib import Path
from app import Batch, save_batch, list_batches, get_batch, parse_pdf, update_batch, delete_batch
from fastapi import HTTPException
from pydantic import ValidationError

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get('CAMISETAS_DB')
        os.environ['CAMISETAS_DB'] = str(Path(self.temp.name) / 'history.sqlite3')

    def tearDown(self):
        if self.previous is None:
            os.environ.pop('CAMISETAS_DB', None)
        else:
            os.environ['CAMISETAS_DB'] = self.previous
        self.temp.cleanup()

    def sample(self):
        return {'name':'Lote novembro','orders':[{'order':'11499','customer':'Jair','items':[{'color':'Verde','size':'M','quantity':1},{'color':'Branca','size':'GG','quantity':4}]}]}

    def test_saved_snapshot_survives_new_connection(self):
        data=self.sample()
        record=save_batch(Batch(**data))
        data['orders'][0]['items'][0]['quantity']=999
        restored=get_batch(record['id'])
        self.assertEqual(restored['orders'][0]['items'][0]['quantity'],1)
        self.assertEqual(restored['orders'][0]['customer'],'Jair')
        self.assertEqual(list_batches()[0]['quantity'],5)
        self.assertIn('+00:00',restored['created_at'])
        self.assertEqual(restored['name'],'Lote novembro')

    def test_invalid_and_duplicate_orders(self):
        d=self.sample();d['orders'][0]['items'][0]['quantity']=-1
        with self.assertRaises(ValidationError): Batch(**d)
        d=self.sample();d['orders'].append(d['orders'][0])
        with self.assertRaises(HTTPException): save_batch(Batch(**d))
        self.assertEqual(list_batches(),[])

    def test_missing_batch(self):
        with self.assertRaises(HTTPException) as err: get_batch('missing')
        self.assertEqual(err.exception.status_code,404)

    def test_customer_names_in_original_pdfs(self):
        root=Path('/workspace/attachments')
        expected={'11499':'Jair Pahohek kracheski','11525':'White serviços de informática e acabamentos em geral'}
        for number,name in expected.items():
            p=next(root.rglob('*'+number+'*'),None)
            if p is None: self.skipTest('Anexos não disponíveis')
            self.assertEqual(parse_pdf(p.read_bytes(),p.name)['customer'],name)


    def test_edit_and_delete_persist(self):
        original=save_batch(Batch(**self.sample()))
        data=self.sample();data['name']='Lote corrigido'
        data['orders'][0]['customer']='Cliente corrigido'
        data['orders'][0]['items'][0]['quantity']=8
        updated=update_batch(original['id'],Batch(**data))
        self.assertEqual(updated['created_at'],original['created_at'])
        self.assertIn('updated_at',updated)
        self.assertEqual(get_batch(original['id'])['orders'][0]['customer'],'Cliente corrigido')
        self.assertEqual(list_batches()[0]['quantity'],12)
        invalid=self.sample();invalid['name']=' '
        with self.assertRaises(HTTPException): update_batch(original['id'],Batch(**invalid))
        self.assertEqual(get_batch(original['id'])['name'],'Lote corrigido')
        delete_batch(original['id'])
        self.assertEqual(list_batches(),[])
        with self.assertRaises(HTTPException): get_batch(original['id'])
        with self.assertRaises(HTTPException): delete_batch(original['id'])
        with self.assertRaises(HTTPException): update_batch(original['id'],Batch(**data))
