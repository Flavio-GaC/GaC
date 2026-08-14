import streamlit as st
from themes.theme import tema_login

def mostrar_login(supabase):
    # Chama a função que injeta o CSS isolado
    tema_login()

    col_esq, col_centro, col_dir = st.columns([1.0, 1.2, 1.0])

    with col_centro:
        st.markdown(
            """
            <div style="display: flex; justify-content: center; margin-bottom: 14px;">
                <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSk-QaUmTV7hcYg5cDpuEUoLCfscN-OVuiCZcJukputzg&s=10" width="130" alt="Logotipo">
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
