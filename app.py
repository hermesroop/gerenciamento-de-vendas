from pathlib import Path
from io import BytesIO
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel, Field
import re
import unicodedata
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

ROOT = Path(__file__).parent
app = FastAPI(title='Neocooler - Gerenciamento de Produção Externa')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
SIZES = ['P', 'M', 'G', 'GG', 'G1', 'G2', 'G3']
COLORS = {'AZUL MARINHO': 'Azul-marinho', 'AZUL ROYAL': 'Azul royal', 'VERDE': 'Verde', 'BRANCA': 'Branca', 'BRANCO': 'Branca', 'PRETA': 'Preta', 'PRETO': 'Preta', 'VERMELHA': 'Vermelha', 'VERMELHO': 'Vermelha', 'AMARELA': 'Amarela', 'AMARELO': 'Amarela', 'CINZA': 'Cinza', 'ROSA': 'Rosa', 'LARANJA': 'Laranja', 'AZUL': 'Azul', 'BEGE': 'Bege', 'ROXA': 'Roxa', 'ROXO': 'Roxa'}

def parse_pdf(data: bytes, filename: str):
    reader = PdfReader(BytesIO(data))
    if len(reader.pages) > 100:
        raise ValueError('Limite de 100 páginas por PDF.')
    text = '\n'.join(p.extract_text(extraction_mode='layout') or '' for p in reader.pages)
    order = re.search(r'Venda\s+(\d+)', text, re.I)
    customer_matches = list(re.finditer(r'(?m)^([^\n]+)\n\s*(?:CPF|CNPJ):', text.split('Produto/Serviço')[0]))
    customer_match = customer_matches[-1] if customer_matches else None
    customer = re.split(r'\s{3,}', customer_match.group(1).strip())[0] if customer_match else ''
    items, warnings = [], []
    # Each sale row begins with quantity and a SKU. Continuation lines contain the size.
    chunks = re.split(r'(?m)^\s*(\d+)\s+(?=[A-Za-z][\w-]*\s+-)', text)
    for i in range(1, len(chunks), 2):
        qty, body = int(chunks[i]), chunks[i + 1]
        body = re.split(r'\n\s*(?:Total\s|Frete\s|Valor líquido|Condição de pagamento|Página)', body)[0]
        normalized = unicodedata.normalize('NFKD', body.upper()).encode('ascii', 'ignore').decode()
        if 'CAMISETA' not in normalized:
            warnings.append('Um item que não é camiseta foi ignorado. Confira o PDF original.')
            continue
        sizes = re.findall(r'\bNEO\s+(G[123]|GG|P|M|G)\b', normalized)
        if not sizes:
            sizes = re.findall(r'\b(G[123]|GG|P|M|G)\b', normalized)
        color = next((v for k, v in COLORS.items() if re.search(r'\b' + k + r'\b', normalized)), '')
        size = sizes[-1] if sizes else ''
        description = ' '.join(body.split())
        items.append(dict(color=color, size=size, quantity=qty, description=description))
        if not color or not size:
            warnings.append('Há item com cor ou tamanho não identificado. Preencha antes de exportar.')
    if not items:
        warnings.append('Nenhuma camiseta identificada. Este formato pode não ser compatível ou o PDF pode precisar de OCR.')
    return dict(filename=filename, order=order.group(1) if order else '', customer=customer, id=hashlib.sha256(data).hexdigest(), items=items, warnings=list(dict.fromkeys(warnings)))

@app.get('/')
def index():
    return FileResponse(ROOT / 'static/index.html')

@app.get('/lotes')
def history_page():
    return FileResponse(ROOT / 'static/lotes.html')

@app.post('/api/parse')
async def parse(files: list[UploadFile] = File(...)):
    if len(files) > 30:
        raise HTTPException(400, 'Envie até 30 PDFs por vez.')
    results = []
    for file in files:
        data = await file.read(10 * 1024 * 1024 + 1)
        if len(data) > 10 * 1024 * 1024:
            results.append(dict(filename=file.filename, error='Arquivo excede 10 MB.'))
            continue
        try:
            if not data.startswith(b'%PDF-'):
                raise ValueError('Arquivo não é um PDF válido.')
            results.append(parse_pdf(data, file.filename or 'Pedido.pdf'))
        except Exception as exc:
            message = str(exc) if isinstance(exc, ValueError) else 'Não foi possível ler o PDF. Verifique se está protegido ou danificado.'
            results.append(dict(filename=file.filename, error=message))
    return results


class Item(BaseModel):
    color: str = Field(min_length=1, max_length=100)
    size: Literal['P', 'M', 'G', 'GG', 'G1', 'G2', 'G3']
    quantity: int = Field(strict=True, gt=0, le=1000000)

class Order(BaseModel):
    order: str = Field(min_length=1, max_length=100)
    customer: str = Field(min_length=1, max_length=300)
    filename: str = Field(default='', max_length=500)
    items: list[Item] = Field(min_length=1, max_length=5000)

class Batch(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    orders: list[Order] = Field(min_length=1, max_length=500)


def connect_history():
    path = Path(os.environ.get('CAMISETAS_DB', str(ROOT / 'data' / 'historico.sqlite3')))
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS batches (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)')
    return con


def batch_record(row):
    return dict(id=row['id'], created_at=row['created_at'], **json.loads(row['payload']))


@app.post('/api/batches', status_code=201)
def save_batch(batch: Batch):
    payload = batch.model_dump()
    payload['name'] = payload['name'].strip()
    numbers = set()
    for order in payload['orders']:
        for key in ['order', 'customer']:
            order[key] = order[key].strip()
        if not order['order'] or not order['customer'] or order['order'] in numbers:
            raise HTTPException(400, 'Preencha cliente e número de cada pedido, sem pedidos repetidos no lote.')
        numbers.add(order['order'])
        for item in order['items']:
            item['color'] = item['color'].strip()
            if not item['color']:
                raise HTTPException(400, 'Preencha a cor de cada camiseta.')
    if not payload['name']:
        raise HTTPException(400, 'Informe um nome para o lote.')
    record = dict(id=uuid4().hex, created_at=datetime.now(timezone.utc).isoformat(), **payload)
    with connect_history() as con:
        con.execute('INSERT INTO batches VALUES (?, ?, ?)', (record['id'], record['created_at'], json.dumps(payload, ensure_ascii=False)))
    return record


@app.get('/api/batches')
def list_batches():
    with connect_history() as con:
        rows = con.execute('SELECT * FROM batches ORDER BY created_at DESC').fetchall()
    return [dict(id=r['id'], created_at=r['created_at'], name=(p := json.loads(r['payload']))['name'], order_count=len(p['orders']), quantity=sum(i['quantity'] for o in p['orders'] for i in o['items'])) for r in rows]


@app.get('/api/batches/{batch_id}')
def get_batch(batch_id: str):
    with connect_history() as con:
        row = con.execute('SELECT * FROM batches WHERE id=?', (batch_id,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Lote não encontrado.')
    return batch_record(row)
