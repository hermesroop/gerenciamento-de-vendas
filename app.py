from pathlib import Path
from io import BytesIO
import hashlib
import re
import unicodedata
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

ROOT = Path(__file__).parent
app = FastAPI(title='Resumo de camisetas')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
SIZES = ['P', 'M', 'G', 'GG', 'G1', 'G2', 'G3']
COLORS = {'AZUL MARINHO': 'Azul-marinho', 'AZUL ROYAL': 'Azul royal', 'VERDE': 'Verde', 'BRANCA': 'Branca', 'BRANCO': 'Branca', 'PRETA': 'Preta', 'PRETO': 'Preta', 'VERMELHA': 'Vermelha', 'VERMELHO': 'Vermelha', 'AMARELA': 'Amarela', 'AMARELO': 'Amarela', 'CINZA': 'Cinza', 'ROSA': 'Rosa', 'LARANJA': 'Laranja', 'AZUL': 'Azul', 'BEGE': 'Bege', 'ROXA': 'Roxa', 'ROXO': 'Roxa'}

def parse_pdf(data: bytes, filename: str):
    reader = PdfReader(BytesIO(data))
    if len(reader.pages) > 100:
        raise ValueError('Limite de 100 páginas por PDF.')
    text = '\n'.join(p.extract_text(extraction_mode='layout') or '' for p in reader.pages)
    order = re.search(r'Venda\s+(\d+)', text, re.I)
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
    return dict(filename=filename, order=order.group(1) if order else '', id=hashlib.sha256(data).hexdigest(), items=items, warnings=list(dict.fromkeys(warnings)))

@app.get('/')
def index():
    return FileResponse(ROOT / 'static/index.html')

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
