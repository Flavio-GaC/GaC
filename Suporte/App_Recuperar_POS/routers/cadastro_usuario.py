import streamlit as st
from datetime import datetime
from themes.theme import cabecalho_pagina, titulo_secao

def mostrar_novo_usuario(supabase):
    cabecalho_pagina(
        "Gestão de Usuários",
        "Cadastre novos acessos e gerencie os colaboradores existentes.",
    )

    # Criação das abas
    aba_novo, aba_gerenciar = st.tabs(["📝 Novo Usuário", "👥 Consultar e Gerenciar"])

    uid = st.session_state.get("uid")
    
    # Busca o nível, empresa e setor do usuário logado para aplicar as regras de segurança
    try:
        resp_user = supabase.table("usuarios").select("nivel_acesso, empresa_id, setor").eq("id", uid).execute()
        dados_logado = resp_user.data[0]
        nivel_atual = int(dados_logado["nivel_acesso"])
        empresa_logada = int(dados_logado.get("empresa_id", 0))
        setor_logado = dados_logado.get("setor", "")
    except:
        nivel_atual = 4
        empresa_logada = 0
        setor_logado = ""

    # ==========================================
    # ABA 1: CADASTRAR NOVO USUÁRIO
    # ==========================================
    with aba_novo:
        todos_niveis = [
            "1 - Gestor",
            "2 - Coordenador/Gestor",
            "3 - Supervisor",
            "4 - Monitor",
            "5 - Operador"
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
                                        "nome_completo": str(nome).upper(),
                                        "setor": str(setor).upper(),
                                        "nivel_acesso": nivel_num,
                                        "empresa_id": empresa_id,
                                        "criado_por": uid,
                                        "ativo": True
                                    }).execute()

                            st.success(f"Usuário {nome} criado com sucesso e vinculado à {empresa_nome}!")
                        except Exception as e:
                            st.error(f"Erro ao criar usuário: {e}")

    # ==========================================
    # ABA 2: CONSULTAR E GERENCIAR USUÁRIOS
    # ==========================================
    with aba_gerenciar:
        titulo_secao("Filtros e Lista de Usuários")

        if nivel_atual > 3:
            st.warning("Você não possui nível de acesso suficiente para gerenciar usuários.")
            return

        # 1. Busca as empresas cadastradas no banco para o selectbox e mapeamento
        empresas_dict = {}
        try:
            resp_empresas = supabase.table("empresas").select("id, nome_fantasia").execute()
            for emp in resp_empresas.data:
                empresas_dict[emp["nome_fantasia"]] = emp["id"]
        except Exception as e:
            st.error(f"Erro ao carregar as empresas: {e}")
            return

        # Cria um dicionário inverso para descobrir o nome da empresa pelo ID atual do usuário
        id_para_nome_empresa = {v: k for k, v in empresas_dict.items()}
        opcoes_empresas = list(empresas_dict.keys())

        # 2. Busca os usuários respeitando as regras de nível
        try:
            query = supabase.table("usuarios").select("id, nome_completo, setor, nivel_acesso, empresa_id, ativo")

            if nivel_atual == 1:
                pass
            elif nivel_atual == 2:
                query = query.eq("empresa_id", empresa_logada)
            elif nivel_atual == 3:
                query = query.eq("empresa_id", empresa_logada).eq("setor", setor_logado)

            resp_busca = query.order("nome_completo").execute()
            usuarios_lista = resp_busca.data
        except Exception as e:
            st.error(f"Erro ao buscar usuários: {e}")
            usuarios_lista = []

        if not usuarios_lista:
            st.info("Nenhum usuário encontrado para o seu nível de acesso.")
        else:
            st.caption(f"Total de usuários encontrados: **{len(usuarios_lista)}**")
            st.write("")

            for u in usuarios_lista:
                u_id = u["id"]
                u_nome = u.get("nome_completo", "Não localizado")
                u_status = u.get("ativo", True)
                u_setor = u.get("setor", "Não localizado")
                u_nivel = u.get("nivel_acesso", 5)
                u_empresa_id = u.get("empresa_id")

                # Descobre o nome fantasia atual da empresa do usuário pelo ID dela
                nome_empresa_atual = id_para_nome_empresa.get(u_empresa_id, "")

                status_label = "🟢 Ativo" if u_status else "🔴 Inativo"
                
                with st.expander(f"👤 {u_nome} | Setor: {u_setor} | Nível: {u_nivel} | {status_label}"):
                    
                    with st.form(f"form_edit_user_{u_id}"):
                        c1, c2 = st.columns(2)
                        
                        with c1:
                            novo_status = st.toggle("Usuário Ativo", value=u_status, key=f"toggle_ativo_{u_id}")
                            novo_nome = st.text_input("Nome Completo", value=u_nome, key=f"nome_{u_id}")
                            
                            # Seleção da Empresa
                            if nome_empresa_atual in opcoes_empresas:
                                idx_empresa = opcoes_empresas.index(nome_empresa_atual)
                            else:
                                idx_empresa = 0

                            # Trava de empresa: Apenas Nível 1 pode alterar a empresa de qualquer um (ou Nível 2 se desejar)
                            bloquear_empresa = (nivel_atual > 2) 
                            
                            nova_empresa_nome = st.selectbox(
                                "Empresa", 
                                opcoes_empresas, 
                                index=idx_empresa,
                                disabled=bloquear_empresa,
                                key=f"empresa_{u_id}"
                            )
                            if bloquear_empresa:
                                st.caption("🔒 Nível de acesso insuficiente para alterar a empresa.")

                        with c2:
                            setores_disponiveis = ["RECUPERAÇÃO", "SUPORTE", "DADOS", "COMERCIAL", "PÓS-VENDA"]
                            if u_setor not in setores_disponiveis:
                                setores_disponiveis.append(u_setor)
                            
                            idx_setor = setores_disponiveis.index(u_setor)
                            bloquear_setor = (nivel_atual >= 3)
                            
                            novo_setor = st.selectbox(
                                "Setor", 
                                setores_disponiveis, 
                                index=idx_setor, 
                                disabled=bloquear_setor,
                                key=f"sel_setor_{u_id}"
                            )
                            if bloquear_setor:
                                st.caption("🔒 Nível de acesso insuficiente para alterar o setor.")

                        st.write("")
                        btn_salvar = st.form_submit_button("Salvar Alterações", type="primary")

                        if btn_salvar:
                            if nivel_atual > 3:
                                st.error("Acesso negado para alteração.")
                            else:
                                try:
                                    with st.spinner("Atualizando dados..."):
                                        # Resgata o ID numérico da empresa selecionada no selectbox através do dicionário
                                        novo_empresa_id = empresas_dict.get(nova_empresa_nome)

                                        dados_atualizacao = {
                                            "ativo": novo_status,
                                            "nome_completo": novo_nome,
                                            "updated_at": datetime.now().isoformat(),
                                            "updated_by": uid
                                        }

                                        # Se for nível 1 ou 2, permite atualizar o setor
                                        if nivel_atual <= 2:
                                            dados_atualizacao["setor"] = novo_setor
                                        
                                        # Se for nível 1, permite atualizar a empresa
                                        if nivel_atual == 1 and novo_empresa_id:
                                            dados_atualizacao["empresa_id"] = novo_empresa_id

                                        supabase.table("usuarios").update(dados_atualizacao).eq("id", u_id).execute()

                                    st.success("Dados do usuário atualizados com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao atualizar usuário: {e}")
