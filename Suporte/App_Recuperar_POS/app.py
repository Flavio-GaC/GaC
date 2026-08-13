import streamlit as st
from supabase import create_client, Client

# Importa as telas
from login import mostrar_login
from home import mostrar_home
from cadastro import mostrar_cadastro
from novo_usuario import mostrar_novo_usuario

st.set_page_config(page_title="Sistema de Devoluções", page_icon="https://i.imgur.com/eG4PhxC.png")

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
    uid = st.session_state.get("uid")
    nome_logado = ""
    nivel_acesso = 4 # Define nível restrito como padrão por segurança
    
    # 1. Busca os dados do usuário de forma segura APÓS o login
    if uid:
        try:
            resposta_usuario = supabase.table("usuarios").select("nome_completo, nivel_acesso").eq("id", uid).execute()
            if resposta_usuario.data:
                nome_logado = resposta_usuario.data[0]["nome_completo"]
                nivel_acesso = int(resposta_usuario.data[0]["nivel_acesso"])
        except Exception as e:
            pass

    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Navegação", ["Home", "Registrar Devolução", "Novo Usuário"])
    
    if nome_logado:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Logado como:**<br>{nome_logado}", unsafe_allow_html=True)

    if st.sidebar.button("Sair"):
        supabase.auth.sign_out()
        st.session_state.clear() # Limpa a sessão por completo
        st.rerun()

    # 2. Exibição das telas usando a variável nivel_acesso extraída corretamente
    if menu == "Home":
        mostrar_home(supabase)
    elif menu == "Registrar Devolução":
        mostrar_cadastro(supabase)
    elif menu == "Novo Usuário":
        if nivel_acesso < 4:
            mostrar_novo_usuario(supabase) 
        else:
            st.error("Nível de acesso insuficiente para acesso.")
