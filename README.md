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
- Lotes salvos são persistidos em SQLite local; pedidos ainda não salvos são perdidos ao recarregar. Não há contas nem sincronização entre computadores.
- PDFs são processados em memória; o histórico guarda apenas os dados conferidos dos pedidos, não os PDFs originais.
- Versão para desenvolvimento, sem autenticação: use em ambiente confiável. Não expor diretamente na internet como serviço público.


## Histórico de lotes

1. Envie os PDFs e confira o número do pedido, o cliente, as cores, tamanhos e quantidades. Os campos podem ser corrigidos antes de salvar.
2. Dê um nome ao lote e clique em **Salvar lote no histórico**. Dados incompletos impedem salvar.
3. O lote recebe data e hora de criação automaticamente. A tela mostra horário de Brasília.
4. Após salvar, a conferência é limpa para o próximo lote. O lote salvo é uma cópia definitiva: alterações em novos pedidos não modificam o histórico.
5. Em **Histórico de produção**, clique em **Abrir lote** para ver os pedidos separados, com o resumo geral ao final. Use **Imprimir / Salvar PDF** e escolha o destino no navegador.

O histórico fica em `data/historico.sqlite3`, dentro da pasta do aplicativo no computador que executa o servidor. Não é enviado ao GitHub. Faça backup da pasta `data` com o aplicativo fechado. Ao atualizar o código, mantenha essa pasta no mesmo local: baixar e abrir uma pasta nova não transfere seu histórico automaticamente. É possível escolher outro caminho com a variável `CAMISETAS_DB`.

### Atualizar no Windows

Feche o servidor com Ctrl+C. Baixe a versão atual no GitHub e copie `app.py`, `requirements.txt`, a pasta `static` e as instruções para a pasta onde você já usa o aplicativo. Preserve `.venv` e principalmente `data`. Depois execute, nessa pasta:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

No navegador, abra o endereço local e pressione Ctrl+F5 para carregar a interface atualizada.
