import streamlit as st

def mostrar_login(supabase):
    css = """
    <style>
    /* Fundo com a sede e filtro escuro */
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(6,12,26,.72), rgba(6,12,26,.72)),
                          url("https://www.brasilcard.net/assets/images/foto-sede.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }

    .block-container { padding-top: 6vh; max-width: 1100px; }

    /* Cartão de login */
    [data-testid="column"]:nth-child(2) {
        background-color: #FFFFFF;
        padding: 2.5rem 2.25rem;
        border-radius: 16px;
        box-shadow: 0 24px 60px -20px rgba(0,0,0,.65);
        border: 1px solid rgba(255,255,255,.6);
    }

    /* Força os textos e labels dentro do cartão a ficarem escuros */
    [data-testid="column"]:nth-child(2) h1,
    [data-testid="column"]:nth-child(2) h3,
    [data-testid="column"]:nth-child(2) h4,
    [data-testid="column"]:nth-child(2) label,
    [data-testid="column"]:nth-child(2) p { color: #0F172A !important; }

    .login-title { text-align:center; margin-bottom:1.25rem; }
    .login-title h3 { margin:0 0 .25rem; font-size:1.25rem; font-weight:700; }
    .login-title p { margin:0; font-size:.88rem; color:#64748B !important; }
    .login-foot {
        text-align:center; margin-top:1.25rem; font-size:.75rem; color:#94A3B8 !important;
    }

    @media (max-width: 640px) {
        .block-container { padding: 1.5rem 1rem; }
        [data-testid="column"]:nth-child(2) { padding: 1.75rem 1.25rem; }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    col_esq, col_centro, col_dir = st.columns([1.0, 1.2, 1.0])

    # Colocamos tudo de login dentro da coluna do centro
    with col_centro:
        # Logo
        st.markdown(
            """
            <div style="display: flex; justify-content: center; margin-bottom: 14px;">
                <img src="https://i.imgur.com/eG4PhxC.png" width="130" alt="Logotipo">
            </div>
            <div class="login-title">
                <h3>GaC - Teresina-Pi</h3>
                <p>Acesse com suas credenciais corporativas</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        email = st.text_input("Usuário / E-mail", placeholder="nome@empresa.com.br")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")

        st.write("")
        if st.button("Entrar", type="primary", use_container_width=True):
            with st.spinner("Validando credenciais..."):
                try:
                    resposta_auth = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": senha
                    })
                    if resposta_auth.user:
                        st.session_state["usuario_logado"] = True
                        st.session_state["uid"] = resposta_auth.user.id
                        st.rerun()
                except Exception as e:
                    st.error("Credenciais inválidas. Tente novamente.")

        st.markdown(
            '<div class="login-foot">Acesso restrito a colaboradores autorizados</div>',
            unsafe_allow_html=True,
        )
