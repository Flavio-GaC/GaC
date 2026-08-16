import streamlit as st
from datetime import datetime
import re

from themes.theme import cabecalho_pagina, titulo_secao

def mostrar_meet(supabase):
    cabecalho_pagina("Gestão de Meets", "Acompanhe e registre o histórico de agendamentos e contatos.")

    aba_novo, aba_atualizar = st.tabs(["📝 Novo Meet", "🔄 Atualizar / Histórico"])

    usuario_id = st.session_state.get("uid")

    # Busca o setor do usuário logado para definir se usa CNPJ (COMERCIAL) ou PDV (Outros)
    try:
        resp_user = supabase.table("usuarios").select("setor").eq("id", usuario_id).execute()
        dados_logado = resp_user.data[0]
        setor_logado = dados_logado.get("setor").upper()
    except:
        setor_logado = False

    # Regra: Setor COMERCIAL usa CNPJ, qualquer outro setor usa PDV
    usa_cnpj = (setor_logado == "COMERCIAL")

    # ==========================================
    # ABA 1: CRIAR NOVO MEET
    # ==========================================
    with aba_novo:
        with st.form("form_novo_meet", clear_on_submit=True):
            titulo_secao("Abertura de Novo Agendamento")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if usa_cnpj:
                    input_identificador = st.text_input("CNPJ *", max_chars=18, placeholder="XX.XXX.XXX/XXXX-XX")
                else:
                    input_identificador = st.text_input("Código PDV *", max_chars=10, placeholder="Apenas números (máx. 10)")
                
                nome_lojista = st.text_input("Nome Lojista *")
            
            with c2:
                input_contato_lojista = st.text_input("Contato do Lojista *", max_chars=15)
                data_meet = st.date_input("Data do Meet", format="DD/MM/YYYY")
            
            with c3:
                hora_meet = st.time_input("Hora do Meet")
                status_meet = st.selectbox("Status", ["Aguardando Horário", "Em Andamento", "Concluído", "Cancelado"])
            
            acao = st.selectbox("Ação", ["AGENDADO", "REAGENDADO"])
            observacao = st.text_area("Observações")

            submit_novo = st.form_submit_button("Criar Meet", type="primary")

            if submit_novo:
                identificador_limpo = re.sub(r"\D", "", input_identificador)
                contato_lojista = re.sub(r"\D", "", input_contato_lojista)

                # Validações baseadas no setor
                if usa_cnpj:
                    if len(identificador_limpo) < 14:
                        st.error("Erro: CNPJ inválido. Digite os 14 números.")
                        st.stop()
                else:
                    if not identificador_limpo or len(identificador_limpo) > 10:
                        st.error("Erro: PDV inválido. Digite apenas números (máximo de 10 caracteres).")
                        st.stop()

                if not contato_lojista:
                    st.error("Erro: Contato inválido.")
                elif not nome_lojista:
                    st.error("Erro: Preencha o nome do lojista.")
                else:
                    try:
                        with st.spinner("Gerando Meet..."):
                            # Salva na coluna correta de acordo com o setor
                            dados = {
                                "usuario_id": usuario_id,
                                "cnpj": identificador_limpo if usa_cnpj else None,
                                "pdv": identificador_limpo if not usa_cnpj else None,
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
                                label_id = "CNPJ" if usa_cnpj else "PDV"
                                st.success(f"✅ Meet gerado com sucesso! {label_id}: **{identificador_limpo}** | Meet ID: **{novo_id}**")
                    except Exception as e:
                        st.error(f"Erro ao criar meet: {e}")

    # ==========================================
    # ABA 2: ATUALIZAR E VER HISTÓRICO
    # ==========================================
    with aba_atualizar:
        titulo_secao("Consultar e Editar")
        
        label_busca_param = "Por CNPJ" if usa_cnpj else "Por PDV"
        
        c_modo, c_param, c_btn = st.columns([2, 3, 1])
        with c_modo:
            modo_busca = st.selectbox("Modo de Busca", ["Meus Meets", label_busca_param])
        with c_param:
            if modo_busca == "Meus Meets":
                limite = st.selectbox("Quantidade de Meets", [10, 20, 50])
                input_busca_param = ""
            else:
                placeholder_txt = "Somente números ou formatado" if usa_cnpj else "Somente números (máx. 10)"
                max_c = 18 if usa_cnpj else 10
                input_busca_param = st.text_input(f"Digite o {label_busca_param.replace('Por ', '')}", max_chars=max_c, placeholder=placeholder_txt)
                limite = 50
        with c_btn:
            st.write("")
            st.write("")
            btn_buscar = st.button("Buscar", use_container_width=True, type="primary")

        if btn_buscar or "meets_buscados" in st.session_state:
            if btn_buscar:
                with st.spinner("Buscando..."):
                    try:
                        if modo_busca == "Meus Meets":
                            resp = supabase.table("meets").select("*").eq("usuario_id", usuario_id).order("created_at", desc=True).execute()
                        else:
                            param_limpo = re.sub(r"\D", "", input_busca_param)
                            if param_limpo:
                                # Busca na coluna correta (cnpj ou pdv) dependendo do setor
                                coluna_busca = "cnpj" if usa_cnpj else "pdv"
                                resp = supabase.table("meets").select("*").eq(coluna_busca, param_limpo).order("created_at", desc=True).execute()
                            else:
                                resp = type('obj', (object,), {'data': []})
                        
                        st.session_state["meets_buscados"] = resp.data
                    except Exception as e:
                        st.error(f"Erro na busca: {e}")
                        st.session_state["meets_buscados"] = []

            dados_busca = st.session_state.get("meets_buscados", [])
            
            if not dados_busca:
                if btn_buscar: st.warning("Nenhum Meet encontrado.")
            else:
                meets_agrupados = {}
                for linha in dados_busca:
                    mid = linha["meet_id"]
                    if mid not in meets_agrupados:
                        meets_agrupados[mid] = []
                    meets_agrupados[mid].append(linha)
                
                lista_mids = list(meets_agrupados.keys())[:limite]

                st.write("---")
                st.caption(f"Exibindo **{len(lista_mids)}** Meet(s).")
                
                for mid in lista_mids:
                    historico = meets_agrupados[mid]
                    historico.reverse()
                    
                    base = historico[0]
                    status_atual = historico[-1]["status_meet"] 
                    
                    # Identifica qual valor exibir no card (CNPJ ou PDV)
                    valor_identificador = base.get('cnpj') if base.get('cnpj') else base.get('pdv', 'N/A')
                    titulo_legenda_id = "CNPJ" if base.get('cnpj') else "PDV"
                    
                    with st.expander(f"📍 Meet {mid} | {base.get('nome_lojista', 'N/A')} | Status: {status_atual}"):
                        st.caption(f"**{titulo_legenda_id}:** {valor_identificador} | **Contato:** {base.get('contato_lojista', 'N/A')}")
                        st.write("")
                        
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
                        
                        with st.form(f"form_up_{mid}", clear_on_submit=True):
                            titulo_secao("Adicionar Nova Interação")
                            c1, c2, c3 = st.columns(3)
                            with c1: 
                                nova_acao = st.selectbox("Ação Realizada", ["AGENDADO", "REAGENDADO"], key=f"acao_{mid}")
                            with c2: 
                                novo_status = st.selectbox("Novo Status", ["Aguardando Horário", "Em Andamento", "Concluído", "Cancelado", "Cancelado No-Show"], key=f"status_{mid}")
                            with c3:
                                st.write("")
                                nova_data = st.date_input("Nova Data", format="DD/MM/YYYY", key=f"dt_{mid}")
                                nova_hora = st.time_input("Nova Hora", key=f"hr_{mid}")
                            
                            nova_obs = st.text_area("Nova Observação (Opcional)", key=f"obs_{mid}")
                            submit_up = st.form_submit_button("Salvar Histórico", type="primary")
                            
                            if submit_up:
                                with st.spinner("Processando..."):
                                    ultimo_registro_id = historico[-1]["id"]
                                    status_anterior_atual = historico[-1]["status_meet"]

                                    # ==========================================
                                    # REGRA 1: TRATAMENTO PARA REAGENDAMENTO
                                    # ==========================================
                                    if nova_acao == "REAGENDADO":
                                        # Valida se o usuário alterou o status atual para Cancelado ou Cancelado No-Show
                                        status_permitidos_reagendamento = ["Cancelado", "Cancelado No-Show"]
                                        
                                        if novo_status not in status_permitidos_reagendamento:
                                            st.warning("⚠️ Para reagendar, você deve primeiro alterar o status deste meet para **'Cancelado'** ou **'Cancelado No-Show'**.")
                                            st.stop()
                                        
                                        # Se passou na validação:
                                        # 1. Atualiza o registro anterior com o status de cancelamento escolhido e a ação REAGENDADO
                                        supabase.table("meets").update({
                                            "status_meet": novo_status,
                                            "acao": "REAGENDADO"
                                        }).eq("id", ultimo_registro_id).execute()

                                        # 2. Insere a nova linha na timeline como AGENDADO com o mesmo meet_id
                                        dados_novo = {
                                            "meet_id": mid,
                                            "usuario_id": usuario_id,
                                            "cnpj": base.get("cnpj"),
                                            "pdv": base.get("pdv"),
                                            "nome_lojista": base.get("nome_lojista"),
                                            "contato_lojista": base.get("contato_lojista"),
                                            "data_meet": nova_data.strftime("%Y-%m-%d"),
                                            "hora_meet": nova_hora.strftime("%H:%M:%S"),
                                            "acao": "AGENDADO",
                                            "status_meet": "Aguardando Horário", # Novo agendamento começa aguardando
                                            "observacao": nova_obs
                                        }
                                        
                                        resp_up = supabase.table("meets").insert(dados_novo).execute()
                                        if resp_up.data:
                                            st.session_state.pop("meets_buscados", None)
                                            st.success("Meet reagendado com sucesso! Nova linha criada na timeline.")
                                            st.rerun()

                                    # ==========================================
                                    # REGRA 2: APENAS ATUALIZAÇÃO DE STATUS/DADOS
                                    # ==========================================
                                    else:
                                        dados_update = {
                                            "status_meet": novo_status,
                                            "acao": nova_acao,
                                            "observacao": nova_obs if nova_obs else historico[-1].get("observacao")
                                        }
                                        
                                        supabase.table("meets").update(dados_update).eq("id", ultimo_registro_id).execute()
                                        
                                        st.session_state.pop("meets_buscados", None)
                                        st.success("Status atualizado com sucesso no mesmo registro!")
                                        st.rerun()
