import os
import tempfile
import unittest
from pathlib import Path
from app import Batch, save_batch, list_batches, get_batch, parse_pdf, update_batch, delete_batch, summarize_batches, BatchSummaryRequest, connect_history, append_orders, AppendOrdersRequest
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


    def test_summary_selection_dates_and_timezone(self):
        a=save_batch(Batch(**self.sample()))
        other=self.sample();other['name']='Outro lote';other['orders'][0]['items'][0]['quantity']=7
        b=save_batch(Batch(**other))
        c=save_batch(Batch(**self.sample()))
        with connect_history() as con:
            con.execute('UPDATE batches SET created_at=? WHERE id=?',('2026-11-11T02:59:00+00:00',a['id']))
            con.execute('UPDATE batches SET created_at=? WHERE id=?',('2026-11-11T03:00:00+00:00',b['id']))
        report=summarize_batches(BatchSummaryRequest(batch_ids=[a['id'],b['id'],a['id']]))
        self.assertEqual(report['batch_count'],2)
        self.assertEqual(report['quantity'],16)
        self.assertEqual(report['order_count'],2)
        self.assertEqual({b['id'] for b in report['batches']},{a['id'],b['id']})
        report=summarize_batches(BatchSummaryRequest(batch_ids=[a['id']],start_date='2026-11-10',end_date='2026-11-10'))
        self.assertEqual(report['quantity'],5)
        with self.assertRaises(HTTPException): summarize_batches(BatchSummaryRequest(batch_ids=[b['id']],end_date='2026-11-10'))
        with self.assertRaises(HTTPException): summarize_batches(BatchSummaryRequest(batch_ids=[a['id']],start_date='2026-11-11',end_date='2026-11-10'))
        with self.assertRaises(HTTPException): summarize_batches(BatchSummaryRequest(batch_ids=[a['id']],start_date='invalid'))
        delete_batch(a['id'])
        with self.assertRaises(HTTPException) as err: summarize_batches(BatchSummaryRequest(batch_ids=[a['id'],b['id']]))
        self.assertEqual(err.exception.status_code,409)


    def test_append_orders_preserves_batch_and_rejects_duplicate(self):
        a=save_batch(Batch(**self.sample()))
        order=self.sample()['orders'][0];order['order']='NEW-1'
        appended=append_orders(a['id'],AppendOrdersRequest(orders=[order]))
        self.assertEqual(len(appended['orders']),2)
        self.assertEqual(appended['created_at'],a['created_at'])
        self.assertEqual(appended['name'],a['name'])
        with self.assertRaises(HTTPException):append_orders(a['id'],AppendOrdersRequest(orders=[order]))
        self.assertEqual(len(get_batch(a['id'])['orders']),2)
        with self.assertRaises(HTTPException):append_orders('missing',AppendOrdersRequest(orders=[order]))
