import streamlit as st

def mostrar_login(supabase):
    st.title("Login - Sistema de Devoluções")
    
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        try:
            resposta = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state["usuario_logado"] = True
            st.session_state["uid"] = resposta.user.id
            st.rerun() # Atualiza a página para carregar o app.py logado
        except Exception as e:
            st.error("E-mail ou senha incorretos.")
