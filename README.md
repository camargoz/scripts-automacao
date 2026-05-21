# Scripts de Automação — Kronoos

Coleção de notebooks Jupyter para consulta de dados jurídicos e empresariais via API local. Cada automação lê uma lista de documentos de um arquivo JSON, consulta os endpoints correspondentes, armazena cache por documento e exporta os resultados em `.xlsx` formatado.

---

## Pré-requisitos

**Python 3.9+** com os pacotes:

```bash
pip install requests pandas openpyxl
```

**API local rodando** nos endereços configurados em cada notebook (ver seção de cada automação).

---

## Estrutura de pastas

```
scripts-automacao/
├── input/                          # Arquivos de entrada (listas de documentos)
│   ├── processos_documentos.json
│   ├── get_partners_documentos.json
│   └── ubo_registration_documentos.json
├── notebooks/                      # Notebooks Jupyter
│   ├── processos-por-cpf.ipynb
│   ├── get-partners.ipynb
│   └── ubo-registration.ipynb
├── responses/                      # Gerado em runtime
│   ├── processos-por-cpf/
│   │   ├── relatorio_processos.xlsx
│   │   └── cache/
│   ├── get-partners/
│   │   ├── relatorio_consolidado.xlsx
│   │   └── cache/
│   └── ubo-registration/
│       ├── relatorio_ubo.xlsx
│       ├── erros_registro.txt
│       └── cache/
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

### 3. UBO Registration (`ubo-registration.ipynb`)

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
