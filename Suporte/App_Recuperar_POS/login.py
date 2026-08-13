import streamlit as st

def mostrar_login(supabase):
    css = """
    <style>
    /* Fundo com a sede e filtro escuro */
    [data-testid="stAppViewContainer"] {
        background-image: url("https://www.brasilcard.net/assets/images/foto-sede.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        box-shadow: inset 0 0 0 2000px rgba(0, 0, 0, 0.6);
    }
    
    [data-testid="stHeader"] {
        background: transparent;
    }

    /* Estiliza apenas a coluna do meio para virar o cartão branco */
    [data-testid="column"]:nth-child(2) {
        background-color: white;
        padding: 2.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
        margin-top: 10vh;
    }
    
    /* Força os textos e labels dentro do cartão a ficarem escuros */
    [data-testid="column"]:nth-child(2) h4,
    [data-testid="column"]:nth-child(2) label,
    [data-testid="column"]:nth-child(2) p {
        color: #333 !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # --- O SEGREDO ESTÁ AQUI ---
    # Usamos proporções. As colunas laterais (1.5) empurram a do centro (1.0)
    col_esq, col_centro, col_dir = st.columns([1.0, 1.2, 1.0])

    # Colocamos tudo de login dentro da coluna do centro
    with col_centro:
        # Logo
        st.markdown(
            """
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <img src="https://i.imgur.com/eG4PhxC.png" width="130">
            </div>
            """, 
            unsafe_allow_html=True
        )
                
        email = st.text_input("Usuário / E-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
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
