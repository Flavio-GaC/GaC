import streamlit as st

def mostrar_novo_usuario(supabase):
    st.subheader("Cadastrar Novo Usuário")
    
    uid = st.session_state.get("uid")
    try:
        resp_user = supabase.table("usuarios").select("nivel_acesso").eq("id", uid).execute()
        nivel_atual = int(resp_user.data[0]["nivel_acesso"])
    except:
        nivel_atual = 4 
        
    todos_niveis = [
        "1 - ADMIN", 
        "2 - Coordenador/Gestor", 
        "3 - Supervisor", 
        "4 - Operador"
    ]
    
    niveis_permitidos = [
        n for n in todos_niveis 
        if nivel_atual == 1 or int(n.split(" ")[0]) > nivel_atual
    ]

    if not niveis_permitidos:
        st.warning("Você não tem permissão para criar usuários de nível inferior ao seu.")
        return

    with st.form("form_novo_usuario", clear_on_submit=True):
        nome = st.text_input("Nome Completo *")
        setor = st.selectbox("Setor *", ["RECUPERAÇÃO", "SUPORTE", "DADOS"])
        email = st.text_input("E-mail *")
        senha = st.text_input("Senha *", type="password", help="Mínimo de 6 caracteres")
        
        nivel = st.selectbox("Nível de Acesso", niveis_permitidos)
        
        submit = st.form_submit_button("Criar Usuário", type="primary")

        if submit:
            if not nome or not email or not senha:
                st.error("Preencha todos os campos obrigatórios.")
            else:
                nivel_num = int(nivel.split(" ")[0])
                
                # === VALIDAÇÃO DE SEGURANÇA AQUI ===
                if nivel_atual != 1 and nivel_num <= nivel_atual:
                    st.error("Acesso Negado: Você não tem permissão real para criar um usuário com este nível.")
                else:
                    try:
                        resposta_auth = supabase.auth.sign_up({
                            "email": email,
                            "password": senha
                        })
                        
                        if resposta_auth.user:
                            novo_id = resposta_auth.user.id
                            
                            supabase.table("usuarios").insert({
                                "id": novo_id,
                                "nome_completo": nome,
                                "setor": setor,
                                "nivel_acesso": nivel_num
                            }).execute()
                            
                            st.success(f"Usuário {nome} criado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao criar usuário: {e}")
