# Neocooler - Gerenciamento de Produção Externa

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
- Prints PNG/JPG/WEBP são lidos por OCR; PDFs digitalizados ainda não são reconhecidos.
- Até 30 arquivos por envio, 10 MB por arquivo, 100 páginas por PDF e 16 milhões de pixels por imagem.
- Lotes salvos são persistidos em SQLite local; pedidos em conferência são mantidos temporariamente na mesma aba do navegador. Não há contas nem sincronização entre computadores.
- PDFs são processados em memória; o histórico guarda apenas os dados conferidos dos pedidos, não os PDFs originais.
- Versão para desenvolvimento, sem autenticação: use em ambiente confiável. Não expor diretamente na internet como serviço público.


## Histórico de lotes

1. Envie os PDFs e confira o número do pedido, o cliente, as cores, tamanhos e quantidades. Os campos podem ser corrigidos antes de salvar.
2. Dê um nome ao lote e clique em **Salvar lote no histórico**. Dados incompletos impedem salvar.
3. O lote recebe data e hora de criação automaticamente. A tela mostra horário de Brasília.
4. Após salvar, a conferência é limpa para o próximo lote. O lote salvo é uma cópia independente: alterações em novos pedidos não modificam o histórico. Edições explícitas do lote podem ser feitas na janela de detalhes.
5. No botão **Lotes salvos** do cabeçalho, abra a página de histórico e clique em **Abrir lote** para ver os pedidos separados, com o resumo geral ao final. Use **Imprimir / Salvar PDF** e escolha o destino no navegador.

O histórico fica em `data/historico.sqlite3`, dentro da pasta do aplicativo no computador que executa o servidor. Não é enviado ao GitHub. Faça backup da pasta `data` com o aplicativo fechado. Ao atualizar o código, mantenha essa pasta no mesmo local: baixar e abrir uma pasta nova não transfere seu histórico automaticamente. É possível escolher outro caminho com a variável `CAMISETAS_DB`.

### Atualizar no Windows

Feche o servidor com Ctrl+C. Baixe a versão atual no GitHub e copie `app.py`, `requirements.txt`, a pasta `static` e as instruções para a pasta onde você já usa o aplicativo. Preserve `.venv` e principalmente `data`. Depois execute, nessa pasta:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

No navegador, abra o endereço local e pressione Ctrl+F5 para carregar a interface atualizada.


## Navegação e identidade visual

A página inicial (`/`) contém apenas o preparo e a conferência do novo lote. O botão **Lotes salvos** abre `/lotes`, com o histórico e os relatórios. Ao salvar um lote, o aplicativo abre seu relatório nessa página. O botão **Novo lote** retorna ao preparo. A conferência em andamento é mantida na mesma aba durante a navegação, mas só **Salvar lote no histórico** grava uma cópia permanente no banco de dados.

A interface usa preto, branco e tons de cinza. O logo Neocooler e o favicon usam uma cópia do logo presente nos PDFs de exemplo, em `static/neocooler-logo.jpg`. Não requer serviços de imagem ou fontes externos.

Nesta atualização, substitua `app.py` e toda a pasta `static` (incluindo os novos arquivos `shared.js`, `lotes.js`, `lotes.html` e o logo). Preserve a pasta `data`. Reinicie o servidor e atualize o navegador com Ctrl+F5.


## Editar e excluir lotes

Em **Lotes salvos**, clique em **Abrir lote**. O relatório abre em uma janela sobre a lista, com rolagem própria, impressão e fechamento pelo botão **Fechar** ou pela tecla Esc.

- **Editar lote**: permite alterar nome do lote, número do pedido, cliente, cores, tamanhos e quantidades. **Salvar alterações** grava no banco e recalcula os totais. A data de criação é mantida e a última edição é registrada. **Cancelar edição** descarta as alterações após confirmação.
- **Excluir lote**: pede confirmação antes de excluir definitivamente o lote. A lista é atualizada após a operação. Faça backup da pasta `data` se precisar preservar uma cópia antes de excluir.

Para instalar esta atualização no Windows, encerre o servidor, substitua `app.py` e toda a pasta `static`, preserve `data`, reinicie e pressione Ctrl+F5 no navegador. Não há novas dependências.

## Resumo de vários lotes

Na página **Lotes salvos**:

1. Informe a data inicial e/ou final e clique em **Buscar por período**. A pesquisa usa a data de criação do lote, incluindo os dois dias completos no horário de Brasília. Deixe as datas vazias para consultar todo o histórico.
2. Marque os lotes desejados ou clique em **Selecionar todos os resultados**. O contador informa lotes, pedidos e camisetas selecionados. **Limpar seleção** desmarca todos. Ao mudar o período, lotes que ficam fora do filtro são desmarcados automaticamente.
3. Clique em **Gerar resumo dos selecionados**. Uma janela mostra a data de geração, o período aplicado, os lotes incluídos, seus pedidos com clientes e itens, um resumo por lote e o resumo geral por cor/tamanho.
4. Use **Imprimir / Salvar PDF** para guardar ou enviar o relatório. A geração não altera nem cria lotes no histórico. O relatório usa os dados atuais; para preservar o registro de um envio antes de edições futuras, guarde o PDF gerado.

Pedidos presentes em vários lotes são somados em cada ocorrência, pois podem representar envios diferentes. O relatório avisa sobre números de pedido repetidos para permitir conferência. Cada lote selecionado entra apenas uma vez. Um lote excluído durante a seleção causa aviso para atualizar a lista, sem gerar um relatório incompleto.

A data filtrada é a criação do lote, não a data de venda do PDF nem a última edição. Não há status de envio ou data de envio separada nesta versão. A seleção e o filtro desta consulta não são salvos ao sair da página.

## Importar prints (PNG, JPG ou WEBP)

O botão **Selecionar PDFs ou prints** aceita os dois tipos no mesmo envio. A leitura de imagens é local, sem serviço pago ou envio a um provedor de OCR. São aceitos os formatos dos exemplos:

```text
Barco
2 branca p
2 marinho p
1 branca m
```

```text
Neocooler
todas azul
p 6
m 8
g 10
gg 12
g1 4
g2 4
```

**Azul** e **marinho** são normalizados para **Azul-marinho**. A linha “todas azul” aplica essa cor às quantidades por tamanho. A primeira linha de nome é uma sugestão de cliente e deve ser conferida. Horários e “Editada” não são quantidades. Outros formatos podem exigir correção.

Após a leitura, confira todos os campos e marque **Conferi todos os dados deste print**. Informe um número de pedido manualmente se ele não aparecer na imagem (por exemplo, uma referência interna única). Em **Conferir ou corrigir o texto do print**, é possível corrigir o texto e clicar em **Interpretar texto corrigido**; isso exige nova conferência. Linhas não interpretadas geram aviso para evitar omissões silenciosas. OCR pode errar mesmo em itens que parecem completos; a conferência é obrigatória antes de salvar/exportar.

### Instalação no Windows

1. Instale o **Tesseract OCR**. A documentação do projeto indica os instaladores Windows da Universidade de Mannheim: https://tesseract-ocr.github.io/tessdoc/Installation.html e https://github.com/UB-Mannheim/tesseract/wiki . Use o instalador da arquitetura do seu Windows, mantendo o idioma inglês (`eng`).
2. O caminho padrão `C:\Program Files\Tesseract-OCR\tesseract.exe` é detectado automaticamente. Para outro local, configure a variável `TESSERACT_CMD` com o caminho completo do executável antes de iniciar o aplicativo.
3. Atualize `app.py`, **`ocr.py`**, `requirements.txt` e a pasta `static`. Preserve a pasta `data`.
4. No terminal da pasta do aplicativo execute:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Depois pressione Ctrl+F5 no navegador. Se o Tesseract não estiver instalado, o app informa o problema ao importar imagens; PDFs com texto continuam funcionando. Em Linux, instale os pacotes `tesseract-ocr` e `tesseract-ocr-eng` pelo gerenciador do sistema.

Limites: 30 arquivos por envio, 10 MB por arquivo e 16 milhões de pixels por imagem. Apenas prints com texto legível; não há suporte a escrita à mão ou OCR de PDFs digitalizados. O texto OCR é temporário na aba; o histórico guarda os pedidos conferidos, não as imagens originais.

## Adicionar pedidos a lotes existentes

Na tela inicial, importe PDFs/prints e confira os pedidos normalmente (incluindo o número do pedido e a confirmação de OCR). Em **Adicionar a um lote existente**, escolha o destino e clique em **Adicionar pedidos ao lote selecionado**. Todos os pedidos em conferência serão acrescentados, sem substituir os que já estavam no lote. Não é necessário preencher um nome de lote novo. Números de pedido repetidos no mesmo lote impedem toda a inclusão, sem salvar parcialmente ou limpar os pedidos da tela. Após sucesso, a conferência é limpa e o relatório do lote atualizado é aberto.

Na janela **Editar lote**, use **Adicionar pedido** para preencher manualmente o número, cliente e itens. **Adicionar camiseta** e **Remover item** permitem ajustar as linhas. **Excluir pedido** retira o pedido da edição após confirmação. O resumo da edição acompanha as quantidades. Essas alterações só entram no histórico ao clicar em **Salvar alterações**; cancelar descarta todas. É necessário manter pelo menos um pedido e uma camiseta por pedido. Para remover um lote inteiro, use **Excluir lote**.

A inclusão preserva nome e data original do lote e atualiza a data de última edição. O filtro de datas continua considerando a criação do lote, não a data em que os novos pedidos foram acrescentados. O limite é de 500 pedidos por lote.

## Conferência, pedidos manuais e texto

Os pedidos da tela inicial aparecem em modo de consulta. Ao lado de **Remover**, **Editar** abre os campos e os botões **Adicionar Item** e **Remover Item**. **Concluir edição** aplica os dados ao resumo; **Cancelar edição** descarta as alterações daquele pedido. Enquanto algum pedido está em edição, o salvamento, a inclusão em outro lote e a exportação ficam bloqueados. Cada pedido precisa de número, cliente e ao menos um item válido para concluir.

- **Adicionar Pedido** cria um pedido manual em edição, com uma linha inicial. Preencha os campos e clique em **Concluir edição**.
- **Adicionar via Texto** abre a caixa para colar/digitar o cliente, o número e os itens, uma informação por linha. **Interpretar Texto** transforma o texto em um pedido para conferência. Exemplo:

```text
Barco
Pedido 123
2 branca p
2 marinho g
```

Também é aceito “todas azul” seguido das linhas “p 6”, “m 8”, etc. Texto digitado não exige Tesseract. Confira a interpretação e marque **Conferi todos os dados deste pedido**. Se faltar informação ou houver item não interpretado, use **Editar**; o texto original pode ser corrigido e reinterpretado dentro da edição. O botão **Cancelar** da caixa de novo texto mantém o conteúdo digitado até sair da página.

Os nomes **Adicionar Item** e **Remover Item** são usados tanto na conferência inicial como em **Editar lote**. Nesta atualização, substitua toda a pasta `static`, reinicie o aplicativo e pressione Ctrl+F5. Preserve `data` e os demais arquivos do servidor.

## Avisos e confirmações

As ações de salvar, acrescentar pedidos, excluir e descartar alterações usam janelas internas com **Confirmar** e **Cancelar**, seguindo o visual do aplicativo. Esc cancela a confirmação; o foco inicial fica em Cancelar. Essas janelas também funcionam sobre a janela de detalhes do lote. Não são usados `alert`, `confirm` ou `prompt` nativos do navegador.

Mensagens de resultado e de validação continuam próximas aos controles e também aparecem como avisos dispensáveis, que somem após 10 segundos. O botão **Fechar aviso** permite removê-los antes. Esses avisos não bloqueiam a tela e não aparecem na impressão.

Para atualizar esta versão, substitua toda a pasta `static` e pressione Ctrl+F5 no navegador. Não há novas dependências nem alterações no banco de dados.
