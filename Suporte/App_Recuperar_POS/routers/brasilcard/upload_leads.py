import streamlit as st
import pandas as pd
import re
from themes.theme import cabecalho_pagina, titulo_secao

def mostrar_upload_leads(supabase):
    cabecalho_pagina("Gestão e Distribuição de Leads", "Importe novas bases e atribua os contatos para a equipe de Pré-Venda.")

    nivel_atual = st.session_state.get("nivel_acesso", 5)
    if nivel_atual > 3: 
        st.warning("Você não tem permissão para acessar a gestão de leads.")
        return

    aba_importar, aba_distribuir = st.tabs(["📤 Importar Planilha", "👥 Distribuir Leads"])

    # ==========================================
    # ABA 1: IMPORTAR LEADS
    # ==========================================
    with aba_importar:
        with st.container(border=True):
            titulo_secao("Upload de Nova Base")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                origem_lead = st.selectbox("Origem dos Leads", ["LEADS-ÍMPAR", "CAMPANHA", "VOX", "INTERNO", "MARKETING", "OUTROS"])
            with c2:
                arquivo = st.file_uploader("Selecione a planilha (.xlsx ou .csv)", type=["xlsx", "csv"])

        if arquivo is not None:
            try:
                with st.spinner("Lendo arquivo..."):
                    if arquivo.name.endswith(".csv"):
                        df = pd.read_csv(arquivo)
                    else:
                        df = pd.read_excel(arquivo)
                
                st.write(f"✅ Arquivo carregado com **{len(df)}** linhas.")
                st.info("Mapeie as colunas da sua planilha com os campos do sistema:")
                
                colunas_planilha = ["Não importar"] + list(df.columns)
                
                def auto_index(termo):
                    for i, col in enumerate(colunas_planilha):
                        if termo.lower() in col.lower():
                            return i
                    return 0

                m1, m2, m3 = st.columns(3)
                with m1:
                    col_cnpj = st.selectbox("Coluna de CNPJ *", colunas_planilha, index=auto_index("cnpj"))
                    col_empresa = st.selectbox("Nome da Empresa", colunas_planilha, index=auto_index("empresa"))
                with m2:
                    col_contato = st.selectbox("Nome do Contato", colunas_planilha, index=auto_index("completo"))
                    col_telefone = st.selectbox("Telefone", colunas_planilha, index=auto_index("phone"))
                with m3:
                    col_segmento = st.selectbox("Segmento/Ramo", colunas_planilha, index=auto_index("segmento"))
                    col_faturamento = st.selectbox("Faturamento", colunas_planilha, index=auto_index("faturamento"))

                if st.button("Processar e Salvar Leads", type="primary"):
                    if col_cnpj == "Não importar":
                        st.error("A coluna de CNPJ é obrigatória para a importação.")
                    else:
                        with st.spinner("Processando e validando CNPJs..."):
                            df_valido = df.copy()
                            df_valido["cnpj_limpo"] = df_valido[col_cnpj].astype(str).apply(lambda x: re.sub(r"\D", "", x))
                            df_valido = df_valido[df_valido["cnpj_limpo"].str.len() >= 14] 

                            cnpjs_planilha = df_valido["cnpj_limpo"].tolist()

                            try:
                                resp_existentes = supabase.table("leads").select("cnpj").in_("cnpj", cnpjs_planilha).execute()
                                cnpjs_existentes = [linha["cnpj"] for linha in resp_existentes.data]
                            except Exception:
                                cnpjs_existentes = []

                            df_novos = df_valido[~df_valido["cnpj_limpo"].isin(cnpjs_existentes)]

                            if df_novos.empty:
                                st.warning("Todos os CNPJs válidos desta planilha já existem no banco de dados. Nenhum lead novo foi importado.")
                            else:
                                lote_insercao = []
                                for _, row in df_novos.iterrows():
                                    lead_data = {
                                        "cnpj": row["cnpj_limpo"],
                                        "origem": origem_lead,
                                        "fase_atual": 1,
                                        "status_atual": "PROSPECTAR"
                                    }
                                    if col_empresa != "Não importar": lead_data["nome_empresa"] = str(row[col_empresa]).strip()
                                    if col_contato != "Não importar": lead_data["contato_loja"] = str(row[col_contato]).strip()
                                    if col_telefone != "Não importar": lead_data["telefone"] = str(row[col_telefone]).strip()
                                    if col_segmento != "Não importar": lead_data["segmento"] = str(row[col_segmento]).strip().title()
                                    
                                    # Formatação elegante automática do faturamento
                                    if col_faturamento != "Não importar": 
                                        fat_bruto = str(row[col_faturamento]).strip()
                                        if fat_bruto.lower() != 'nan':
                                            # Troca _ por espaço e ajeita R$
                                            fat_limpo = fat_bruto.replace("_", " ")
                                            fat_limpo = re.sub(r'(?i)\bde\s*r\$', 'R$ ', fat_limpo)
                                            lead_data["faturamento_mensal"] = fat_limpo.title()
                                        else:
                                            lead_data["faturamento_mensal"] = ""
                                    
                                    lote_insercao.append(lead_data)

                                try:
                                    supabase.table("leads").insert(lote_insercao).execute()
                                    st.success(f"🚀 Importação concluída! {len(lote_insercao)} novos leads foram adicionados à base.")
                                    st.balloons()
                                except Exception as e:
                                    st.error(f"Erro ao inserir no banco: {e}")

            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")

    # ==========================================
    # ABA 2: DISTRIBUIR LEADS (PRÉ-VENDA)
    # ==========================================
    with aba_distribuir:
        titulo_secao("Distribuir Leads sem Responsável")

        @st.cache_data(show_spinner=False, ttl=60)
        def buscar_operadores():
            try:
                resp = supabase.table("usuarios").select("id, nome_completo").eq("nivel_acesso", 5).eq("empresa_id", 1).eq("setor", "PRÉ-VENDA").eq("ativo", "TRUE").order("nome_completo").execute()
                return resp.data if resp.data else []
            except Exception:
                return []

        operadores = buscar_operadores()
        
        # Agora buscamos também segmento e faturamento
        try:
            resp_leads = supabase.table("leads").select("id, cnpj, nome_empresa, origem, segmento, faturamento_mensal, created_at").eq("fase_atual", 1).is_("id_pre_venda", "null").order("created_at").execute()
            leads_livres = resp_leads.data if resp_leads.data else []
        except Exception:
            leads_livres = []
            st.error("Erro ao buscar leads livres.")

        if not operadores:
            st.warning("Nenhum operador de Pré-Venda encontrado no sistema.")
        elif not leads_livres:
            st.info("🎉 Excelente! Todos os leads importados já foram distribuídos e possuem um responsável.")
        else:
            st.write(f"Fila total: **{len(leads_livres)}** leads aguardando distribuição.")
            st.write("---")
            
            # 1. ESCOLHA DA ESTRATÉGIA DE DISTRIBUIÇÃO
            tipo_distribuicao = st.selectbox("Estratégia de Distribuição", ["Aleatória / Fila Padrão", "Por Segmento / Ramo", "Por Faturamento"])
            
            leads_alvo_filtro = leads_livres # Padrão: todos
            
            if tipo_distribuicao == "Por Segmento / Ramo":
                # Extrai os segmentos únicos, removendo vazios e "Nan"
                segmentos_unicos = sorted(list(set([l.get("segmento") for l in leads_livres if l.get("segmento") and str(l.get("segmento")).lower() not in ["nan", "", "none"]])))
                
                if not segmentos_unicos:
                    st.warning("Nenhum segmento preenchido nos leads da fila.")
                    leads_alvo_filtro = []
                else:
                    seg_selecionado = st.selectbox("Qual segmento deseja distribuir?", segmentos_unicos)
                    leads_alvo_filtro = [l for l in leads_livres if l.get("segmento") == seg_selecionado]
            
            elif tipo_distribuicao == "Por Faturamento":
                # Extrai os faturamentos únicos
                faturamentos_unicos = sorted(list(set([l.get("faturamento_mensal") for l in leads_livres if l.get("faturamento_mensal") and str(l.get("faturamento_mensal")).lower() not in ["nan", "", "none"]])))
                
                if not faturamentos_unicos:
                    st.warning("Nenhum faturamento preenchido nos leads da fila.")
                    leads_alvo_filtro = []
                else:
                    fat_selecionado = st.selectbox("Qual faixa de faturamento deseja distribuir?", faturamentos_unicos)
                    leads_alvo_filtro = [l for l in leads_livres if l.get("faturamento_mensal") == fat_selecionado]

            # 2. FORMULÁRIO DE ATRIBUIÇÃO
            qtd_maxima = len(leads_alvo_filtro)
            
            if qtd_maxima > 0:
                st.success(f"📌 {qtd_maxima} leads disponíveis para esta seleção.")
                
                with st.form("form_distribuicao"):
                    c_dist1, c_dist2 = st.columns(2)
                    
                    with c_dist1:
                        mapa_ops = {op["nome_completo"]: op["id"] for op in operadores}
                        op_selecionado = st.selectbox("Selecione o Operador de Pré-Venda", list(mapa_ops.keys()))
                    
                    with c_dist2:
                        qtd_atribuir = st.number_input(
                            "Quantidade para atribuir:", 
                            min_value=1, 
                            max_value=qtd_maxima, 
                            value=min(20, qtd_maxima)
                        )
                    
                    btn_atribuir = st.form_submit_button("Distribuir Leads", type="primary")

                    if btn_atribuir:
                        # Corta a lista baseada na quantidade escolhida e no filtro
                        leads_para_enviar = leads_alvo_filtro[:qtd_atribuir]
                        ids_para_atualizar = [l["id"] for l in leads_para_enviar]
                        id_operador_banco = mapa_ops[op_selecionado]

                        try:
                            with st.spinner("Atribuindo leads..."):
                                supabase.table("leads").update({
                                    "id_pre_venda": id_operador_banco,
                                    "responsavel_atual": id_operador_banco,
                                    "updated_at": "now()"
                                }).in_("id", ids_para_atualizar).execute()
                            
                            st.success(f"✅ {qtd_atribuir} leads foram atribuídos para {op_selecionado} com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao distribuir leads: {e}")
