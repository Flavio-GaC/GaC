import streamlit as st
from supabase import create_client, Client

# Importa as telas
from theme import aplicar_tema, LOGO_URL, rodape
from login import mostrar_login
from home import mostrar_home
from cadastro import mostrar_cadastro
from novo_usuario import mostrar_novo_usuario
from meet import mostrar_meet


st.set_page_config(
    page_title="Sistema de Devoluções",
    page_icon="https://i.imgur.com/eG4PhxC.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa as variáveis de controle
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = False
if "tema" not in st.session_state:
    st.session_state["tema"] = "dark" # Padrão escuro

aplicar_tema()


@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Inicializa variável de controle de sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = False

if st.session_state["usuario_logado"]:
    c_vazia, c_botao = st.columns([8.8, 1.2])
    with c_botao:
        icone = "☀️ Light" if st.session_state["tema"] == "dark" else "🌙 Dark"
        if st.button(icone, use_container_width=True):
            st.session_state["tema"] = "light" if st.session_state["tema"] == "dark" else "dark"
            st.rerun()

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
            resposta_usuario = supabase.table("usuarios").select("nome_completo, nivel_acesso, empresa_id, setor").eq("id", uid).execute()
            if resposta_usuario.data:
                nome_logado = resposta_usuario.data[0]["nome_completo"]
                nivel_acesso = int(resposta_usuario.data[0]["nivel_acesso"])
                empresa_id = resposta_usuario.data[0].get("empresa_id")
                setor_usuario = resposta_usuario.data[0].get("setor")
        except Exception as e:
            pass

    NOMES_NIVEIS = {1: "Admin", 2: "Coordenador/Gestor", 3: "Supervisor", 4: "Operador"}

    with st.sidebar:
        st.markdown(
            f'<div class="sb-brand"><img src="{LOGO_URL}" width="120" alt="Logotipo"></div>',
            unsafe_allow_html=True,
        )

        # Cria a lista de menus permitidos dinamicamente
        opcoes_menu = ["Home"]
        
        # Regra da Aba Registrar Devolução: Nível 1 OU (Empresa 2 E Setor Recuperação/Suporte)
        if nivel_acesso == 1 or (empresa_id == 2 and setor_usuario in ["RECUPERAÇÃO", "SUPORTE"]):
            opcoes_menu.append("Registrar Devolução")
            
        # Regra da Aba Meet: Nível 1 OU Empresa 1
        if nivel_acesso == 1 or empresa_id == 1:
            opcoes_menu.append("Meet")
            
        # Regra da Aba Novo Usuário: Nível menor que 4 (Admin, Gestor, Supervisor)
        if nivel_acesso < 4:
            opcoes_menu.append("Novo Usuário")

        menu = st.radio(
            "Navegação",
            opcoes_menu,
            format_func=lambda item: {
                "Home": "📊  Home",
                "Registrar Devolução": "📦  Registrar Devolução",
                "Meet": "📅  Meet",
                "Novo Usuário": "👤  Novo Usuário",
            }[item],
            label_visibility="collapsed",
        )
        
        # Cria a lista de menus permitidos dinamicamente
        opcoes_menu = ["Home", "Registrar Devolução"]
        
        # Regra da Aba Meet: Empresa 1 (Bolt) ou Setor DADOS
        if empresa_id == 1 or setor_usuario == "DADOS":
            opcoes_menu.append("Meet")
            
        if nivel_acesso < 4:
            opcoes_menu.append("Novo Usuário")

        st.markdown("---")

        if nome_logado:
            iniciais = "".join([p[0] for p in nome_logado.split()[:2]]).upper()
            st.markdown(
                f"""<div class="sb-user">
                      <div class="sb-avatar">{iniciais}</div>
                      <div>
                        <small>Logado como</small>
                        <strong>{nome_logado}</strong>
                        <small>{NOMES_NIVEIS.get(nivel_acesso, "Operador")}</small>
                      </div>
                    </div>""",
                unsafe_allow_html=True,
            )

        st.write("")
        if st.button("Sair", use_container_width=True):
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
    elif menu == "Meet":
        mostrar_meet(supabase)
    rodape()
