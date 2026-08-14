import streamlit as st

from themes.theme import cabecalho_pagina, titulo_secao


def mostrar_novo_usuario(supabase):
    cabecalho_pagina(
        "Cadastrar Novo Usuário",
        "Crie acessos respeitando a hierarquia de níveis do sistema.",
    )

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
        "3 - Monitor",
        "4 - Operador"
    ]

    niveis_permitidos = [
        n for n in todos_niveis
        if nivel_atual == 1 or int(n.split(" ")[0]) > nivel_atual
    ]

    if not niveis_permitidos:
        st.warning("Você não tem permissão para criar usuários de nível inferior ao seu.")
        return

    # Busca as empresas cadastradas no banco
    empresas_dict = {}
    try:
        resp_empresas = supabase.table("empresas").select("id, nome_fantasia").execute()
        for emp in resp_empresas.data:
            empresas_dict[emp["nome_fantasia"]] = emp["id"]
    except Exception as e:
        st.error(f"Erro ao carregar as empresas: {e}")
        return

    # Cria a lista de opções para o Selectbox
    opcoes_empresas = [""] + list(empresas_dict.keys())

    with st.form("form_novo_usuario", clear_on_submit=True):
        titulo_secao("Dados do colaborador")
        
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome Completo *", placeholder="Ex.: Maria Silva")
            email = st.text_input("E-mail *", placeholder="nome@empresa.com.br")
            empresa_nome = st.selectbox("Empresa *", opcoes_empresas)

        with col2:
            setor = st.selectbox("Setor *", ["RECUPERAÇÃO", "SUPORTE", "DADOS", "PÓS-VENDA", "COMERCIAL"])
            senha = st.text_input("Senha *", type="password", help="Mínimo de 6 caracteres")
            nivel = st.selectbox("Nível de Acesso *", niveis_permitidos)

        st.caption("Campos com * são obrigatórios. Você só pode criar usuários de nível inferior ao seu.")

        st.write("")
        submit = st.form_submit_button("Criar Usuário", type="primary", use_container_width=True)

        if submit:
            if not nome or not email or not senha or not empresa_nome:
                st.error("Preencha todos os campos obrigatórios.")
            else:
                nivel_num = int(nivel.split(" ")[0])
                empresa_id = empresas_dict[empresa_nome]

                # === VALIDAÇÃO DE SEGURANÇA ===
                if nivel_atual != 1 and nivel_num <= nivel_atual:
                    st.error("Acesso Negado: Você não tem permissão real para criar um usuário com este nível.")
                else:
                    try:
                        with st.spinner("Criando usuário..."):
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
                                    "nivel_acesso": nivel_num,
                                    "empresa_id": empresa_id,
                                    "criado_por": uid
                                }).execute()

                        if resposta_auth.user:
                            st.success(f"Usuário {nome} criado com sucesso e vinculado à {empresa_nome}!")
                    except Exception as e:
                        st.error(f"Erro ao criar usuário: {e}")
