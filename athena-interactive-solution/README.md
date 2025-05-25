# Projeto Athena Interativo - MVP

## Objetivo

O Projeto Athena Interativo é uma solução de Inteligência Artificial (MVP) que permite aos usuários colar o texto de um edital de concurso público (foco inicial: área de controle) e receber sugestões de tópicos e prompts de estudo personalizados. Esta versão inclui um backend em Flask e um frontend interativo em Streamlit.

## Funcionalidades (MVP)

*   **Interface Interativa (Streamlit)**: Permite ao usuário colar o edital, extrair tópicos, selecionar lacunas de conhecimento e gerar prompts.
*   **Extração de Tópicos do Edital**: O backend API analisa o texto de um edital e sugere tópicos relevantes.
*   **Geração de Prompts de Estudo Personalizados**: Com base no edital e nas lacunas de conhecimento (selecionadas ou inseridas pelo usuário), a API gera sugestões de estudo.
*   **API Backend (Flask)**: Um backend em Python (Flask) que expõe endpoints para as funcionalidades de IA.

## Estrutura do Projeto

```
athena-interactive-solution/
├── backend/
│   ├── app.py                # Aplicação Flask principal
│   ├── models/
│   │   └── mock_bert_model.py# Lógica de geração de prompts (simplificada)
│   ├── utils/
│   │   └── text_processor.py # Utilitários para processamento de texto
│   └── requirements.txt      # Dependências Python do backend
├── frontend/
│   ├── app.py                # Aplicação Streamlit (interface do usuário)
│   └── requirements.txt      # Dependências Python do frontend
└── README.md                 # Este arquivo
```

## Rodando Localmente (Sem Docker)

Siga os passos abaixo para rodar o backend Flask e o frontend Streamlit em sua máquina local.

**Pré-requisitos**:
*   Python 3.8 ou superior
*   `pip` (gerenciador de pacotes Python)
*   Opcional: `virtualenv` ou `conda` para gerenciamento de ambientes virtuais.

### Passo 1: Rodar o Backend Flask

1.  **Navegue até a pasta do backend**:
    ```bash
    cd athena-interactive-solution/backend
    ```

2.  **(Opcional, mas recomendado) Crie e ative um ambiente virtual**:
    ```bash
    python -m venv venv_backend
    # No Windows:
    # venv_backend\Scripts\activate
    # No macOS/Linux:
    source venv_backend/bin/activate
    ```

3.  **Instale as dependências do backend**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute a aplicação Flask**:
    ```bash
    python app.py
    ```
    O backend Flask iniciará e estará escutando em `http://localhost:5000` (ou `http://127.0.0.1:5000`).
    Você deverá ver mensagens no console indicando que o servidor está rodando. Deixe este terminal aberto.

### Passo 2: Rodar o Front-end Streamlit

1.  **Abra um novo terminal.**

2.  **Navegue até a pasta do frontend**:
    ```bash
    cd athena-interactive-solution/frontend
    ```

3.  **(Opcional, mas recomendado) Crie e ative um ambiente virtual diferente para o frontend**:
    ```bash
    python -m venv venv_frontend
    # No Windows:
    # venv_frontend\Scripts\activate
    # No macOS/Linux:
    source venv_frontend/bin/activate
    ```

4.  **Instale as dependências do frontend**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute a aplicação Streamlit**:
    ```bash
    streamlit run app.py
    ```
    O Streamlit geralmente abrirá automaticamente uma nova aba no seu navegador web, apontando para `http://localhost:8501`. Se não abrir, acesse essa URL manualmente.

6.  **Interaja com a Aplicação**:
    *   Cole o texto de um edital na área designada.
    *   Clique em "Extrair Tópicos".
    *   Selecione os tópicos que representam suas lacunas de conhecimento na lista que aparecer.
    *   Opcionalmente, adicione mais lacunas manualmente no campo de texto.
    *   Clique em "Gerar Prompts de Estudo".
    *   Os prompts personalizados serão exibidos.

## Rodando com Docker e Docker Compose (Recomendado para Facilidade)

Se você tem Docker e Docker Compose instalados, você pode rodar ambos os serviços (backend e frontend) com um único comando. Esta é a maneira recomendada para simplificar a configuração e execução.

**Pré-requisitos**:
*   [Docker](https://docs.docker.com/get-docker/) instalado.
*   [Docker Compose](https://docs.docker.com/compose/install/) instalado (geralmente vem com o Docker Desktop).

**Passos para Execução**:

1.  **Navegue até a raiz do projeto `athena-interactive-solution`**:
    Certifique-se de que você está no diretório que contém o arquivo `docker-compose.yml`.
    ```bash
    cd caminho/para/seu/projeto/athena-interactive-solution
    ```

2.  **Construa e Inicie os Contêineres**:
    Execute o seguinte comando no seu terminal:
    ```bash
    docker-compose up --build
    ```
    *   `--build`: Este flag garante que as imagens Docker sejam construídas (ou reconstruídas se houverem alterações nos Dockerfiles ou no código).
    *   Este comando iniciará o backend Flask (acessível na porta 5000 do seu host) e o frontend Streamlit (acessível na porta 8501 do seu host).
    *   Você verá os logs de ambos os serviços no seu terminal.

3.  **Acesse a Aplicação**:
    Após os contêineres serem construídos e iniciados (pode levar alguns momentos na primeira vez), abra seu navegador e acesse:
    `http://localhost:8501`
    Isto o levará para a interface do Streamlit.

4.  **Interaja com a Aplicação**:
    Use a interface como descrito na seção "Como Interagir com a Solução (Localmente)". O frontend se comunicará com o backend que está rodando no outro contêiner.

5.  **Para Parar os Contêineres**:
    No terminal onde você executou `docker-compose up`, pressione `Ctrl+C`.
    Para garantir que os contêineres e redes sejam removidos (liberando as portas), você pode rodar:
    ```bash
    docker-compose down
    ```
    Isso para e remove os contêineres, redes e volumes definidos no `docker-compose.yml` (os volumes montados do seu código local não são afetados).

**Vantagens de usar Docker Compose**:
*   **Ambiente Consistente**: Garante que a aplicação rode da mesma forma, independentemente da sua configuração local de Python.
*   **Gerenciamento Simplificado**: Um único comando para iniciar e parar todos os serviços.
*   **Isolamento**: As dependências de cada serviço são isoladas dentro de seus respectivos contêineres.

## Modelo de IA e Simplificações no MVP

*   **Modelo de IA Simplificado**: Para este MVP, a funcionalidade de "extração de tópicos" e "geração de prompts" é implementada de forma simplificada (nos arquivos `backend/models/mock_bert_model.py` e `backend/utils/text_processor.py`). Utilizamos técnicas básicas de processamento de linguagem natural (como análise de frequência de palavras e correspondência de palavras-chave) em vez de um modelo BERT completo e treinado.
*   **Evolução Futura**: A intenção é evoluir o projeto para integrar um modelo BERT mais sofisticado (possivelmente treinado ou ajustado com dados específicos de editais e materiais de estudo, utilizando plataformas como a Vertex AI do Google Cloud) para melhorar significativamente a qualidade e relevância dos tópicos e prompts gerados. Isso exigiria um volume de dados de treinamento e infraestrutura de Machine Learning (ML) mais robusta.

## Considerações Adicionais

*   **Comunicação Frontend-Backend**: O frontend Streamlit (`frontend/app.py`) se comunica com o backend Flask (`backend/app.py`) através de requisições HTTP para os endpoints `/extract_topics` e `/generate_prompts`.
*   **CORS**: O backend Flask está configurado com `Flask-CORS` para permitir requisições de qualquer origem, o que é necessário para que o Streamlit (rodando em uma porta diferente) possa se comunicar com ele localmente.

## Contribuições

Este é um projeto MVP. Contribuições, sugestões e feedback são bem-vindos para futuras melhorias!
```
