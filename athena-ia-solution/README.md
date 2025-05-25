# Projeto Athena IA - MVP

## Objetivo

O Projeto Athena é uma solução de Inteligência Artificial desenhada para auxiliar estudantes que se preparam para concursos públicos na área de controle (como TCU e CGU). O objetivo principal é gerar prompts de estudo personalizados a partir do conteúdo de editais, ajudando os usuários a focarem em suas lacunas de conhecimento.

Esta é a versão Mínima Viável (MVP) do projeto, focada em fornecer a funcionalidade central de backend e API.

## Funcionalidades (MVP)

*   **Extração de Tópicos do Edital**: A API pode analisar o texto de um edital e sugerir tópicos relevantes.
*   **Geração de Prompts de Estudo Personalizados**: Com base no edital e nas lacunas de conhecimento informadas pelo usuário, a API gera sugestões de estudo.
*   **API Backend**: Um backend em Python (Flask) que expõe endpoints para as funcionalidades acima.

## Estrutura do Projeto

```
athena-ia-solution/
├── backend/
│   ├── app.py                # Aplicação Flask principal
│   ├── models/
│   │   └── bert_model.py     # Lógica de geração de prompts (simplificada no MVP)
│   ├── utils/
│   │   └── text_processor.py # Utilitários para processamento de texto
│   └── requirements.txt      # Dependências Python
├── .github/
│   └── workflows/
│       └── main.yml          # Placeholder para CI/CD
└── README.md                 # Este arquivo
```

## Configuração e Execução do Backend Localmente

1.  **Pré-requisitos**:
    *   Python 3.8 ou superior
    *   `pip` (gerenciador de pacotes Python)
    *   Opcional: `virtualenv` para criar um ambiente virtual

2.  **Clone o repositório (se aplicável) ou crie a estrutura de pastas e arquivos conforme descrito.**

3.  **Crie e Ative um Ambiente Virtual (Recomendado)**:
    ```bash
    python -m venv venv
    # No Windows
    venv\Scripts\activate
    # No macOS/Linux
    source venv/bin/activate
    ```

4.  **Instale as Dependências**:
    Navegue até a pasta `backend` e execute:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute a Aplicação Flask**:
    Ainda na pasta `backend`, execute:
    ```bash
    python app.py
    ```
    A API estará rodando em `http://127.0.0.1:5000` por padrão.

    *   **Endpoint de Saúde**: `GET http://127.0.0.1:5000/health`
    *   **Endpoint de Extração de Tópicos**: `POST http://127.0.0.1:5000/extract_topics`
    *   **Endpoint de Geração de Prompts**: `POST http://127.0.0.1:5000/generate_prompts`

## Integração com Glide (ou Outro Front-end)

Para integrar o backend Athena com uma interface no Glide (ou qualquer outro front-end que possa fazer requisições HTTP), você precisará configurar ações para chamar os endpoints da API.

**Substitua `[SEU_ENDPOINT_API]` pela URL base onde sua API Flask está hospedada (ex: `http://127.0.0.1:5000` para testes locais, ou a URL pública se você fizer deploy).**

### 1. Para POST /extract_topics:

*   **Ação no Glide**: Configure uma ação (ex: "Webhook", "Fetch JSON" ou "Custom Action", dependendo das funcionalidades do Glide) para ser acionada quando o usuário inserir o texto do edital.
*   **Método**: `POST`
*   **URL**: `[SEU_ENDPOINT_API]/extract_topics`
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "edital_content": "TEXTO_DO_EDITAL_AQUI"
    }
    ```
    Onde `"TEXTO_DO_EDITAL_AQUI"` é o conteúdo do edital fornecido pelo usuário no Glide.
*   **Resposta Esperada (JSON)**:
    ```json
    {
      "topics": ["tópico1", "tópico2", ...]
    }
    ```
*   **No Glide**: Configure o Glide para receber esta lista de tópicos e exibi-los ao usuário (ex: em uma lista, para que ele possa identificar suas lacunas de conhecimento).

### 2. Para POST /generate_prompts:

*   **Ação no Glide**: Configure outra ação que será acionada após o usuário identificar suas lacunas de conhecimento.
*   **Método**: `POST`
*   **URL**: `[SEU_ENDPOINT_API]/generate_prompts`
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "edital_content": "TEXTO_DO_EDITAL_AQUI",
      "knowledge_gaps": ["lacuna1_selecionada", "lacuna2_digitada"]
    }
    ```
    Onde `"TEXTO_DO_EDITAL_AQUI"` é o conteúdo do edital e `["lacuna1_selecionada", ...]` é a lista de lacunas de conhecimento do usuário.
*   **Resposta Esperada (JSON)**:
    ```json
    {
      "prompts": ["prompt de estudo 1", "prompt de estudo 2", ...]
    }
    ```
*   **No Glide**: Configure o Glide para receber esta lista de prompts e exibi-los ao usuário (ex: como flashcards, em uma lista detalhada, etc.).

### Exemplo de Fluxo no Glide (Narrativa para o Usuário):

1.  **Usuário insere o texto do edital** no app Glide.
2.  Glide envia este texto para a API `/extract_topics`.
3.  API retorna uma **lista de tópicos identificados** (simplificado no MVP).
4.  Usuário **seleciona/digita suas lacunas de conhecimento** no Glide com base nos tópicos ou em seu próprio conhecimento.
5.  Glide envia o texto do edital e as lacunas selecionadas para a API `/generate_prompts`.
6.  API retorna os **prompts de estudo personalizados**.
7.  Glide **exibe esses prompts** para o usuário.

## Modelo de IA e Simplificações no MVP

*   **Modelo de IA Simplificado**: Para este MVP, a funcionalidade de "extração de tópicos" e "geração de prompts" é implementada de forma simplificada (`backend/models/bert_model.py` e `backend/utils/text_processor.py`). Utilizamos técnicas básicas de processamento de linguagem natural (como análise de frequência de palavras e correspondência de palavras-chave) em vez de um modelo BERT completo.
*   **Evolução Futura**: A intenção é evoluir o projeto para integrar um modelo BERT mais sofisticado (possivelmente treinado ou ajustado com dados específicos de editais e materiais de estudo) para melhorar a qualidade e relevância dos tópicos e prompts gerados. Isso exigiria um volume de dados de treinamento e infraestrutura de Machine Learning (ML) mais robusta.

## Funcionalidades Futuras (Não Incluídas no MVP)

*   Integração com banco de dados para persistir informações de usuários ou editais.
*   Autenticação e autorização de usuários.
*   Módulo de métricas de sucesso para acompanhar o progresso do estudo.
*   Treinamento e deploy de um modelo BERT completo para processamento de linguagem natural avançado.
*   Interface de administração para gerenciar conteúdos ou configurações.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.
```
