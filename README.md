# Scripts de Automação — Kronoos

Coleção de notebooks Jupyter para consulta de dados jurídicos e empresariais via API local. Cada automação lê uma lista de documentos de um arquivo JSON, consulta os endpoints correspondentes, armazena cache por documento e exporta os resultados em `.xlsx` formatado.

---

## Pré-requisitos

**Python 3.9+** com os pacotes:

```bash
pip install requests pandas openpyxl pymongo
```

**API local rodando** nos endereços configurados em cada notebook (ver seção de cada automação).

---

## Estrutura de pastas

```
scripts-automacao/
├── input/                          # Arquivos de entrada (listas de documentos)
│   ├── processos_documentos.json
│   ├── get_partners_documentos.json
│   ├── ubo_registration_documentos.json
│   └── teste_resumo_ia_escavador_processos.json
├── notebooks/                      # Notebooks Jupyter
│   ├── processos-por-cpf.ipynb
│   ├── get-partners.ipynb
│   ├── ubo-registration.ipynb
│   ├── teste-resumo-ia-escavador.ipynb
│   └── metricas-processos-por-documento.ipynb
├── responses/                      # Gerado em runtime
│   ├── processos-por-cpf/
│   │   ├── relatorio_processos.xlsx
│   │   └── cache/
│   ├── get-partners/
│   │   ├── relatorio_consolidado.xlsx
│   │   └── cache/
│   ├── ubo-registration/
│   │   ├── relatorio_ubo.xlsx
│   │   ├── erros_registro.txt
│   │   └── cache/
│   ├── teste-resumo-ia-escavador/
│   │   ├── relatorio_metricas_resumo_ia.xlsx
│   │   └── cache/
│   └── metricas-processos-por-documento/
│       └── relatorio_metricas_processos_por_documento.xlsx
└── examples/                       # Exemplos de resposta da API
```

---

## Formato de input

Todos os arquivos de entrada seguem o mesmo padrão JSON:

```json
[
    { "nome": "Nome da Pessoa ou Empresa", "documento": "000.000.000-00" },
    { "nome": "Outra Empresa Ltda", "documento": "00.000.000/0001-00" }
]
```

- `nome`: rótulo de referência que aparece no Excel como primeira coluna
- `documento`: CPF ou CNPJ — pode ser com ou sem formatação (pontos, barras, traços)

---

## Cache

Todas as automações armazenam o resultado de cada consulta em `responses/<script>/cache/<documento_limpo>.json`, onde `<documento_limpo>` contém apenas os dígitos do documento (ex: `00107100860.json`).

Em execuções subsequentes, se o arquivo de cache existir, a chamada à API é ignorada e o dado é lido do disco. Para forçar uma nova consulta, basta apagar o arquivo de cache correspondente.

---

## Automações

### 1. Processos por CPF (`processos-por-cpf.ipynb`)

Busca processos judiciais para cada CPF na lista de entrada.

**API:** `http://localhost:3003` — endpoint `/processos-por-documento`

**Input:** `input/processos_documentos.json`

**Como usar:**
1. Preencha `input/processos_documentos.json` com os CPFs desejados
2. Abra `notebooks/processos-por-cpf.ipynb` no Jupyter
3. Execute todas as células (`Run All`)

**Output:** `responses/processos-por-cpf/relatorio_processos.xlsx`

| Aba | Conteúdo |
|---|---|
| Com Processos | Uma linha por processo encontrado, com todos os detalhes |
| Sem Processos | Documentos consultados que não possuem processos |

**Colunas (aba Com Processos):**

| Coluna | Cor | Descrição |
|---|---|---|
| Nome | Amarelo | Nome do input |
| CPF Consultado | Amarelo | Documento pesquisado |
| Número do Processo | Azul | Identificador único do processo |
| Tribunal / Órgão Julgador / Instância / Sistema | Azul | Dados de localização do processo |
| Área / Segmento / Ramo do Direito / Classe / Assuntos Principais | Laranja | Classificação jurídica |
| Status / Data de Distribuição | Verde | Situação e timeline |
| Valor da Causa (R$) | Roxo | Valor formatado em BRL |
| Juiz / Total de Partes / Partes / URL do Processo | Azul-claro | Dados administrativos |

---

### 2. Get Partners (`get-partners.ipynb`)

Consulta dados cadastrais e quadro societário de empresas (CNPJs).

**API:** `http://localhost:3003` — endpoints `/registration` e `/business-participation`

**Input:** `input/get_partners_documentos.json`

**Como usar:**
1. Preencha `input/get_partners_documentos.json` com os CNPJs desejados
2. Abra `notebooks/get-partners.ipynb` no Jupyter
3. Execute todas as células (`Run All`)

**Output:** `responses/get-partners/relatorio_consolidado.xlsx`

| Aba | Conteúdo |
|---|---|
| Empresas | Uma linha por CNPJ com dados cadastrais e contagem de sócios ativos |
| Sócios Ativos | Uma linha por sócio ativo (com nome e documento) |
| Erros ou Inválidos | Documentos que falharam na consulta |

**Colunas (aba Empresas):**

| Coluna | Cor | Descrição |
|---|---|---|
| Nome / Documento | Amarelo | Identificação do input |
| Razão Social / Nome Fantasia | Azul | Dados cadastrais da empresa |
| Telefones / Emails / CNAE | Laranja | Contato e atividade econômica |
| Status da Empresa | Verde | Situação fiscal (Ativa, Baixada, etc.) |
| Qtd Sócios Ativos | Cinza | Total de sócios com status ativo |

**Colunas (aba Sócios Ativos):**

| Coluna | Cor | Descrição |
|---|---|---|
| Nome | Amarelo | Nome do input (empresa consultada) |
| Documento Empresa | Azul | CNPJ da empresa |
| Documento do Sócio / Nome do Sócio | Roxo | Dados do sócio ativo |

> Sócios com status `inativo` ou `inativa` são filtrados automaticamente.

---

### 3. Teste de Performance — Resumo Inteligente IA (`teste-resumo-ia-escavador.ipynb`)

Testa as 3 chamadas da API de "Resumo Inteligente de Processos (IA)" do **escavador.com** contra uma lista de números de processo, medindo tempo de resposta e quantidade de verificações de status até o resumo ficar pronto. Objetivo: gerar métricas para a equipe decidir se continua com esse distribuidor.

**API:** `https://api.escavador.com/api/v2` — endpoints `POST .../ia/resumo/solicitar-atualizacao`, `GET .../ia/resumo/status` e `GET .../ia/resumo`

**Input:** `input/teste_resumo_ia_escavador_processos.json` (campos `numero_processo` — dígitos, com ou sem formatação CNJ — e `descricao`)

**Como usar:**
1. Preencha `input/teste_resumo_ia_escavador_processos.json` com os números de processo desejados
2. Ajuste `TOKEN` na primeira célula do notebook, se necessário
3. Abra `notebooks/teste-resumo-ia-escavador.ipynb` no Jupyter e execute todas as células (`Run All`)

**Output:** `responses/teste-resumo-ia-escavador/relatorio_metricas_resumo_ia.xlsx`

| Aba | Conteúdo |
|---|---|
| Métricas por Processo | Uma linha por processo: tempos de cada etapa, quantidade de verificações de status, sinal (✅/⚠️) e erros |
| Estatísticas Agregadas | Contagens, tempo médio/mediano/mín/máx/desvio-padrão e uma recomendação textual automática |

> A coluna **Tempo até Finalizado (s)** é a métrica-chave: acima de 10s (configurável em `BAD_SIGNAL_THRESHOLD_SEG`) é marcada como "⚠️ Mau sinal" e destacada em vermelho na planilha.
>
> A API do Escavador não permite regenerar o resumo de um mesmo processo mais de uma vez em 24h sem novas movimentações — nesse caso o notebook não conta como erro, apenas registra `JA_ATUALIZADO` e busca o conteúdo já existente (sem medir tempo de geração). Para medir o tempo real de geração é preciso testar processos que ainda não tiveram resumo solicitado nas últimas 24h, ou aguardar esse intervalo.

---

### 4. UBO Registration (`ubo-registration.ipynb`)

Identifica os beneficiários finais (UBOs — Ultimate Beneficial Owners) de empresas.

**API:** `http://localhost:3000` — endpoint `/dados-gerais` (requer autenticação via login)

> Esta automação usa autenticação por Bearer Token. As credenciais estão configuradas na primeira célula do notebook. A consulta é assíncrona: o notebook cria uma ordem e faz polling até receber o resultado (até 15 tentativas com intervalo de 2s).

**Input:** `input/ubo_registration_documentos.json`

**Como usar:**
1. Preencha `input/ubo_registration_documentos.json` com os CNPJs desejados
2. Certifique-se de que a API em `localhost:3000` está rodando
3. Abra `notebooks/ubo-registration.ipynb` no Jupyter
4. Execute todas as células (`Run All`)

**Output:** `responses/ubo-registration/relatorio_ubo.xlsx` e `responses/ubo-registration/erros_registro.txt`

| Arquivo | Conteúdo |
|---|---|
| `relatorio_ubo.xlsx` | Aba única "Relatório UBO" com uma linha por sócio por empresa |
| `erros_registro.txt` | Log de documentos que falharam, com o motivo |

**Colunas:**

| Coluna | Cor | Descrição |
|---|---|---|
| Nome | Amarelo | Nome do input |
| Business CNPJ / Business Name / Business Address | Azul | Dados da empresa |
| Registration Status / Entity Type | Verde | Situação e natureza jurídica |
| List of UBOs / UBOs Ownership (%) | Laranja | Relação e participação dos sócios |
| UBO Name / UBO Tax ID | Roxo | Identificação do sócio individual |
| UBO Address / Tax Status / Phone / Date of Birth | Cinza | Campos coletados mas ainda não preenchidos pela API |

---

### 5. Métricas Processos por Documento (`metricas-processos-por-documento.ipynb`)

Consulta direto no MongoDB (coleção `requisicaoapis`, banco `kronoos`) quantos
pedidos do serviço `ProcessosPorDocumento` foram feitos no ano corrente e
quantos retornaram 1000 ou mais itens no total — um sinal de CPF/CNPJ com
volume atípico de processos. Diferente das outras automações, não depende de
nenhuma API nem de arquivo de input: a fonte é só o banco.

> Quando a resposta de um pedido tem muitos itens, a API salva o resultado em
> vários documentos (lotes) com o mesmo `id_pedido` em vez de um só. O notebook
> agrupa por `id_pedido` e soma os itens de todos os lotes antes de comparar
> com o limiar de 1000 — um pedido com 10 lotes de 1000 itens cada conta como
> 1 pedido com 10.000 itens, não como 10 buscas de 1000.

**Banco:** MongoDB (`requisicaoapis`, coleção do banco `kronoos`) — string de
conexão configurável via variável de ambiente `MONGO_URI` (tem um valor padrão
já configurado na primeira célula do notebook).

**Como usar:**
1. Abra `notebooks/metricas-processos-por-documento.ipynb` no Jupyter
2. Execute todas as células (`Run All`) — a consulta agregada pode levar
   alguns minutos, pois a coleção tem milhões de documentos

**Output:** `responses/metricas-processos-por-documento/relatorio_metricas_processos_por_documento.xlsx`

| Aba | Conteúdo |
|---|---|
| Resumo Geral | Total de pedidos (`id_pedido` distintos) no ano, quantidade e % com 1000+ itens somando todos os lotes |
| Pedidos com 1000+ Itens | Uma linha por `id_pedido` que somou 1000+ itens entre todos os seus lotes, com o total de itens, a quantidade de lotes e a data da primeira busca |
