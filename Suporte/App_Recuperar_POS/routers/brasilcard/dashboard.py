import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_card_dash(titulo, valor, percentual_texto, cor_fundo, cor_texto="white"):
    st.markdown(f"""
    <div style="background-color: {cor_fundo}; padding: 15px; border-radius: 8px; color: {cor_texto}; 
                text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px;">
        <p style="margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">{titulo}</p>
        <h2 style="margin: 5px 0 5px 0; font-size: 32px; font-weight: bold;">{valor}</h2>
        <p style="margin: 0; font-size: 11px; opacity: 0.8; font-style: italic;">{percentual_texto}</p>
    </div>
    """, unsafe_allow_html=True)

# Cache otimizado: guarda os dados pesados na memória por 10 minutos (600 segundos) para evitar requisições ao Supabase
@st.cache_data(show_spinner=False, ttl=600)
def buscar_dados_dashboard(_supabase, dt_ini, dt_fim):
    # 1. Busca os Leads do período selecionado
    leads_extraidos = []
    offset = 0
    while True:
        resp = _supabase.table("leads").select("id, status_atual, responsavel_atual").gte("created_at", f"{dt_ini} 00:00:00").lte("created_at", f"{dt_fim} 23:59:59").range(offset, offset + 999).execute()
        if not resp.data: break
        leads_extraidos.extend(resp.data)
        if len(resp.data) < 1000: break
        offset += 1000

    # 2. Busca o Histórico (Tentativas) APENAS para os leads da lista acima
    historico_extraido = []
    if leads_extraidos:
        lista_ids_leads = [lead['id'] for lead in leads_extraidos]
        tamanho_lote = 200
        
        # Processa em lotes para não estourar o limite de parâmetros da API
        for i in range(0, len(lista_ids_leads), tamanho_lote):
            lote_ids = lista_ids_leads[i : i + tamanho_lote]
            
            resp = (
                _supabase.table("historico_leads")
                .select("id, usuario_id, lead_id, created_at, status_novo, tentativa")
                .in_("lead_id", lote_ids)
                .gte("created_at", f"{dt_ini} 00:00:00")
                .lte("created_at", f"{dt_fim} 23:59:59")
                .execute()
            )
            
            if resp.data:
                historico_extraido.extend(resp.data)

    return leads_extraidos, historico_extraido

@st.cache_data(show_spinner=False, ttl=3600)
@st.cache_data(show_spinner=False, ttl=3600)
def buscar_usuarios_dash(_supabase):
    try:
        # 1. Traz do banco apenas os usuários da empresa_id = 1
        resp = _supabase.table("usuarios").select("id, nome_completo, setor").eq("empresa_id", 1).eq("ativo", True).eq("nivel_acesso", 5).in_("setor", ["COMERCIAL", "PRÉ-VENDA"]).execute()
        if not resp.data: return []
        
        # 2. Remove da lista qualquer usuário que o nome comece com "test"
        usuarios_validos = []
        for u in resp.data:
            nome = str(u.get("nome_completo", "")).strip().lower()
            if not nome.startswith("test"):
                usuarios_validos.append(u)
                
        return usuarios_validos
    except Exception:
        return []


def mostrar_dashboard(supabase):
    st.markdown("### 📊 Dashboard de Performance")
    st.caption("Visão gerencial de métricas, leads e engajamento da equipe.")

    # ==========================================
    # 1. FILTROS
    # ==========================================
    usuarios_bd = buscar_usuarios_dash(supabase)
    mapa_usuarios = {u['nome_completo']: u['id'] for u in usuarios_bd}
    lista_nomes = sorted(list(mapa_usuarios.keys()))

    with st.container(border=True):
        col_d1, col_d2, col_consul = st.columns([1, 1, 2])
        with col_d1:
            dt_inicio = st.date_input("Data Inicial", value=datetime.now() - timedelta(days=7), format="DD/MM/YYYY")
        with col_d2:
            dt_final = st.date_input("Data Final", value=datetime.now(), format="DD/MM/YYYY")
        with col_consul:
            consultores_selecionados = st.multiselect("Filtrar Consultores (Deixe vazio para ver todos)", options=lista_nomes)
    
    aba_geral, aba_freq = st.tabs(["📊 Métricas Gerais", "⏱️ Frequência de Envios"])
    
    with aba_geral:
        # ==========================================
        # 2. PROCESSAMENTO DE DADOS (PANDAS NA MEMÓRIA CLIENTE)
        # ==========================================
        with st.spinner("Processando métricas..."):
            dados_leads, dados_hist = buscar_dados_dashboard(supabase, dt_inicio, dt_final)
            
            df_leads = pd.DataFrame(dados_leads) if dados_leads else pd.DataFrame(columns=["id", "status_atual", "responsavel_atual"])
            df_hist = pd.DataFrame(dados_hist) if dados_hist else pd.DataFrame(columns=["id", "usuario_id"])

            if consultores_selecionados:
                ids_selecionados = [mapa_usuarios[nome] for nome in consultores_selecionados]
                df_leads = df_leads[df_leads['responsavel_atual'].isin(ids_selecionados)]
                df_hist = df_hist[df_hist['usuario_id'].isin(ids_selecionados)]

            if not df_leads.empty: df_leads['status_atual'] = df_leads['status_atual'].fillna("")

            total_leads = df_leads['id'].nunique() if not df_leads.empty else 0
            total_tentativas = len(df_hist)
            
            if not df_leads.empty:
                total_contatos = len(df_leads[df_leads['status_atual'] != "REALIZADO - MEET"])
                tot_sem_perfil = len(df_leads[df_leads['status_atual'].str.startswith("SEM PERFIL", na=False)])
                tot_invalido = len(df_leads[df_leads['status_atual'].str.startswith("INVALIDO", na=False)])
                tot_sem_interesse = len(df_leads[df_leads['status_atual'].str.startswith("SEM INTERESSE", na=False)])
                tot_sem_retorno = len(df_leads[df_leads['status_atual'].str.startswith("SEM RETORNO", na=False)])
                tot_tem_interesse = len(df_leads[df_leads['status_atual'].str.startswith("TEM INTERESSE", na=False)])
                tot_reagendamento = len(df_leads[df_leads['status_atual'].str.startswith("REAGENDAMENTO", na=False)])
                tot_realizado = len(df_leads[df_leads['status_atual'].str.startswith("REALIZADO", na=False)])
            else:
                total_contatos = tot_sem_perfil = tot_invalido = tot_sem_interesse = tot_sem_retorno = tot_tem_interesse = tot_reagendamento = tot_realizado = 0

        # ==========================================
        # 3. RENDERIZAÇÃO DOS CARDS (DEGRADÊ HORIZONTAL)
        # ==========================================
        st.write("")
        
        # Linha 1
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: render_card_dash("Leads", str(total_leads), "Únicos no período", "#0f4d7e", "white")
        with c2: render_card_dash("Contatos", str(total_contatos), "Exceto Realizado-Meet", "#0f4d7e", "#1e1e1e")
        with c3: render_card_dash("Tentativas", str(total_tentativas), "Histórico registrado", "#0f4d7e", "white")
        with c4: render_card_dash("Sem Perfil", str(tot_sem_perfil), "Métrica consolidada", "#0f4d7e", "#1e1e1e")
        with c5: render_card_dash("Inválido", str(tot_invalido), "Métrica consolidada", "#0f4d7e", "white")

        # Linha 2
        c6, c7, c8, c9, c10 = st.columns(5)
        with c6: render_card_dash("Sem Interesse", str(tot_sem_interesse), "Métrica consolidada", "#0f4d7e", "white")
        with c7: render_card_dash("Sem Retorno", str(tot_sem_retorno), "Métrica consolidada", "#0f4d7e", "white")
        with c8: render_card_dash("Tem Interesse", str(tot_tem_interesse), "Métrica consolidada", "#0f4d7e", "#1e1e1e")
        with c9: render_card_dash("Reagendamento", str(tot_reagendamento), "Métrica consolidada", "#0f4d7e", "#1e1e1e")
        with c10: render_card_dash("Realizado", str(tot_realizado), "Métrica consolidada", "#0f4d7e", "white")

        # ==========================================
        # 4. MATRIZ DE DESEMPENHO (NATIVA STREAMLIT)
        # ==========================================
        st.write("---")
        st.markdown("#### Matriz de Desempenho por Consultor")

        if consultores_selecionados:
            usuarios_tabela = [u for u in usuarios_bd if u['nome_completo'] in consultores_selecionados]
        else:
            ids_ativos_leads = df_leads['responsavel_atual'].unique().tolist() if not df_leads.empty else []
            ids_ativos_hist = df_hist['usuario_id'].unique().tolist() if not df_hist.empty else []
            ids_ativos = set(ids_ativos_leads + ids_ativos_hist)
            usuarios_tabela = [u for u in usuarios_bd if u['id'] in ids_ativos]

        if not usuarios_tabela:
            st.info("Nenhuma atividade registrada para os filtros selecionados.")
        else:
            dados_matriz = []
            for u in sorted(usuarios_tabela, key=lambda x: x['nome_completo']):
                uid = u['id']
                nome = u['nome_completo'].upper()
                
                setor_cru = str(u.get('setor', '')).strip().upper()
                if setor_cru == "COMERCIAL": cargo = "Especialista"
                elif setor_cru == "PRÉ-VENDA": cargo = "Pré-Venda"
                else: cargo = setor_cru.title() if setor_cru else "Sem Setor"

                df_u_leads = df_leads[df_leads['responsavel_atual'] == uid] if not df_leads.empty else pd.DataFrame(columns=["status_atual"])
                df_u_hist = df_hist[df_hist['usuario_id'] == uid] if not df_hist.empty else []

                u_leads = df_u_leads['id'].nunique() if not df_u_leads.empty else 0
                u_tentativas = len(df_u_hist)
                
                if not df_u_leads.empty:
                    u_contatos = len(df_u_leads[df_u_leads['status_atual'] != "REALIZADO - MEET"])
                    u_sem_perfil = len(df_u_leads[df_u_leads['status_atual'].str.startswith("SEM PERFIL", na=False)])
                    u_invalido = len(df_u_leads[df_u_leads['status_atual'].str.startswith("INVALIDO", na=False)])
                    u_sem_interesse = len(df_u_leads[df_u_leads['status_atual'].str.startswith("SEM INTERESSE", na=False)])
                    u_sem_retorno = len(df_u_leads[df_u_leads['status_atual'].str.startswith("SEM RETORNO", na=False)])
                    u_tem_interesse = len(df_u_leads[df_u_leads['status_atual'].str.startswith("TEM INTERESSE", na=False)])
                    u_reagendamento = len(df_u_leads[df_u_leads['status_atual'].str.startswith("REAGENDAMENTO", na=False)])
                    u_realizado = len(df_u_leads[df_u_leads['status_atual'].str.startswith("REALIZADO", na=False)])
                else:
                    u_contatos = u_sem_perfil = u_invalido = u_sem_interesse = u_sem_retorno = u_tem_interesse = u_reagendamento = u_realizado = 0

                # Função auxiliar matemática para calcular e formatar o percentual
                def formatar_com_percentual(valor, total):
                    if total == 0:
                        return f"{valor} (0,00%)"
                    percentual = (valor / total) * 100
                    return f"{valor} ({percentual:.2f}%)".replace(".", ",")

                # Adiciona os dados como um dicionário para a matriz do Pandas
                dados_matriz.append({
                    "NOME DO CONSULTOR": nome,
                    "CARGO": cargo,
                    "LEADS": u_leads,
                    "TENTATIVAS": u_tentativas,
                    "CONTATOS": formatar_com_percentual(u_contatos, u_leads),
                    "S/ PERFIL": formatar_com_percentual(u_sem_perfil, u_leads),
                    "INVÁLIDO": formatar_com_percentual(u_invalido, u_leads),
                    "S/ INTERESSE": formatar_com_percentual(u_sem_interesse, u_leads),
                    "S/ RETORNO": formatar_com_percentual(u_sem_retorno, u_leads),
                    "T/ INTERESSE": formatar_com_percentual(u_tem_interesse, u_leads),
                    "REAGEND.": formatar_com_percentual(u_reagendamento, u_leads),
                    "REALIZADO": formatar_com_percentual(u_realizado, u_leads)
                })

            # Renderiza a matriz nativa do Streamlit
            df_matriz = pd.DataFrame(dados_matriz)
            st.dataframe(df_matriz, use_container_width=True, hide_index=True)

    with aba_freq:
        st.markdown("### Análise de Engajamento e Cohort de Contatos")
        st.caption("Acompanhe o volume de envios e a velocidade de retorno por tentativa.")

        # Garantir que temos histórico carregado
        with st.spinner("Processando histórico temporal..."):
            dados_leads, dados_hist = buscar_dados_dashboard(supabase, dt_inicio, dt_final)
            df_h = pd.DataFrame(dados_hist) if dados_hist else pd.DataFrame()
            
        if df_h.empty:
            st.info("Não há histórico de contatos registrado para os filtros selecionados.")
        else:
            # 1. Aplicar os filtros do menu suspenso (Consultores) se houver
            if consultores_selecionados:
                ids_selecionados = [mapa_usuarios[nome] for nome in consultores_selecionados]
                df_h = df_h[df_h['usuario_id'].isin(ids_selecionados)]

            if not df_h.empty:
                # 2. Preparar dados para o tempo médio
                df_h['created_at'] = pd.to_datetime(df_h['created_at'])
                df_h['tentativa'] = pd.to_numeric(df_h['tentativa'], errors='coerce').fillna(1).astype(int)
                df_h = df_h.sort_values(by=['lead_id', 'tentativa'])

                # Calcula a diferença em dias corridos comparando a tentativa atual com a anterior DO MESMO LEAD
                df_h['data_anterior'] = df_h.groupby('lead_id')['created_at'].shift(1)
                df_h['dias_intervalo'] = (df_h['created_at'] - df_h['data_anterior']).dt.days

                # Função de prateleiras (Bins)
                def classificar_tempo(dias):
                    if pd.isna(dias): return None
                    if dias == 0: return "MESMO DIA"
                    if dias == 1: return "1 DIA"
                    if dias == 2: return "2 DIAS"
                    if 3 <= dias <= 4: return "3 A 4 DIAS"
                    if 5 <= dias <= 7: return "5 A 7 DIAS"
                    return "ACIMA DE 7 DIAS"

                df_h['cat_tempo'] = df_h['dias_intervalo'].apply(classificar_tempo)

                # Descobrir até qual tentativa fomos
                max_tentativa = int(df_h['tentativa'].max())
                if max_tentativa > 10: max_tentativa = 10 # Trava de segurança visual para não quebrar a tela

                # 3. RENDERIZAR AS COLUNAS (COM QUEBRA DE LINHA AUTOMÁTICA)
                # O limite de 4 cartões por linha dobra o espaço horizontal de cada um
                max_cartoes_por_linha = 4

                for t in range(1, max_tentativa + 1):
                    # Sempre que o índice for múltiplo de 4, criamos uma nova linha de colunas na tela
                    if (t - 1) % max_cartoes_por_linha == 0:
                        st.write("") # Dá um respiro visual entre as fileiras
                        qtd_colunas_agora = min(max_cartoes_por_linha, max_tentativa - (t - 1))
                        colunas_ui = st.columns(qtd_colunas_agora)
                    
                    # Filtra o dataframe apenas para a tentativa (t)
                    df_t = df_h[df_h['tentativa'] == t]
                    
                    enviados = len(df_t)
                    nao_respondeu = len(df_t[df_t['status_novo'] == "SEM RETORNO"])
                    respondeu = enviados - nao_respondeu
                    
                    perc_resp = f"{(respondeu / enviados) * 100:.0f}%" if enviados > 0 else "0%"
                    perc_nao_resp = f"{(nao_respondeu / enviados) * 100:.0f}%" if enviados > 0 else "0%"

                    # Direciona a renderização para a coluna correta dentro da fileira atual
                    col_idx = (t - 1) % max_cartoes_por_linha
                    
                    with colunas_ui[col_idx]:
                        # --- 1. BLOCO SUPERIOR (STATUS) ---
                        st.markdown(f"<div style='text-align: center; font-weight: bold; padding-bottom: 8px;'>{t}º CONTATO</div>", unsafe_allow_html=True)
                        
                        dados_status = [
                            {"Status": "ENVIADOS", "Qtd": enviados, "%": "100%"},
                            {"Status": "RESPONDEU", "Qtd": respondeu, "%": perc_resp},
                            {"Status": "NÃO RESP.", "Qtd": nao_respondeu, "%": perc_nao_resp}
                        ]
                        st.dataframe(pd.DataFrame(dados_status), hide_index=True, use_container_width=True)

                        # --- 2. BLOCO INFERIOR (TEMPO MÉDIO) ---
                        if t > 1:
                            st.write("") 
                            st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 13px; padding-bottom: 8px;'>TEMPO ({t-1}º ao {t}º)</div>", unsafe_allow_html=True)
                            
                            ordem_categorias = ["MESMO DIA", "1 DIA", "2 DIAS", "3 A 4 DIAS", "5 A 7 DIAS", "ACIMA DE 7 DIAS"]
                            contagem_tempo = df_t['cat_tempo'].value_counts().to_dict()
                            
                            media_dias = df_t['dias_intervalo'].mean()
                            media_texto = f"{media_dias:.1f}".replace(".", ",") if pd.notna(media_dias) else "0,0"
                            
                            dados_tempo = []
                            for cat in ordem_categorias:
                                qtd_cat = contagem_tempo.get(cat, 0)
                                perc_cat = f"{(qtd_cat / enviados) * 100:.1f}%".replace(".", ",") if enviados > 0 else "0,0%"
                                dados_tempo.append({
                                    "Intervalo": cat,
                                    "Qtd": qtd_cat,
                                    "%": perc_cat
                                })
                            
                            st.dataframe(pd.DataFrame(dados_tempo), hide_index=True, use_container_width=True)
                            st.caption(f"**Média global:** {media_texto} dias")
            else:
                st.info("Nenhuma atividade de histórico encontrada para estes filtros após aplicar a seleção de consultor.")