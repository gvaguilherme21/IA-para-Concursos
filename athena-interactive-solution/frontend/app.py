import streamlit as st
import requests
import json # Import json for formatting the JSON preview

# Configuration for the backend API URL
# Assumes the Flask backend is running on localhost:5000
# If your backend is elsewhere, change this URL
BACKEND_API_URL = "http://localhost:5000"
EXTRACT_TOPICS_ENDPOINT = f"{BACKEND_API_URL}/extract_topics"
GENERATE_PROMPTS_ENDPOINT = f"{BACKEND_API_URL}/generate_prompts"

st.set_page_config(page_title="Athena Interativo", layout="wide")

st.title("Athena - Solução de IA para Concursos (Interativo)")
st.markdown("Cole o conteúdo do edital abaixo para extrair tópicos e, em seguida, gere prompts de estudo personalizados.")

# Initialize session state variables if they don't exist
if 'topics' not in st.session_state:
    st.session_state.topics = []
if 'selected_gaps' not in st.session_state:
    st.session_state.selected_gaps = []
if 'prompts' not in st.session_state:
    st.session_state.prompts = []
if 'edital_text_area' not in st.session_state:
    st.session_state.edital_text_area = ""

# --- 1. Input Edital Content ---
st.subheader("1. Insira o Conteúdo do Edital")
edital_content = st.text_area("Conteúdo do Edital:", 
                              value=st.session_state.edital_text_area,
                              height=250, 
                              key="edital_input_main",
                              help="Cole aqui todo o texto do edital que você deseja analisar.")

if edital_content and edital_content != st.session_state.edital_text_area:
    st.session_state.edital_text_area = edital_content
    # Clear previous results if edital changes
    st.session_state.topics = []
    st.session_state.selected_gaps = []
    st.session_state.prompts = []


# --- 2. Extract Topics ---
st.subheader("2. Extraia Tópicos do Edital")
if st.button("Extrair Tópicos", key="extract_topics_button", help="Clique para analisar o edital e identificar os principais tópicos."):
    if edital_content.strip():
        with st.spinner("Analisando edital e extraindo tópicos... Por favor, aguarde."):
            try:
                payload = {"edital_content": edital_content}
                response = requests.post(EXTRACT_TOPICS_ENDPOINT, json=payload, timeout=30) # Added timeout
                response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
                
                st.session_state.topics = response.json().get("topics", [])
                if st.session_state.topics:
                    st.success(f"{len(st.session_state.topics)} tópicos extraídos com sucesso!")
                else:
                    st.warning("Nenhum tópico foi extraído. Verifique o conteúdo do edital ou tente um texto diferente.")
                # Clear previous prompts when new topics are extracted
                st.session_state.prompts = []
            except requests.exceptions.ConnectionError:
                st.error(f"Erro de Conexão: Não foi possível conectar ao backend em {BACKEND_API_URL}. Verifique se o backend Flask está rodando.")
            except requests.exceptions.Timeout:
                st.error("Erro de Timeout: A requisição para extrair tópicos demorou muito para responder.")
            except requests.exceptions.HTTPError as e:
                st.error(f"Erro HTTP ao extrair tópicos: {e.response.status_code} - {e.response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro ao extrair tópicos: {e}")
            except json.JSONDecodeError:
                st.error("Erro ao processar a resposta do backend (não é um JSON válido).")
    else:
        st.warning("Por favor, insira o conteúdo do edital antes de extrair tópicos.")

# Display extracted topics for selection
if st.session_state.topics:
    st.markdown("#### Tópicos Extraídos (Selecione suas lacunas de conhecimento):")
    # Using st.multiselect to allow users to pick multiple topics as knowledge gaps
    st.session_state.selected_gaps = st.multiselect(
        "Selecione os tópicos que você considera como suas lacunas de conhecimento:",
        options=st.session_state.topics,
        default=st.session_state.selected_gaps, # Keep previous selections if any
        key="topics_multiselect"
    )

# --- 3. Add Manual Knowledge Gaps ---
st.subheader("3. Adicione Lacunas de Conhecimento Manuais (Opcional)")
manual_gaps_input = st.text_input(
    "Digite lacunas de conhecimento adicionais (separadas por vírgula):",
    key="manual_gaps_input",
    help="Ex: Direito Financeiro, Controle Interno, AFO"
)

# --- 4. Generate Study Prompts ---
st.subheader("4. Gere Prompts de Estudo Personalizados")
if st.button("Gerar Prompts de Estudo", key="generate_prompts_button", help="Clique para gerar prompts com base no edital e nas lacunas de conhecimento selecionadas/digitadas."):
    if not edital_content.strip():
        st.warning("Por favor, insira o conteúdo do edital.")
    else:
        # Combine selected topics and manually entered gaps
        final_knowledge_gaps = list(st.session_state.selected_gaps) # Start with selected topics
        if manual_gaps_input.strip():
            manual_gaps_list = [gap.strip() for gap in manual_gaps_input.split(',') if gap.strip()]
            for mgap in manual_gaps_list:
                if mgap not in final_knowledge_gaps: # Avoid duplicates
                    final_knowledge_gaps.append(mgap)
        
        if not final_knowledge_gaps:
            st.info("Nenhuma lacuna de conhecimento foi selecionada ou digitada. Prompts gerais para o edital podem ser gerados.")
            # Optionally, you could decide to not call the API if no gaps are provided,
            # or let the backend handle it (current backend mock does generate generic prompts).

        with st.spinner("Gerando prompts de estudo... Por favor, aguarde."):
            try:
                payload = {
                    "edital_content": edital_content,
                    "knowledge_gaps": final_knowledge_gaps
                }
                response = requests.post(GENERATE_PROMPTS_ENDPOINT, json=payload, timeout=30) # Added timeout
                response.raise_for_status()

                st.session_state.prompts = response.json().get("prompts", [])
                if st.session_state.prompts:
                    st.success(f"{len(st.session_state.prompts)} prompts gerados com sucesso!")
                else:
                    st.warning("Nenhum prompt foi gerado. Tente ajustar as lacunas de conhecimento ou o edital.")
            except requests.exceptions.ConnectionError:
                st.error(f"Erro de Conexão: Não foi possível conectar ao backend em {BACKEND_API_URL}. Verifique se o backend Flask está rodando.")
            except requests.exceptions.Timeout:
                st.error("Erro de Timeout: A requisição para gerar prompts demorou muito para responder.")
            except requests.exceptions.HTTPError as e:
                st.error(f"Erro HTTP ao gerar prompts: {e.response.status_code} - {e.response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro ao gerar prompts: {e}")
            except json.JSONDecodeError:
                st.error("Erro ao processar a resposta do backend (não é um JSON válido).")


# Display generated prompts
if st.session_state.prompts:
    st.markdown("---")
    st.subheader("Prompts de Estudo Gerados:")
    for i, prompt in enumerate(st.session_state.prompts):
        st.markdown(f"**{i+1}.** {prompt}")
    st.markdown("---")


# --- Footer and Debug Information (Optional) ---
st.sidebar.header("Opções")
if st.sidebar.checkbox("Mostrar informações de Debug", key="debug_checkbox"):
    st.sidebar.subheader("Último Edital Enviado:")
    st.sidebar.text_area("Edital (preview)", value=edital_content[:500] + "..." if edital_content else "Nenhum edital.", height=100, disabled=True)
    
    st.sidebar.subheader("Tópicos Extraídos (JSON):")
    st.sidebar.json({"topics": st.session_state.topics} if st.session_state.topics else {"message": "Nenhum tópico extraído."})

    combined_gaps_for_debug = list(st.session_state.selected_gaps)
    if manual_gaps_input.strip():
        manual_gaps_list_debug = [gap.strip() for gap in manual_gaps_input.split(',') if gap.strip()]
        for mgap_debug in manual_gaps_list_debug:
            if mgap_debug not in combined_gaps_for_debug:
                combined_gaps_for_debug.append(mgap_debug)
    st.sidebar.subheader("Lacunas de Conhecimento para Envio (JSON):")
    st.sidebar.json({"knowledge_gaps": combined_gaps_for_debug} if combined_gaps_for_debug else {"message": "Nenhuma lacuna."})
    
    st.sidebar.subheader("Prompts Recebidos (JSON):")
    st.sidebar.json({"prompts": st.session_state.prompts} if st.session_state.prompts else {"message": "Nenhum prompt gerado."})

st.sidebar.markdown("---")
st.sidebar.info(
    "Esta é uma aplicação MVP (Minimum Viable Product).\n\n"
    "O modelo de IA para extração e geração é simplificado."
)

# To run this Streamlit app:
# 1. Ensure the Flask backend is running (e.g., `python backend/app.py`)
# 2. Navigate to the `frontend` directory in your terminal
# 3. Run: `streamlit run app.py`
