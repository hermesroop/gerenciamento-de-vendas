# Fio a fio — Resumo de camisetas

Aplicativo web em português para extrair pedidos NEOCOOLER em PDF, conferir itens e consolidar quantidades por cor e tamanho (P, M, G, GG, G1, G2, G3). Permite exportar CSV e evita repetir o mesmo arquivo ou número de venda na sessão.

## Executar

Use Python 3.12 ou superior, na pasta deste repositório:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Abra a aplicação na porta 8000 pelo acesso web disponível no seu ambiente. Envie PDFs e confira cada item antes de produzir. A tabela só inclui itens com cor, tamanho e quantidade válidos; a exportação fica bloqueada enquanto houver itens incompletos ou documentos sem itens.

## Validar

```sh
python -m unittest discover -s tests -v
node --check static/app.js
```

O teste de integração usa os dois PDFs originais em `/workspace/attachments` quando disponíveis; caso contrário, é explicitamente pulado. Os arquivos dos clientes não são incorporados ao repositório.

## Limites da primeira versão

- Leitura baseada no modelo NEOCOOLER dos PDFs fornecidos; outros layouts precisam de validação e adaptação.
- PDFs de imagem precisam de OCR, ainda não implementado.
- Até 30 arquivos por envio, 10 MB e 100 páginas por arquivo.
- Sem banco de dados, contas ou histórico persistente. Recarregar a página apaga a sessão. Exporte o CSV para guardar o resultado.
- PDFs são processados em memória pelo servidor, sem armazenamento explícito em disco pelo aplicativo.
- Versão para desenvolvimento, sem autenticação: use em ambiente confiável. Não expor diretamente na internet como serviço público.
