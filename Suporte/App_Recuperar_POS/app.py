import streamlit as st
from supabase import create_client, Client

# Importa as telas
from login import mostrar_login
from home import mostrar_home
from cadastro import mostrar_cadastro

st.set_page_config(page_title="Sistema de Devoluções", layout="wide", page_icon="https://bolt.com.br/assets/images/favicon-32x32.png?58abdfbfa6eb51ae231d3cdfff8e8648")

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Inicializa variável de controle de sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = False

# Roteamento de telas
if not st.session_state["usuario_logado"]:
    mostrar_login(supabase)
else:
    # Estrutura provisória enquanto criamos os próximos arquivos
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Navegação", ["Home", "Registrar Devolução"])
    
    if st.sidebar.button("Sair"):
        supabase.auth.sign_out()
        st.session_state["usuario_logado"] = False
        st.rerun()

    if menu == "Home":
        mostrar_home(supabase)
    elif menu == "Registrar Devolução":
        mostrar_cadastro(supabase)
