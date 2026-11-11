"""Local OCR and interpretation of short clothing orders."""
import hashlib
from io import BytesIO
import os
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata
from PIL import Image, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 16000000

def normalize(text):
    return unicodedata.normalize('NFKD', text.upper()).encode('ascii', 'ignore').decode()

def color_of(text):
    text = normalize(text)
    for pattern, color in [(r'AZUL\s+ROYAL','Azul royal'), (r'AZUL(?:[ -]+MARINHO)?|MARINHO','Azul-marinho'), (r'BRANC[AO]S?','Branca'), (r'PRET[AO]S?','Preta'), (r'VERDES?','Verde'), (r'VERMELH[AO]S?','Vermelha'), (r'CINZA','Cinza'), (r'AMAREL[AO]S?','Amarela'), (r'ROSA','Rosa'), (r'LARANJA','Laranja'), (r'ROX[AO]S?','Roxa'), (r'BEGE','Bege')]:
        if re.search(r'\b(?:'+pattern+r')\b', text):
            return color
    return ''

def parse_order_text(text, filename, data=b''):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    global_colors = [color_of(line) for line in lines if re.search(r'\bTOD[AO]S?\b', normalize(line))]
    global_color = global_colors[0] if global_colors and len(set(global_colors)) == 1 else ''
    items, unknown, customer, order = [], [], '', ''
    size_pattern = r'(G[123]|GG|P|M|G)'
    for line in lines:
        clean = normalize(line)
        number = re.search(r'\b(?:PEDIDO|VENDA)\s*[:#-]?\s*(\d+)\b', clean)
        if number:
            order = number.group(1)
            continue
        if re.search(r'\bTOD[AO]S?\b', clean) and color_of(line):
            continue
        # WhatsApp timestamps and edit markers are metadata, not quantities.
        if re.fullmatch(r'(?:EDITAD[AO]\s*)?\d{1,2}:\d{2}', clean):
            continue
        clean = re.sub(r'\s+EDITAD[AO].*$', '', clean)
        a = re.fullmatch(r'(\d+)\s+(.+?)\s+'+size_pattern, clean)
        b = re.fullmatch(size_pattern+r'\s*[:xX-]?\s*(\d+)', clean)
        if a:
            qty, color, size = int(a[1]), color_of(a[2]), a[3]
        elif b:
            size, qty, color = b[1], int(b[2]), global_color
        else:
            if not customer and not items and not re.search(r'\d', clean):
                customer = re.sub(r'^CLIENTE\s*:\s*', '', line, flags=re.I)
            else:
                unknown.append(line)
            continue
        items.append(dict(color=color, size=size, quantity=qty, description=line))
    warnings = ['Leitura automática de print: confira cliente, cores, tamanhos e quantidades antes de salvar.']
    if unknown:
        warnings.append('Linhas não interpretadas: '+ ' | '.join(unknown))
    if not items:
        warnings.append('Nenhuma camiseta identificada. Corrija o texto lido e tente novamente.')
    if any(not i['color'] or i['quantity'] < 1 for i in items):
        warnings.append('Há itens incompletos. Preencha a cor e confira as quantidades.')
    return dict(id=hashlib.sha256(data or text.encode()).hexdigest(),filename=filename,order=order,customer=customer,items=items,warnings=warnings,source='image',reviewed=False,ocr_text=text)

def read_image(data, filename):
    executable = os.environ.get('TESSERACT_CMD') or shutil.which('tesseract')
    if not executable:
        candidate = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Tesseract-OCR' / 'tesseract.exe'
        if candidate.is_file():
            executable = str(candidate)
    if not executable:
        raise ValueError('Para ler prints, instale o Tesseract OCR no Windows e reinicie o aplicativo. Consulte o README. A leitura de PDFs continua disponível.')
    try:
        with Image.open(BytesIO(data)) as original:
            if original.format not in ('PNG', 'JPEG', 'WEBP'):
                raise ValueError('Envie imagens PNG, JPG ou WEBP.')
            if original.width * original.height > 16000000:
                raise ValueError('A imagem deve ter no máximo 16 milhões de pixels.')
            image = ImageOps.exif_transpose(original).convert('RGB')
            factor = min(3, 3000 / max(image.size))
            if factor > 1:
                image = image.resize((round(image.width*factor),round(image.height*factor)))
            output = BytesIO()
            image.save(output, format='PNG')
        result = subprocess.run([executable, 'stdin', 'stdout', '-l', 'eng', '--psm', '6'], input=output.getvalue(), capture_output=True, timeout=45, check=False)
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('Imagem inválida ou grande demais. Envie um print menor em PNG ou JPG.')
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('O OCR não conseguiu processar a imagem. Confira a instalação ou envie um print menor.')
    if result.returncode:
        raise ValueError('Falha no Tesseract OCR. Confira a instalação e os dados do idioma inglês (eng).')
    return parse_order_text(result.stdout.decode('utf-8', errors='replace'), filename, data)
