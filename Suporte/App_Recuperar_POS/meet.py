import streamlit as st
from datetime import datetime
import re

from theme import cabecalho_pagina, titulo_secao

def mostrar_meet(supabase):
    cabecalho_pagina("Gestão de Meets", "Acompanhe e registre o histórico de agendamentos e contatos.")

    aba_novo, aba_atualizar = st.tabs(["📝 Novo Meet", "🔄 Atualizar / Histórico"])

    usuario_id = st.session_state.get("uid")

    # ==========================================
    # ABA 1: CRIAR NOVO MEET
    # ==========================================
    with aba_novo:
        with st.form("form_novo_meet", clear_on_submit=True):
            titulo_secao("Abertura de Novo Agendamento")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                input_cnpj = st.text_input("CNPJ", max_chars=18, placeholder="XX.XXX.XXX/XXXX-XX")
                nome_lojista = st.text_input("Nome Lojista")
            with c2:
                input_contato_lojista = st.text_input("Contato do Lojista", max_chars=15)
                data_meet = st.date_input("Data do Meet", format="DD/MM/YYYY")
            with c3:
                hora_meet = st.time_input("Hora do Meet")
                status_meet = st.selectbox("Status", ["Aguardando Horário", "Em Andamento", "Concluído", "Cancelado"])
            
            acao = st.selectbox("Ação", ["AGENDADO", "REAGENDADO"])
            observacao = st.text_area("Observações")

            submit_novo = st.form_submit_button("Criar Novo Meet", type="primary")

            if submit_novo:
                cnpj = re.sub(r"\D", "", input_cnpj)
                contato_lojista = re.sub(r"\D", "", input_contato_lojista)

                if len(cnpj) < 14:
                    st.error("Erro: CNPJ inválido. Digite os 14 números.")
                elif not contato_lojista:
                    st.error("Erro: Contato inválido.")
                elif not nome_lojista:
                    st.error("Erro: Preencha o nome do lojista.")
                else:
                    try:
                        with st.spinner("Gerando Meet..."):
                            dados = {
                                "usuario_id": usuario_id,
                                "cnpj": cnpj,
                                "nome_lojista": nome_lojista,
                                "contato_lojista": contato_lojista,
                                "data_meet": data_meet.strftime("%Y-%m-%d"),
                                "hora_meet": hora_meet.strftime("%H:%M:%S"),
                                "acao": acao,
                                "status_meet": status_meet,
                                "observacao": observacao
                            }
                            resp = supabase.table("meets").insert(dados).execute()
                            if resp.data:
                                novo_id = resp.data[0]["meet_id"]
                                st.success(f"✅ Meet gerado com sucesso! O número do seu Meet é: **{novo_id}**")
                    except Exception as e:
                        st.error(f"Erro ao criar meet: {e}")

    # ==========================================
    # ABA 2: ATUALIZAR E VER HISTÓRICO
    # ==========================================
    with aba_atualizar:
        titulo_secao("Consultar e Editar")
        
        c_modo, c_param, c_btn = st.columns([2, 3, 1])
        with c_modo:
            modo_busca = st.selectbox("Modo de Busca", ["Meus Meets", "Por CNPJ"])
        with c_param:
            if modo_busca == "Meus Meets":
                limite = st.selectbox("Quantidade de Meets", [10, 20, 50])
                input_cnpj_busca = ""
            else:
                input_cnpj_busca = st.text_input("Digite o CNPJ", max_chars=18, placeholder="Somente números ou formatado")
                limite = 50 # Limite seguro padrão para busca por CNPJ
        with c_btn:
            st.write("")
            st.write("")
            btn_buscar = st.button("Buscar", use_container_width=True, type="primary")

        if btn_buscar or "meets_buscados" in st.session_state:
            if btn_buscar:
                with st.spinner("Buscando..."):
                    try:
                        # Busca ordenando pelos mais recentes
                        if modo_busca == "Meus Meets":
                            resp = supabase.table("meets").select("*").eq("usuario_id", usuario_id).order("created_at", desc=True).execute()
                        else:
                            cnpj_limpo = re.sub(r"\D", "", input_cnpj_busca)
                            if cnpj_limpo:
                                resp = supabase.table("meets").select("*").eq("cnpj", cnpj_limpo).order("created_at", desc=True).execute()
                            else:
                                resp = type('obj', (object,), {'data': []}) # Retorno vazio falso
                        
                        st.session_state["meets_buscados"] = resp.data
                    except Exception as e:
                        st.error(f"Erro na busca: {e}")
                        st.session_state["meets_buscados"] = []

            dados_busca = st.session_state.get("meets_buscados", [])
            
            if not dados_busca:
                if btn_buscar: st.warning("Nenhum Meet encontrado.")
            else:
                # 1. Agrupar o histórico pelo meet_id
                meets_agrupados = {}
                for linha in dados_busca:
                    mid = linha["meet_id"]
                    if mid not in meets_agrupados:
                        meets_agrupados[mid] = []
                    meets_agrupados[mid].append(linha)
                
                # 2. Limita a quantidade de Meets únicos a exibir para poupar memória
                lista_mids = list(meets_agrupados.keys())[:limite]

                st.write("---")
                st.caption(f"Exibindo **{len(lista_mids)}** Meet(s). Clique em um deles para ver o histórico e atualizar.")
                
                # 3. Renderiza os cards sanfonados (Expanders)
                for mid in lista_mids:
                    historico = meets_agrupados[mid]
                    historico.reverse() # Inverte para exibir do mais antigo para o mais novo na timeline (Top->Down)
                    
                    base = historico[0]
                    status_atual = historico[-1]["status_meet"] 
                    
                    with st.expander(f"📍 Meet {mid} | {base.get('nome_lojista', 'N/A')} | Status: {status_atual}"):
                        st.caption(f"**CNPJ:** {base.get('cnpj', 'N/A')} | **Contato:** {base.get('contato_lojista', 'N/A')}")
                        st.write("")
                        
                        # Injeta o HTML da Linha do Tempo
                        for linha in historico:
                            data_formatada = datetime.strptime(linha['data_meet'], "%Y-%m-%d").strftime("%d/%m/%Y")
                            obs_html = f'<div class="tl-obs">"{linha["observacao"]}"</div>' if linha.get('observacao') else ''
                            
                            html_timeline = f"""
                            <div class="timeline-container">
                                <div class="timeline-dot"></div>
                                <div class="timeline-content">
                                    <div class="tl-header">
                                        <div class="tl-date">🕒 {data_formatada} às {linha['hora_meet']}</div>
                                        <div class="tl-status">{linha['status_meet']}</div>
                                    </div>
                                    <div class="tl-grid">
                                        <div>
                                            <span class="tl-label">Ação Realizada:</span> <span class="tl-value">{linha['acao']}</span>
                                        </div>
                                    </div>
                                    {obs_html}
                                </div>
                            </div>
                            """
                            st.markdown(html_timeline, unsafe_allow_html=True)
                        
                        st.write("---")
                        
                        # Usamos f"{mid}" nas chaves para que o Streamlit não confunda os inputs dos formulários
                        with st.form(f"form_up_{mid}", clear_on_submit=True):
                            titulo_secao("Adicionar Nova Interação")
                            c1, c2, c3 = st.columns(3)
                            with c1: 
                                nova_acao = st.selectbox("Ação Realizada", ["AGENDADO", "REAGENDADO"], key=f"acao_{mid}")
                            with c2: 
                                novo_status = st.selectbox("Novo Status", ["Aguardando Horário", "Em Andamento", "Concluído", "Cancelado"], key=f"status_{mid}")
                            with c3:
                                nova_data = st.date_input("Nova Data", format="DD/MM/YYYY", key=f"dt_{mid}")
                                nova_hora = st.time_input("Nova Hora", key=f"hr_{mid}")
                            
                            nova_obs = st.text_area("Nova Observação (Opcional)", key=f"obs_{mid}")
                            submit_up = st.form_submit_button("Salvar Histórico", type="primary")
                            
                            if submit_up:
                                with st.spinner("Atualizando..."):
                                    
                                    acao_final = nova_acao
                                    
                                    # === LÓGICA DE REAGENDAMENTO ===
                                    if nova_acao == "REAGENDADO":
                                        # Pega o ID da última interação (que é o último item da lista historico)
                                        ultimo_registro_id = historico[-1]["id"]
                                        
                                        # 1. Atualiza o status do registro anterior no banco
                                        supabase.table("meets").update({"status_meet": "Reagendado", "acao": "REAGENDADO"}).eq("id", ultimo_registro_id).execute()
                                        
                                        # 2. Altera a ação da nova inserção para AGENDADO
                                        acao_final = "AGENDADO"

                                    dados_update = {
                                        "meet_id": mid,
                                        "usuario_id": usuario_id,
                                        "cnpj": base.get("cnpj"),
                                        "nome_lojista": base.get("nome_lojista"),
                                        "contato_lojista": base.get("contato_lojista"),
                                        "data_meet": nova_data.strftime("%Y-%m-%d"),
                                        "hora_meet": nova_hora.strftime("%H:%M:%S"),
                                        "acao": acao_final,
                                        "status_meet": novo_status,
                                        "observacao": nova_obs
                                    }
                                    
                                    resp_up = supabase.table("meets").insert(dados_update).execute()
                                    if resp_up.data:
                                        # Limpa a busca para evitar dados desatualizados na tela
                                        st.session_state.pop("meets_buscados", None)
                                        st.success("Histórico atualizado com sucesso!")
                                        st.rerun()
