import streamlit as st
import pandas as pd
from datetime import datetime
from themes.theme import cabecalho_pagina, titulo_secao

def renderizar_linha_do_tempo(historicos, mapa_usuarios):
    if not historicos:
        st.info("Nenhuma interação registrada no histórico ainda.")
        return

    html = '<div style="margin-top: 15px; border-left: 2px solid #3f3f46; padding-left: 20px; margin-left: 10px;">'
    
    for h in historicos:
        fase = h.get('fase_na_epoca', 1)
        cor = "#3b82f6" if fase == 1 else ("#a855f7" if fase == 2 else "#f97316")
        nome = mapa_usuarios.get(h.get('usuario_id'), 'Usuário Desconhecido')
        
        dt_str = h.get('created_at', '')
        try:
            dt_obj = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            data_fmt = dt_obj.strftime('%d/%m/%Y %H:%M')
        except:
            data_fmt = dt_str[:16].replace('T', ' ') if dt_str else 'Data desconhecida'
        
        status = h.get('status_novo', 'Atualizado')
        obs = h.get('observacao', '')
        tentativa = h.get('tentativa')
        tent_str = f" | Tentativa: {tentativa}" if tentativa and fase == 1 else ""

        html += f"""
<div style="position: relative; margin-bottom: 20px;">
    <div style="position: absolute; left: -27px; top: 4px; background-color: {cor}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #1e1e1e;"></div>
    <div style="background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 5px; border: 1px solid rgba(255,255,255,0.1);">
        <div style="font-size: 14px; margin-bottom: 5px;">
            <span style="color: {cor}; font-weight: bold;">{status}</span>
            <span style="color: #a1a1aa; font-size: 12px; float: right;">{data_fmt}</span>
        </div>
        <div style="font-size: 13px; color: #e4e4e7; margin-bottom: 5px;">
            👤 <b>{nome}</b> (Fase {fase}){tent_str}
        </div>
        <div style="font-size: 13px; color: #a1a1aa; font-style: italic;">
            "{obs}"
        </div>
    </div>
</div>
"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def mostrar_esteira_leads(supabase):
    cabecalho_pagina("Esteira de Vendas", "Gerencie seus leads, avance as negociações e acompanhe o funil em tempo real.")

    uid = st.session_state.get("uid")
    nivel_acesso = int(st.session_state.get("nivel_acesso", 5))
    
    setor_usuario = st.session_state.get("setor_usuario")
    if not setor_usuario:
        try:
            resp_user = supabase.table("usuarios").select("setor").eq("id", uid).execute()
            if resp_user.data:
                setor_usuario = str(resp_user.data[0].get("setor", "")).strip().upper()
                st.session_state["setor_usuario"] = setor_usuario
            else:
                setor_usuario = ""
        except Exception:
            setor_usuario = ""

    @st.cache_data(show_spinner=False, ttl=300)
    def buscar_meus_leads_esteira(usuario_id, nivel, setor):
        try:
            query = supabase.table("leads").select("*")
            if nivel >= 5:
                if setor == "PRÉ-VENDA": query = query.eq("id_pre_venda", usuario_id)
                elif setor == "COMERCIAL": query = query.eq("id_especialista", usuario_id)
                elif setor == "BACKOFFICE": query = query.or_(f"fase_atual.eq.3,id_bko.eq.{usuario_id}")
                else: query = query.eq("responsavel_atual", usuario_id)
            else:
                query = query.limit(200)

            resp = query.order("updated_at", desc=True).execute()
            return resp.data if resp.data else []
        except Exception as e:
            return f"erro: {e}"

    @st.cache_data(show_spinner=False, ttl=300)
    def buscar_historico_lote(lead_ids):
        if not lead_ids: return {}
        try:
            resp = supabase.table("historico_leads").select("*").in_("lead_id", lead_ids).order("created_at", desc=False).execute()
            mapa = {}
            for h in (resp.data or []):
                lid = h['lead_id']
                if lid not in mapa: mapa[lid] = []
                mapa[lid].append(h)
            return mapa
        except Exception:
            return {}

    @st.cache_data(show_spinner=False, ttl=3600)
    def buscar_todos_usuarios():
        try:
            resp = supabase.table("usuarios").select("id, nome_completo").execute()
            return {u["id"]: u["nome_completo"] for u in resp.data} if resp.data else {}
        except Exception:
            return {}
            
    def formatar_cnpj(cnpj):
        if not cnpj:
            return '-'

        cnpj = ''.join(filter(str.isdigit, str(cnpj)))

        if len(cnpj) != 14:
            return cnpj

        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'

    @st.cache_data(show_spinner=False, ttl=3600)
    def buscar_especialistas():
        try:
            resp = supabase.table("usuarios").select("id, nome_completo").eq("nivel_acesso", 5).eq("setor", "COMERCIAL").eq("empresa_id", 1).eq("ativo", "TRUE").order("nome_completo").execute()
            return resp.data if resp.data else []
        except Exception:
            return []

    leads = buscar_meus_leads_esteira(uid, nivel_acesso, setor_usuario)
    especialistas = buscar_especialistas()
    mapa_todos_usuarios = buscar_todos_usuarios()

    if isinstance(leads, str) and leads.startswith("erro:"):
        st.error(f"Erro ao carregar seus leads: {leads}")
        return

    if not leads:
        st.success("Sua fila está vazia no momento!")
        return

    ids_dos_leads = [l["id"] for l in leads]
    mapa_historicos = buscar_historico_lote(ids_dos_leads)

    st.write(f"Você tem acesso a **{len(leads)}** leads na esteira.")
    st.write("---")

    mapa_especialistas = {esp["nome_completo"]: esp["id"] for esp in especialistas}
    
    status_fase1 = ["PROSPECTAR", "CONTATO REALIZADO", "QUALIFICADO", "MEET AGENDADO", "RAMO QUE NÃO FECHA", "CONTATO INVÁLIDO"]
    status_fase2 = ["MEET REALIZADO", "PROPOSTA APRESENTADA", "EM NEGOCIAÇÃO", "CLIENTE DESISTIU", "NEGADO", "CADASTRO"]
    status_fase3 = ["EM ANALISE", "AGUARDANDO DOCUMENTAÇÃO", "AGUARDANDO PAGAMENTO PRIVATE/LINK", "AGUARDANDO PAGAMENTO DE ADESÃO", "NEGADO COMPROVANTE", "NEGADO BIO", "NEGADO RISCO", "NEGADO PRAZO", "NEGADO PELO SUPERVISOR", "NEGADO SEM RETORNO", "NEGADO CONTRATO", "CLIENTE DESISTIU", "CONTRATO APROVADO, AGUARDANDO ASSINATURA", "ASSINADO", "PDV GERADO"]
    opcoes_meio = ["", "Whatsapp", "Ligação - VOX", "Ligação - Whatsapp", "Fortics", "E-mail", "Meet"]
    setores_ind = ["PROSPECÇÃO PRÓPRIA", "PRÉ-VENDAS BCARD", "OUTROS SETORES", "LEADS ÍMPAR", "INDICAÇÃO INTERNA"]

    for lead in leads:
        lead_id = lead["id"]
        status_atual = lead.get("status_atual", "PROSPECTAR")
        fase_atual = lead.get("fase_atual", 1)
        empresa = lead.get("nome_empresa", "Empresa não informada")
        
        pode_editar = False
        cor_status = "🔒" 
        is_gestao = (nivel_acesso < 5)

        if fase_atual == 1 and (is_gestao or setor_usuario == "PRÉ-VENDA"):
            pode_editar = True
            cor_status = "🔵"
        elif fase_atual == 2 and (is_gestao or setor_usuario == "COMERCIAL"):
            pode_editar = True
            cor_status = "🟣"
        elif fase_atual == 3 and (is_gestao or setor_usuario == "BACKOFFICE"):
            pode_editar = True
            cor_status = "🟠"

        if status_atual == "PDV GERADO":
            cor_status = "🏆"
            if nivel_acesso > 2:
                pode_editar = False

        with st.expander(f"{cor_status} {empresa} | Fase: {fase_atual} | Status: {status_atual}"):
            
            cor_destaque = "#3b82f6" if fase_atual == 1 else ("#a855f7" if fase_atual == 2 else ("#eab308" if cor_status == "🏆" else "#f97316"))
            st.markdown(f"""
<div style="border-left: 6px solid {cor_destaque}; background: linear-gradient(90deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.01) 100%); padding: 15px 20px; border-radius: 4px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="font-size: 11px; color: #a1a1aa; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 2px;">Fase {fase_atual} • Status Atual</div>
    <div style="font-size: 24px; font-weight: 900; color: {cor_destaque}; text-transform: uppercase; letter-spacing: 0.5px;">{status_atual}</div>
</div>
""", unsafe_allow_html=True)
            
            c_info1, c_info2, c_info3 = st.columns(3)
            with c_info1:
                st.caption("**Segmento:**")
                st.write(lead.get('segmento', '—'))
                st.caption("**CNPJ:**")
                st.write(formatar_cnpj(lead.get('cnpj', '-')))
            with c_info2:
                st.caption("**Telefone:**")
                st.write(lead.get('telefone', '—'))
                st.caption("**Lojista:**")
                st.write(lead.get('contato_loja', '-'))
            with c_info3:
                st.caption("**Faturamento:**")
                st.write(lead.get('faturamento_mensal', '—'))
                st.caption("**Nome Fantasia:**")
                st.write(lead.get('nome_empresa', '-'))
            
            st.write("---")

            if pode_editar:
                # --- FASE 1: PRÉ-VENDA ---
                if fase_atual == 1:
                    st.markdown("🎯 **Ação: Pré-Venda**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        novo_status = st.selectbox("Status *", status_fase1, index=status_fase1.index(status_atual) if status_atual in status_fase1 else 0, key=f"st1_{lead_id}")
                        houve_contato = st.selectbox("Houve Contato?", ["NÃO", "SIM"], key=f"ct1_{lead_id}")
                    with col2:
                        meio_contato = st.selectbox("Meio de Contato", opcoes_meio, key=f"meio1_{lead_id}")
                        ramo_nao_fecha = st.selectbox("Ramo não fecha?", ["NÃO", "SIM"], key=f"ramo1_{lead_id}")
                    with col3:
                        tentativa = st.number_input("Tentativa (Nº)", min_value=1, step=1, value=1, key=f"tent1_{lead_id}")
                    
                    especialista_selecionado = None
                    if novo_status == "MEET AGENDADO":
                        st.info("🔄 O lead será transferido para a Fase 2 (Especialista).")
                        if mapa_especialistas:
                            especialista_selecionado = st.selectbox("Selecione o Especialista *", list(mapa_especialistas.keys()), key=f"esp_{lead_id}")

                    obs = st.text_area("Observações (Resumo do Contato)", key=f"obs1_{lead_id}")
                    
                    if st.button("Salvar Pré-Venda", key=f"btn1_{lead_id}", type="primary"):
                        if novo_status == "MEET AGENDADO" and not especialista_selecionado:
                            st.warning("Selecione um Especialista para transferir o lead.")
                        else:
                            with st.spinner("Atualizando esteira..."):
                                update_lead = {"status_atual": novo_status, "updated_at": "now()"}
                                if novo_status == "MEET AGENDADO":
                                    id_esp = mapa_especialistas[especialista_selecionado]
                                    update_lead.update({"fase_atual": 2, "id_especialista": id_esp, "responsavel_atual": id_esp, "meio_fechamento": "MEET"})

                                supabase.table("leads").update(update_lead).eq("id", lead_id).execute()
                                supabase.table("historico_leads").insert({
                                    "lead_id": lead_id, "usuario_id": uid, "fase_na_epoca": 1, 
                                    "status_anterior": status_atual, "status_novo": novo_status,
                                    "tentativa": tentativa, "houve_contato": houve_contato, "observacao": obs
                                }).execute()

                                buscar_meus_leads_esteira.clear()
                                buscar_historico_lote.clear()
                                st.rerun()

                # --- FASE 2: COMERCIAL ---
                elif fase_atual == 2:
                    st.markdown("💼 **Ação: Especialista Comercial**")
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_status = st.selectbox("Avanço da Negociação *", status_fase2, index=status_fase2.index(status_atual) if status_atual in status_fase2 else 0, key=f"st2_{lead_id}")
                    with col2:
                        meio_contato = st.selectbox("Meio de Contato", opcoes_meio, index=opcoes_meio.index("Meet") if "Meet" in opcoes_meio else 0, key=f"meio2_{lead_id}")
                    
                    if novo_status == "CADASTRO":
                        st.info("🚀 **Fechamento concluído!** Ao salvar, este lead será enviado para a fila do Backoffice (BKO).")

                    obs = st.text_area("Observações da Negociação (Visível para o BKO)", key=f"obs2_{lead_id}")
                    
                    if st.button("Atualizar Negociação", key=f"btn2_{lead_id}", type="primary"):
                        with st.spinner("Gravando no banco..."):
                            update_lead = {"status_atual": novo_status, "updated_at": "now()"}
                            if novo_status == "CADASTRO":
                                update_lead["fase_atual"] = 3
                                update_lead["responsavel_atual"] = None 

                            supabase.table("leads").update(update_lead).eq("id", lead_id).execute()
                            supabase.table("historico_leads").insert({
                                "lead_id": lead_id, "usuario_id": uid, "fase_na_epoca": 2, 
                                "status_anterior": status_atual, "status_novo": novo_status,
                                "observacao": obs if obs else "Negociação atualizada."
                            }).execute()

                            buscar_meus_leads_esteira.clear()
                            buscar_historico_lote.clear()
                            st.rerun()
                
                # --- FASE 3: BKO ---
                elif fase_atual == 3:
                    st.markdown("📑 **Ação: Backoffice (BKO) - Auditoria e Cadastro**")
                    
                    c_bko1, c_bko2 = st.columns(2)
                    with c_bko1:
                        novo_status = st.selectbox("Status do BKO *", status_fase3, index=status_fase3.index(status_atual) if status_atual in status_fase3 else 0, key=f"st3_{lead_id}")
                        rede_individual = st.selectbox("Rede ou Individual?", ["", "Rede", "Individual"], index=["", "Rede", "Individual"].index(lead.get("rede_ou_individual")) if lead.get("rede_ou_individual") in ["Rede", "Individual"] else 0, key=f"rede_{lead_id}")
                        is_private = st.selectbox("PRIVATE?", ["NÃO", "SIM"], index=1 if lead.get("is_private")=="SIM" else 0, key=f"priv_{lead_id}")
                        private_pago = st.selectbox("PRIVATE PAGO?", ["NÃO", "SIM"], index=1 if lead.get("private_pago")=="SIM" else 0, key=f"privpago_{lead_id}")
                        valor_adesao = st.number_input("Valor da Adesão (R$)", min_value=0.0, step=10.0, value=float(lead.get("valor_adesao") or 0.0), key=f"val_{lead_id}")
                        adesao_paga = st.selectbox("ADESÃO PAGA?", ["NÃO", "SIM"], index=1 if lead.get("adesao_paga")=="SIM" else 0, key=f"adpaga_{lead_id}")
                        emitir_receber = st.selectbox("Emiti ou Apenas Receber?", ["", "EMITIR", "APENAS RECEBER"], index=["", "EMITIR", "APENAS RECEBER"].index(lead.get("emitir_ou_receber")) if lead.get("emitir_ou_receber") in ["EMITIR", "APENAS RECEBER"] else 0, key=f"emit_{lead_id}")

                    with c_bko2:
                        email_loja = st.text_input("E-mail Lojista", value=lead.get("email_loja", ""), key=f"email_{lead_id}")
                        contato_loja = st.text_input("Contato da Loja", value=lead.get("contato_loja", ""), key=f"contloja_{lead_id}")
                        responsavel_loja = st.text_input("Responsável da Loja", value=lead.get("responsavel_loja", ""), key=f"resploja_{lead_id}")
                        superv_resp = st.text_input("Supervisor Responsável", value=lead.get("supervisor_responsavel", ""), key=f"sup_{lead_id}")
                        
                        setor_indicacao = st.selectbox("Setor de Indicação", [""] + setores_ind, index=([""] + setores_ind).index(lead.get("setor_indicacao")) if lead.get("setor_indicacao") in setores_ind else 0, key=f"setind_{lead_id}")
                        meio_fechamento = st.selectbox("Por onde fechou?", [""] + opcoes_meio, index=([""] + opcoes_meio).index(lead.get("meio_fechamento")) if lead.get("meio_fechamento") in ([""] + opcoes_meio) else 0, key=f"meiof_{lead_id}")

                    if novo_status == "PDV GERADO":
                        st.success("🎉 **PDV GERADO?** Ao salvar como PDV GERADO, o cadastro é concluído e o lead será bloqueado!")

                    obs = st.text_area("Observações Finais e Auditoria", value=lead.get("observacao_final", ""), key=f"obs3_{lead_id}")
                    
                    if st.button("Salvar Cadastro (BKO)", key=f"btn3_{lead_id}", type="primary"):
                        with st.spinner("Atualizando base do BKO..."):
                            update_lead = {
                                "status_atual": novo_status,
                                "rede_ou_individual": rede_individual,
                                "is_private": is_private,
                                "private_pago": private_pago,
                                "valor_adesao": valor_adesao,
                                "adesao_paga": adesao_paga,
                                "emitir_ou_receber": emitir_receber,
                                "email_loja": email_loja,
                                "contato_loja": contato_loja,
                                "responsavel_loja": responsavel_loja,
                                "supervisor_responsavel": superv_resp,
                                "setor_indicacao": setor_indicacao,
                                "meio_fechamento": meio_fechamento,
                                "observacao_final": obs,
                                "updated_at": "now()"
                            }
                            
                            if not lead.get("id_bko"):
                                update_lead["id_bko"] = uid
                                update_lead["responsavel_atual"] = uid

                            if novo_status == "PDV GERADO":
                                update_lead["data_pdv_gerado"] = "now()"

                            try:
                                supabase.table("leads").update(update_lead).eq("id", lead_id).execute()
                                supabase.table("historico_leads").insert({
                                    "lead_id": lead_id, "usuario_id": uid, "fase_na_epoca": 3, 
                                    "status_anterior": status_atual, "status_novo": novo_status,
                                    "observacao": obs if obs else "Atualização de BKO"
                                }).execute()

                                buscar_meus_leads_esteira.clear()
                                buscar_historico_lote.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar: {e}")

            else:
                if status_atual == "PDV GERADO":
                    st.success("🏆 Este lead já completou a esteira (PDV Gerado). Edição restrita à gestão.")
                else:
                    st.info("🔍 Este lead está em uma fase restrita a outro setor ou você não tem permissão para editá-lo.")

            st.write("")
            st.markdown("### 🕒 Histórico de Interações")
            historico_deste_lead = mapa_historicos.get(lead_id, [])
            renderizar_linha_do_tempo(historico_deste_lead, mapa_todos_usuarios)
