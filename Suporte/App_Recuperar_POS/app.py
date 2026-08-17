import streamlit as st
from supabase import create_client

# Importações de temas
from themes.theme import aplicar_tema, LOGO_URL, rodape
from themes.theme_notifications import checar_notificacoes

# Importar rotas
from routers.login import mostrar_login
from routers.homepage import mostrar_home
from routers.bolt.devolucao import mostrar_devolucao
from routers.brasilcard.registro_meet import mostrar_meet
from routers.brasilcard.dashboard_meets import mostrar_dashboard_meets
from routers.cadastro_usuario import mostrar_novo_usuario
from routers.lojistas import mostrar_lojistas
from routers.brasilcard.upload_leads import mostrar_upload_leads
from routers.brasilcard.esteira_leads import mostrar_esteira_leads


# Configuração Base
st.set_page_config(
    page_title="Sistema de Gestão",
    page_icon="https://i.imgur.com/eG4PhxC.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicialização do Supabase (Mantendo a Sessão Ativa)
if "supabase" not in st.session_state:
    URL_SUPABASE = st.secrets["SUPABASE_URL"]
    CHAVE_SUPABASE = st.secrets["SUPABASE_KEY"]
    st.session_state["supabase"] = create_client(URL_SUPABASE, CHAVE_SUPABASE)
   
# Resgata o cliente com a sessão do usuário logado
supabase = st.session_state["supabase"]

# Inicialização de Variáveis de Sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = False
if "tema" not in st.session_state:
    st.session_state["tema"] = "dark"

# Aplica as cores na tela inteira
aplicar_tema()

# Logo nativa acima do menu (Suportado pelo st.navigation)
st.logo(LOGO_URL, icon_image=LOGO_URL, size="large")

mapa_cargos = {
    0: "Desenvolvedor(a)",
    1: "Gestor(a)",
    2: "Coordenador(a)",
    3: "Supervisor(a)",
    4: "Monitor(a)",
    5: "Operador(a)"
}

# --- ENVOLTÓRIOS DE PÁGINAS ---
def render_login():
    mostrar_login(supabase)

def render_home(): 
    mostrar_home(supabase)

def render_devolucao_maquinas():
    mostrar_devolucao(supabase)

def render_meet():
    mostrar_meet(supabase)

def render_usuario():
    mostrar_novo_usuario(supabase)

def render_lojistas():
    mostrar_lojistas(supabase)

def render_dashboard_meet():
    mostrar_dashboard_meets(supabase)

def render_upload_leads():
    mostrar_upload_leads(supabase)

def render_esteira_leads():
    mostrar_esteira_leads(supabase)

def render_notifications():
    checar_notificacoes(supabase)


# --- LÓGICA DE NAVEGAÇÃO E REGRAS DE ACESSO ---
if not st.session_state["usuario_logado"]:
    # Oculta a barra lateral caso o usuário não esteja logado
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    pg = st.navigation([st.Page(render_login, title="Login", icon="🔒")])
    pg.run()
    
else:
    # 1. Busca todos os dados do usuário em uma única consulta
    uid = st.session_state.get("uid")
    try:
        resp = supabase.table("usuarios").select("nivel_acesso, empresa_id, setor, nome_completo").eq("id", uid).execute()
        dados_user = resp.data[0]
        
        nivel_acesso = int(dados_user["nivel_acesso"])
        empresa_id = int(dados_user.get("empresa_id", 0))
        setor_usuario = str(dados_user.get("setor", "")).strip().upper()
        nome_logado = dados_user.get("nome_completo", "Usuário")
        cargo_texto = mapa_cargos.get(nivel_acesso, "")
        
        # Já guarda o setor na sessão para as outras telas (como a da esteira) aproveitarem
        st.session_state["setor_usuario"] = setor_usuario
        
    except:
        # Caso o banco falhe, força a visualização do menu para testes
        nivel_acesso, empresa_id, setor_usuario, nome_logado = 1, 2, "SUPORTE", "Usuário Teste"
        cargo_texto = ""
    
    # 2. Chama o verificador de notificações silencioso
    checar_notificacoes(supabase, uid, setor_usuario)

    # 3. Botão de Dark/Light Mode na tela principal
    c_vazia, c_botao = st.columns([8.8, 1.2])
    with c_botao:
        icone = "☀️ Light" if st.session_state["tema"] == "dark" else "🌙 Dark"
        if st.button(icone, use_container_width=True):
            st.session_state["tema"] = "light" if st.session_state["tema"] == "dark" else "dark"
            st.rerun()

    # 3. Montagem do Menu Base (Sempre visível)
    paginas = {
        "Menu Principal": [
            st.Page(render_home, title="Home", icon="📊", default=True),
            st.Page(render_lojistas, title="Lojistas", icon="💼")
        ]
    }

    # 4. ACESSOS ADMINISTRATIVO
    if nivel_acesso <= 2:
        paginas["Administrativo"] = [
            st.Page(render_usuario, title="Cadastrar Usuário", icon="👤"),
            st.Page(render_dashboard_meet, title="Dashboard Meets", icon="🎯")
            ]
        paginas["BrasilCard"] = [
                                st.Page(render_meet, title="Meets", icon="🎥"),
                                st.Page(render_upload_leads, title="Importar Leads", icon="🧲"),
                                st.Page(render_esteira_leads, title="Esteira comercial", icon="🚀")
                            ]
        paginas["Bolt"] = [
                            st.Page(render_devolucao_maquinas, title="Devoluções", icon="📦")
                        ]
    # ACESSOS BRASILCARD
    elif empresa_id == 1:
        if nivel_acesso <= 4:
            paginas["Administrativo"] = [
                        st.Page(render_usuario, title="Cadastrar Usuário", icon="👤"),
                        st.Page(render_dashboard_meet, title="Dashboard Meets", icon="🎯"),
                        st.Page(render_upload_leads, title="Importar Leads", icon="🧲")
                        ]
            paginas["BrasilCard"] = [
                        st.Page(render_meet, title="Meets", icon="🎥"),
                        st.Page(render_esteira_leads, title="Esteira comercial", icon="🚀")
                    ]
        else:
            paginas["BrasilCard"] = [
                        st.Page(render_meet, title="Meets", icon="🎥"),
                        st.Page(render_esteira_leads, title="Esteira comercial", icon="🚀")
                    ]
    # ACESSOS BOLT
    elif empresa_id == 2:
        if nivel_acesso <= 4:
            paginas["Administrativo"] = [
                                    st.Page(render_usuario, title="Cadastrar Usuário", icon="👤"),
                                    st.Page(render_dashboard_meet, title="Dashboard Meets", icon="🎯")
                                    ]
            paginas["Bolt"] = [
                        st.Page(render_devolucao_maquinas, title="Devoluções", icon="📦"),
                    ]
        else:
            paginas["Bolt"] = [
                        st.Page(render_devolucao_maquinas, title="Devoluções", icon="📦"),
                    ]
            
    # 5. Inicializa o roteador multipáginas
    pg = st.navigation(paginas)

    # 6. Perfil e Botão Sair na parte inferior da Sidebar
    with st.sidebar:
        st.write("---")
        st.markdown(f"""
            <div class="sb-user">
                <div class="sb-avatar">{nome_logado[:2].upper()}</div>
                <div>
                    <small>Logado como </small><strong>{str(nome_logado).split()[0]}</strong><br>
                    <span style="font-size: 12px; color: #38bdf8; margin-top: 2px; display: inline-block;">{cargo_texto}</span>
                    <span style="font-size: 9px; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 4px; margin-left: 6px; vertical-align: middle;">{str(setor_usuario).split()[0]}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    pg.run()
    rodape()
