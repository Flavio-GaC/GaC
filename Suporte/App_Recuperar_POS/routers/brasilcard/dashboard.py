import io
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# CONSTANTE DE REGRAS DO FUNIL DE VENDAS
# ==========================================
REGRAS_FUNIL = {
    "LEAD RECEBIDO": {
        "todos": True,
        "prefixos": (),
        "exatos": set()
    },
    "LEAD DESQUALIFICADO": {
        "todos": False,
        "prefixos": (
            "SEM PERFIL",
            "INVALIDO",
            "NÃO TEM INTERESSE",
            "INDICAÇÃO LEAD - NÃO TEM INTERESSE",
            "INDICAÇÃO M0 - NÃO TEM INTERESSE",
        ),
        "exatos": set()
    },
    "MEET AGENDADO": {
        "todos": False,
        "prefixos": (),
        "exatos": {
            "MEET AGENDADO",
            "REAGENDAMENTO",
            "TEM INTERESSE - REUNIÃO VIA MEET",
            "RETORNO AGENDADO - MEET",
            "INDICAÇÃO LEAD - RETORNO AGENDADO - MEET",
            "INDICAÇÃO M0 - RETORNO AGENDADO - MEET",
        }
    },
    "MEET REALIZADO": {
        "todos": False,
        "prefixos": (),
        "exatos": {
            "REALIZADO - MEET",
            "REALIZADO - LIGAÇÃO",
            "REALIZADO - PROPOSTA WHATS",
            "EM NEGOCIAÇÃO",
            "COBRANÇA ADESÃO",
        }
    },
    "CADASTRO": {
        "todos": False,
        "prefixos": (),
        "exatos": {
            "CADASTRADO",
        }
    },
    "PDV": {
        "todos": False,
        "prefixos": (),
        "exatos": {
            "FECHADO - GEROU PDV",
        }
    }
}


def contar_leads_etapa_funil(df_base, nome_etapa):
    if df_base.empty:
        return 0

    regra = REGRAS_FUNIL[nome_etapa]
    if regra.get("todos"):
        return int(df_base["id"].nunique())

    serie_status = df_base["status_atual"].fillna("").astype(str).str.strip().str.upper()
    mask = serie_status.isin(regra["exatos"])
    if regra["prefixos"]:
        mask = mask | serie_status.str.startswith(regra["prefixos"], na=False)

    return int(df_base.loc[mask, "id"].nunique())

def render_card_dash(titulo, valor, percentual_texto, cor_fundo, cor_texto="white"):
    st.markdown(f"""
    <div style="background-color: {cor_fundo}; padding: 14px 10px; border-radius: 8px; color: {cor_texto}; 
                text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px;
                height: 135px; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="margin: 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; opacity: 0.9; 
                    line-height: 1.25; min-height: 30px; display: flex; align-items: center; justify-content: center;">
            {titulo}
        </div>
        <div style="margin: 0; font-size: 32px; font-weight: bold; line-height: 1;">
            {valor}
        </div>
        <div style="margin: 0; font-size: 11px; opacity: 0.85; font-style: italic;">
            {percentual_texto}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Cache otimizado: guarda os dados na memória por 10 minutos (600s) para poupar o Supabase
@st.cache_data(show_spinner=False, ttl=600)
def buscar_dados_dashboard(_supabase, dt_ini, dt_fim):
    # 1. Busca os Leads criados no período selecionado
    leads_extraidos = []
    offset = 0
    while True:
        resp = (
            _supabase.table("leads")
            .select("id, status_atual, responsavel_atual")
            .gte("created_at", f"{dt_ini} 00:00:00")
            .lte("created_at", f"{dt_fim} 23:59:59")
            .range(offset, offset + 999)
            .execute()
        )
        if not resp.data:
            break
        leads_extraidos.extend(resp.data)
        if len(resp.data) < 1000:
            break
        offset += 1000

    # 2. Busca o Histórico diretamente pelo período já trazendo a coluna meio_contato
    historico_extraido = []
    offset_h = 0
    while True:
        resp_h = (
            _supabase.table("historico_leads")
            .select("id, usuario_id, lead_id, created_at, status_novo, tentativa, meio_contato")
            .gte("created_at", f"{dt_ini} 00:00:00")
            .lte("created_at", f"{dt_fim} 23:59:59")
            .range(offset_h, offset_h + 999)
            .execute()
        )
        if not resp_h.data:
            break
        historico_extraido.extend(resp_h.data)
        if len(resp_h.data) < 1000:
            break
        offset_h += 1000

    return leads_extraidos, historico_extraido


@st.cache_data(show_spinner=False, ttl=3600)
def buscar_usuarios_dash(_supabase):
    try:
        resp = (
            _supabase.table("usuarios")
            .select("id, nome_completo, setor")
            .eq("empresa_id", 1)
            .eq("ativo", True)
            .eq("nivel_acesso", 5)
            .in_("setor", ["COMERCIAL", "PRÉ-VENDA"])
            .execute()
        )
        if not resp.data:
            return []
        
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

    # Carregamento único compartilhado entre as abas
    with st.spinner("Processando métricas..."):
        dados_leads, dados_hist = buscar_dados_dashboard(supabase, dt_inicio, dt_final)
    
    aba_geral, aba_freq, aba_tentativas, aba_funil = st.tabs([
        "📊 Métricas Gerais",
        "⏱️ Frequência",
        "📞 Tentativas",
        "🌪️ Funil"
    ])
    
    # ==========================================
    # ABA 1: MÉTRICAS GERAIS
    # ==========================================
    with aba_geral:
        df_leads = pd.DataFrame(dados_leads) if dados_leads else pd.DataFrame(columns=["id", "status_atual", "responsavel_atual"])
        df_hist = pd.DataFrame(dados_hist) if dados_hist else pd.DataFrame(columns=["id", "usuario_id", "lead_id", "created_at", "status_novo", "tentativa", "meio_contato"])

        if consultores_selecionados:
            ids_selecionados = [mapa_usuarios[nome] for nome in consultores_selecionados]
            df_leads = df_leads[df_leads['responsavel_atual'].isin(ids_selecionados)]
            df_hist = df_hist[df_hist['usuario_id'].isin(ids_selecionados)]

        if not df_leads.empty:
            df_leads['status_atual'] = df_leads['status_atual'].fillna("")

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

                def formatar_com_percentual(valor, total):
                    if total == 0:
                        return f"{valor} (0,00%)"
                    percentual = (valor / total) * 100
                    return f"{valor} ({percentual:.2f}%)".replace(".", ",")

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

            df_matriz = pd.DataFrame(dados_matriz)
            st.dataframe(df_matriz, use_container_width=True, hide_index=True)

    # ==========================================
    # ABA 2: FREQUÊNCIA
    # ==========================================
    with aba_freq:
        st.markdown("### Análise de Engajamento e Cohort de Contatos")
        st.caption("Acompanhe o volume de envios e a velocidade de retorno por tentativa.")

        df_h = pd.DataFrame(dados_hist) if dados_hist else pd.DataFrame()
            
        if df_h.empty:
            st.info("Não há histórico de contatos registrado para os filtros selecionados.")
        else:
            if consultores_selecionados:
                ids_selecionados = [mapa_usuarios[nome] for nome in consultores_selecionados]
                df_h = df_h[df_h['usuario_id'].isin(ids_selecionados)]

            if not df_h.empty:
                df_h['created_at'] = pd.to_datetime(df_h['created_at'])
                df_h['tentativa'] = pd.to_numeric(df_h['tentativa'], errors='coerce').fillna(1).astype(int)
                df_h = df_h.sort_values(by=['lead_id', 'tentativa'])

                df_h['data_anterior'] = df_h.groupby('lead_id')['created_at'].shift(1)
                df_h['dias_intervalo'] = (df_h['created_at'] - df_h['data_anterior']).dt.days

                def classificar_tempo(dias):
                    if pd.isna(dias): return None
                    if dias == 0: return "MESMO DIA"
                    if dias == 1: return "1 DIA"
                    if dias == 2: return "2 DIAS"
                    if 3 <= dias <= 4: return "3 A 4 DIAS"
                    if 5 <= dias <= 7: return "5 A 7 DIAS"
                    return "ACIMA DE 7 DIAS"

                df_h['cat_tempo'] = df_h['dias_intervalo'].apply(classificar_tempo)

                max_tentativa = int(df_h['tentativa'].max())
                if max_tentativa > 10: max_tentativa = 10

                max_cartoes_por_linha = 4

                for t in range(1, max_tentativa + 1):
                    if (t - 1) % max_cartoes_por_linha == 0:
                        st.write("")
                        qtd_colunas_agora = min(max_cartoes_por_linha, max_tentativa - (t - 1))
                        colunas_ui = st.columns(qtd_colunas_agora)
                    
                    df_t = df_h[df_h['tentativa'] == t]
                    
                    enviados = len(df_t)
                    nao_respondeu = len(df_t[df_t['status_novo'] == "SEM RETORNO"])
                    respondeu = enviados - nao_respondeu
                    
                    perc_resp = f"{(respondeu / enviados) * 100:.0f}%" if enviados > 0 else "0%"
                    perc_nao_resp = f"{(nao_respondeu / enviados) * 100:.0f}%" if enviados > 0 else "0%"

                    col_idx = (t - 1) % max_cartoes_por_linha
                    
                    with colunas_ui[col_idx]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold; padding-bottom: 8px;'>{t}º CONTATO</div>", unsafe_allow_html=True)
                        
                        dados_status = [
                            {"Status": "ENVIADOS", "Qtd": enviados, "%": "100%"},
                            {"Status": "RESPONDEU", "Qtd": respondeu, "%": perc_resp},
                            {"Status": "NÃO RESP.", "Qtd": nao_respondeu, "%": perc_nao_resp}
                        ]
                        st.dataframe(pd.DataFrame(dados_status), hide_index=True, use_container_width=True)

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

    # ==========================================
    # ABA 3: TENTATIVAS
    # ==========================================
    with aba_tentativas:
        st.markdown("### Tentativas de Contato por Meio")
        st.caption("Volume consolidado de tentativas no período por canal de acionamento registrado no histórico.")

        if consultores_selecionados:
            usuarios_tent = [u for u in usuarios_bd if u['nome_completo'] in consultores_selecionados]
        else:
            usuarios_tent = list(usuarios_bd)

        ids_usuarios_tent = [u['id'] for u in usuarios_tent]

        df_h_tent = pd.DataFrame(dados_hist) if dados_hist else pd.DataFrame()

        if not df_h_tent.empty and ids_usuarios_tent:
            df_h_tent['tentativa_num'] = pd.to_numeric(df_h_tent['tentativa'], errors='coerce').fillna(0).astype(int)
            df_validas = df_h_tent[
                (df_h_tent['tentativa_num'] > 0) &
                (df_h_tent['usuario_id'].isin(ids_usuarios_tent))
            ].copy()
            df_validas['meio_limpo'] = df_validas['meio_contato'].fillna("").astype(str).str.strip()
        else:
            df_validas = pd.DataFrame(columns=["id", "lead_id", "usuario_id", "tentativa_num", "meio_limpo"])

        def calcular_metricas_meio(df_base):
            if df_base.empty:
                return 0, 0, 0, 0

            tot_tent = len(df_base)
            mask_lig = df_base['meio_limpo'].str.contains("ligação|ligacao", case=False, na=False)
            mask_whats = df_base['meio_limpo'].str.contains("whatsapp", case=False, na=False) & (~mask_lig)

            qtd_whats = int(mask_whats.sum())
            qtd_lig = int(mask_lig.sum())
            qtd_outros = tot_tent - (qtd_whats + qtd_lig)

            return tot_tent, qtd_whats, qtd_lig, qtd_outros

        tot_tent_geral, tot_whats_geral, tot_lig_geral, tot_outros_geral = calcular_metricas_meio(df_validas)

        def formatar_perc_card(valor, total):
            if total <= 0:
                return "0,0%"
            return f"{(valor / total) * 100:.1f}%".replace(".", ",")

        st.write("")
        ct1, ct2, ct3, ct4 = st.columns(4)
        with ct1:
            render_card_dash("Tentativas", str(tot_tent_geral), "Total no período", "#0f4d7e", "white")
        with ct2:
            render_card_dash("Whatsapp", str(tot_whats_geral), formatar_perc_card(tot_whats_geral, tot_tent_geral), "#0f4d7e", "white")
        with ct3:
            render_card_dash("Ligação", str(tot_lig_geral), formatar_perc_card(tot_lig_geral, tot_tent_geral), "#0f4d7e", "white")
        with ct4:
            render_card_dash("Outros Meios", str(tot_outros_geral), formatar_perc_card(tot_outros_geral, tot_tent_geral), "#0f4d7e", "white")

        st.write("---")
        if not usuarios_tent:
            st.info("Nenhum consultor encontrado para os filtros selecionados.")
        else:
            linhas_consultores = []
            for u in usuarios_tent:
                uid = u['id']
                nome = str(u.get('nome_completo', '')).strip().upper()
                setor_cru = str(u.get('setor', '')).strip().upper()
                if setor_cru == "PRÉ-VENDA":
                    setor_label = "Pré-Venda"
                elif setor_cru == "COMERCIAL":
                    setor_label = "Especialista"
                else:
                    setor_label = setor_cru.title() if setor_cru else "Sem Setor"

                df_u = df_validas[df_validas['usuario_id'] == uid] if not df_validas.empty else pd.DataFrame()
                u_tent, u_whats, u_lig, u_outros = calcular_metricas_meio(df_u)

                linhas_consultores.append({
                    "nome": nome,
                    "setor": setor_label,
                    "tentativas": u_tent,
                    "whats": u_whats,
                    "ligacao": u_lig,
                    "outros": u_outros
                })

            linhas_consultores.sort(key=lambda x: (-x["tentativas"], x["nome"]))

            col_esq, col_centro, col_dir = st.columns([1, 2.5, 1])
            with col_centro:
                html_tabela = (
                    '<div style="border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; overflow: hidden; margin-top: 10px;">'
                    '<table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px;">'
                    '<thead>'
                    '<tr style="background-color: rgba(255,255,255,0.05); color: #a1a1aa; border-bottom: 1px solid rgba(255,255,255,0.12); text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">'
                    '<th style="padding: 12px 16px; text-align: left;">Consultor</th>'
                    '<th style="padding: 12px 10px; text-align: center;">Tentativas</th>'
                    '<th style="padding: 12px 10px; text-align: center;">Whatsapp</th>'
                    '<th style="padding: 12px 10px; text-align: center;">Ligação</th>'
                    '<th style="padding: 12px 10px; text-align: center;">Outros Meios</th>'
                    '</tr>'
                    '</thead>'
                    '<tbody>'
                )

                for item in linhas_consultores:
                    html_tabela += (
                        '<tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">'
                        '<td style="padding: 10px 16px; text-align: left;">'
                        f'<div style="font-weight: 700; color: #f4f4f5; font-size: 13px; line-height: 1.2;">{item["nome"]}</div>'
                        f'<div style="font-size: 11px; color: #a1a1aa; opacity: 0.65; margin-top: 2px;">{item["setor"]}</div>'
                        '</td>'
                        f'<td style="padding: 10px; text-align: center; font-weight: 600;">{item["tentativas"]}</td>'
                        f'<td style="padding: 10px; text-align: center;">{item["whats"]}</td>'
                        f'<td style="padding: 10px; text-align: center;">{item["ligacao"]}</td>'
                        f'<td style="padding: 10px; text-align: center;">{item["outros"]}</td>'
                        '</tr>'
                    )

                html_tabela += (
                    '</tbody>'
                    '<tfoot>'
                    '<tr style="background-color: rgba(255,255,255,0.06); font-weight: bold; border-top: 2px solid rgba(255,255,255,0.15);">'
                    '<td style="padding: 12px 16px; text-align: left;">Total</td>'
                    f'<td style="padding: 12px 10px; text-align: center;">{tot_tent_geral}</td>'
                    f'<td style="padding: 12px 10px; text-align: center;">{tot_whats_geral}</td>'
                    f'<td style="padding: 12px 10px; text-align: center;">{tot_lig_geral}</td>'
                    f'<td style="padding: 12px 10px; text-align: center;">{tot_outros_geral}</td>'
                    '</tr>'
                    '</tfoot>'
                    '</table>'
                    '</div>'
                )

                st.markdown(html_tabela, unsafe_allow_html=True)

    # ==========================================
    # ABA 4: FUNIL DE VENDAS
    # ==========================================
    with aba_funil:
        st.markdown("### 🌪️ Funil de Conversão Comercial")
        st.caption("Acompanhamento das 6 etapas do funil de acordo com o período e os consultores selecionados.")

        df_leads_f = pd.DataFrame(dados_leads) if dados_leads else pd.DataFrame(columns=["id", "status_atual", "responsavel_atual"])
        df_hist_f = pd.DataFrame(dados_hist) if dados_hist else pd.DataFrame(columns=["id", "usuario_id"])

        # Mesmas limitantes de consultor da aba "Métricas Gerais"
        if consultores_selecionados:
            ids_sel_funil = [mapa_usuarios[nome] for nome in consultores_selecionados]
            df_leads_f = df_leads_f[df_leads_f["responsavel_atual"].isin(ids_sel_funil)]
            df_hist_f = df_hist_f[df_hist_f["usuario_id"].isin(ids_sel_funil)]
        else:
            ids_todos_validos = [u["id"] for u in usuarios_bd]
            if not df_leads_f.empty and ids_todos_validos:
                df_leads_f = df_leads_f[df_leads_f["responsavel_atual"].isin(ids_todos_validos)]

        if not df_leads_f.empty:
            df_leads_f["status_atual"] = df_leads_f["status_atual"].fillna("")

        # Cálculo consolidado das 6 etapas usando a constante REGRAS_FUNIL
        qtd_recebido = contar_leads_etapa_funil(df_leads_f, "LEAD RECEBIDO")
        qtd_desqualificado = contar_leads_etapa_funil(df_leads_f, "LEAD DESQUALIFICADO")
        qtd_meet_agendado = contar_leads_etapa_funil(df_leads_f, "MEET AGENDADO")
        qtd_meet_realizado = contar_leads_etapa_funil(df_leads_f, "MEET REALIZADO")
        qtd_cadastro = contar_leads_etapa_funil(df_leads_f, "CADASTRO")
        qtd_pdv = contar_leads_etapa_funil(df_leads_f, "PDV")

        def fmt_perc_funil(valor, base):
            if base <= 0:
                return "0,0%"
            return f"{(valor / base) * 100:.1f}%".replace(".", ",")

        # 1. CARTÕES DAS 6 ETAPAS NO TOPO
        st.write("")
        cf1, cf2, cf3, cf4, cf5, cf6 = st.columns(6)
        with cf1:
            render_card_dash("1. Recebido", str(qtd_recebido), "100,0% da base", "#eb9834", "white")
        with cf2:
            render_card_dash("2. Desqualificado", str(qtd_desqualificado), fmt_perc_funil(qtd_desqualificado, qtd_recebido), "#eb862f", "white")
        with cf3:
            render_card_dash("3. Meet Agendado", str(qtd_meet_agendado), fmt_perc_funil(qtd_meet_agendado, qtd_recebido), "#eb752a", "white")
        with cf4:
            render_card_dash("4. Meet Realizado", str(qtd_meet_realizado), fmt_perc_funil(qtd_meet_realizado, qtd_recebido), "#ea6425", "white")
        with cf5:
            render_card_dash("5. Cadastro", str(qtd_cadastro), fmt_perc_funil(qtd_cadastro, qtd_recebido), "#e95320", "white")
        with cf6:
            render_card_dash("6. PDV", str(qtd_pdv), fmt_perc_funil(qtd_pdv, qtd_recebido), "#e8421b", "white")

        # 2. ILUSTRAÇÃO DINÂMICA DO FUNIL (MODELO PIRÂMIDE INVERTIDA)
        col_f_esq, col_f_meio, col_f_dir = st.columns([1, 2.2, 1])
        with col_f_meio:
            svg_funil = (
                '<div style="display: flex; justify-content: center; margin: 10px 0 20px 0;">'
                '<svg viewBox="0 0 760 550" style="width: 100%; max-width: 680px; height: auto; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.25));">'
                '<!-- Fatia 1: LEAD RECEBIDO -->'
                '<polygon points="30,60 730,60 678.4,130 81.6,130" fill="#eb9834" />'
                '<text x="58" y="102" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" font-style="italic">1ª Lead Recebido</text>'
                f'<text x="660" y="102" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="end">{qtd_recebido} (100%)</text>'
                '<!-- Fatia 2: LEAD DESQUALIFICADO -->'
                '<polygon points="81.6,130 678.4,130 626.8,200 133.2,200" fill="#eb862f" />'
                '<text x="110" y="172" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" font-style="italic">2ª Desqualificado</text>'
                f'<text x="610" y="172" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="end">{qtd_desqualificado} ({fmt_perc_funil(qtd_desqualificado, qtd_recebido)})</text>'
                '<!-- Fatia 3: MEET AGENDADO -->'
                '<polygon points="133.2,200 626.8,200 575.3,270 184.7,270" fill="#eb752a" />'
                '<text x="162" y="242" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" font-style="italic">3ª Meet Agendado</text>'
                f'<text x="558" y="242" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="end">{qtd_meet_agendado} ({fmt_perc_funil(qtd_meet_agendado, qtd_recebido)})</text>'
                '<!-- Fatia 4: MEET REALIZADO -->'
                '<polygon points="184.7,270 575.3,270 523.7,340 236.3,340" fill="#ea6425" />'
                '<text x="213" y="312" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" font-style="italic">4ª Meet Realizado</text>'
                f'<text x="506" y="312" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="end">{qtd_meet_realizado} ({fmt_perc_funil(qtd_meet_realizado, qtd_recebido)})</text>'
                '<!-- Fatia 5: CADASTRO -->'
                '<polygon points="236.3,340 523.7,340 472.1,410 287.9,410" fill="#e95320" />'
                '<text x="268" y="382" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" font-style="italic">5ª Cadastro</text>'
                f'<text x="458" y="382" fill="#ffffff" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="end">{qtd_cadastro} ({fmt_perc_funil(qtd_cadastro, qtd_recebido)})</text>'
                '<!-- Fatia 6: PDV (Fundo do Funil) -->'
                '<polygon points="287.9,410 472.1,410 380,535" fill="#e8421b" />'
                '<text x="315" y="442" fill="#ffffff" font-family="sans-serif" font-size="15" font-weight="bold" font-style="italic">6ª PDV</text>'
                f'<text x="445" y="442" fill="#ffffff" font-family="sans-serif" font-size="15" font-weight="bold" text-anchor="end">{qtd_pdv} ({fmt_perc_funil(qtd_pdv, qtd_recebido)})</text>'
                '<!-- Seta Central Vertical -->'
                '<line x1="380" y1="82" x2="380" y2="395" stroke="#ffffff" stroke-width="6" stroke-linecap="round" />'
                '<polyline points="366,382 380,398 394,382" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" />'
                '<!-- Pílula Topo: Oportunidades -->'
                '<rect x="200" y="14" width="360" height="68" rx="34" ry="34" fill="#ff3b2f" />'
                '<text x="380" y="56" fill="#ffffff" font-family="sans-serif" font-size="24" font-weight="bold" text-anchor="middle">💡 Oportunidades</text>'
                '</svg>'
                '</div>'
            )
            st.markdown(svg_funil, unsafe_allow_html=True)

        # 3. MATRIZ DO FUNIL POR CONSULTOR (MESMA REGRA DA MÉTRICA GERAL)
        st.write("---")
        st.markdown("#### Matriz do Funil por Consultor")

        if consultores_selecionados:
            usuarios_tabela_funil = [u for u in usuarios_bd if u['nome_completo'] in consultores_selecionados]
        else:
            ids_ativos_leads_f = df_leads_f['responsavel_atual'].unique().tolist() if not df_leads_f.empty else []
            ids_ativos_hist_f = df_hist_f['usuario_id'].unique().tolist() if not df_hist_f.empty else []
            ids_ativos_f = set(ids_ativos_leads_f + ids_ativos_hist_f)
            usuarios_tabela_funil = [u for u in usuarios_bd if u['id'] in ids_ativos_f]

        if not usuarios_tabela_funil:
            st.info("Nenhuma atividade registrada para os filtros selecionados.")
        else:
            dados_matriz_funil = []
            for u in sorted(usuarios_tabela_funil, key=lambda x: x['nome_completo']):
                uid = u['id']
                nome = u['nome_completo'].upper()

                setor_cru = str(u.get('setor', '')).strip().upper()
                if setor_cru == "COMERCIAL":
                    cargo = "Especialista"
                elif setor_cru == "PRÉ-VENDA":
                    cargo = "Pré-Venda"
                else:
                    cargo = setor_cru.title() if setor_cru else "Sem Setor"

                df_u_funil = df_leads_f[df_leads_f['responsavel_atual'] == uid] if not df_leads_f.empty else pd.DataFrame(columns=["id", "status_atual"])

                u_rec = contar_leads_etapa_funil(df_u_funil, "LEAD RECEBIDO")
                u_desq = contar_leads_etapa_funil(df_u_funil, "LEAD DESQUALIFICADO")
                u_agend = contar_leads_etapa_funil(df_u_funil, "MEET AGENDADO")
                u_real = contar_leads_etapa_funil(df_u_funil, "MEET REALIZADO")
                u_cad = contar_leads_etapa_funil(df_u_funil, "CADASTRO")
                u_pdv = contar_leads_etapa_funil(df_u_funil, "PDV")

                def formatar_celula_funil(valor, total):
                    if total == 0:
                        return f"{valor} (0,00%)"
                    perc = (valor / total) * 100
                    return f"{valor} ({perc:.2f}%)".replace(".", ",")

                dados_matriz_funil.append({
                    "NOME DO CONSULTOR": nome,
                    "CARGO": cargo,
                    "1. LEAD RECEBIDO": u_rec,
                    "2. DESQUALIFICADO": formatar_celula_funil(u_desq, u_rec),
                    "3. MEET AGENDADO": formatar_celula_funil(u_agend, u_rec),
                    "4. MEET REALIZADO": formatar_celula_funil(u_real, u_rec),
                    "5. CADASTRO": formatar_celula_funil(u_cad, u_rec),
                    "6. PDV": formatar_celula_funil(u_pdv, u_rec),
                })

            df_matriz_funil = pd.DataFrame(dados_matriz_funil)
            st.dataframe(df_matriz_funil, use_container_width=True, hide_index=True)
