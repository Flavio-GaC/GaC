import streamlit as st
import io
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from themes.theme import cabecalho_pagina, titulo_secao

# --- FUNÇÃO DE ESTILIZAÇÃO DOS CARTÕES (KPIS) ---
def render_card(titulo, valor, cor_fundo):
    st.markdown(f"""
    <div style="background-color: {cor_fundo}; padding: 20px; border-radius: 10px; color: white; 
                text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
        <p style="margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">{titulo}</p>
        <h2 style="margin: 5px 0 0 0; font-size: 38px; font-weight: bold;">{valor}</h2>
    </div>
    """, unsafe_allow_html=True)

def mostrar_dashboard_meets(supabase):
    cabecalho_pagina("Dashboard Gerencial", "Acompanhe o funil de vendas, os agendamentos e a volumetria da equipe.")

    # ==========================================
    # CACHE E CONSULTAS AO BANCO
    # ==========================================
    @st.cache_data(show_spinner=False, ttl=1800)
    def obter_mapa_usuarios():
        try:
            resp = supabase.table("usuarios").select("id, nome_completo").execute()
            if resp.data:
                return {u["id"]: u["nome_completo"] for u in resp.data}
            return {}
        except Exception:
            return {}

    @st.cache_data(show_spinner=False, ttl=1800)
    def buscar_dados_meets(data_inicio_str, data_fim_str):
        try:
            resp = supabase.table("meets").select("*").gte("created_at", f"{data_inicio_str} 00:00:00").lte("created_at", f"{data_fim_str} 23:59:59").limit(10000).execute()
            return resp.data if resp.data else []
        except Exception as e:
            return f"erro: {e}"

    @st.cache_data(show_spinner=False, ttl=1800)
    def buscar_dados_leads(data_inicio_str, data_fim_str):
        try:
            resp = supabase.table("leads").select("*").gte("created_at", f"{data_inicio_str} 00:00:00").lte("created_at", f"{data_fim_str} 23:59:59").limit(10000).execute()
            return resp.data if resp.data else []
        except Exception as e:
            return f"erro: {e}"

    # ==========================================
    # FILTROS GLOBAIS (Aplicam para as duas abas)
    # ==========================================
    with st.container(border=True):
        st.subheader("⚙️ Filtros de Período")
        c1, c2, c3 = st.columns(3)
        
        data_padrao_inicio = date.today() - timedelta(days=30)
        data_padrao_fim = date.today()

        with c1:
            d_inicio = st.date_input("Data Inicial", value=data_padrao_inicio, format="DD/MM/YYYY")
        with c2:
            d_fim = st.date_input("Data Final", value=data_padrao_fim, format="DD/MM/YYYY")
        with c3:
            st.write("")
            st.write("")
            btn_atualizar = st.button("Buscar Dados no Banco", type="primary", use_container_width=True)

    if btn_atualizar:
        with st.spinner("Extraindo volumetria do banco..."):
            str_ini = d_inicio.strftime("%Y-%m-%d")
            str_fim = d_fim.strftime("%Y-%m-%d")
            
            st.session_state["dash_dados_meets"] = buscar_dados_meets(str_ini, str_fim)
            st.session_state["dash_dados_leads"] = buscar_dados_leads(str_ini, str_fim)

    dados_meets = st.session_state.get("dash_dados_meets", [])
    dados_leads = st.session_state.get("dash_dados_leads", [])

    mapa_usuarios = obter_mapa_usuarios()

    aba_leads, aba_meets = st.tabs(["🚀 Esteira de Leads", "🎥 Agendamentos (Meets)"])

    # ==============================================================================
    # ABA 1: ESTEIRA DE LEADS
    # ==============================================================================
    with aba_leads:
        if isinstance(dados_leads, str) and dados_leads.startswith("erro:"):
            st.error(f"Erro ao buscar leads: {dados_leads}")
        elif not dados_leads:
            st.warning("Nenhum lead importado no período selecionado.")
        else:
            df_leads = pd.DataFrame(dados_leads)
            
            df_leads['nome_pre_venda'] = df_leads['id_pre_venda'].map(lambda uid: mapa_usuarios.get(uid, "Sem dono"))
            df_leads['nome_especialista'] = df_leads['id_especialista'].map(lambda uid: mapa_usuarios.get(uid, "Não atribuído"))
            df_leads['data_criacao'] = pd.to_datetime(df_leads['created_at']).dt.strftime('%d/%m/%Y')

            # --- KPIS PRINCIPAIS DA ESTEIRA ---
            total_leads = len(df_leads)
            leads_fase2_mais = len(df_leads[df_leads['fase_atual'] >= 2])
            pdvs_gerados = len(df_leads[df_leads['status_atual'] == 'PDV GERADO'])
            taxa_conversao = (pdvs_gerados / total_leads * 100) if total_leads > 0 else 0

            l1, l2, l3, l4 = st.columns(4)
            with l1: render_card("Total de Leads Importados", str(total_leads), "#1E3A8A")
            with l2: render_card("Avançaram pro Comercial", str(leads_fase2_mais), "#9333EA")
            with l3: render_card("PDVs Gerados (Sucesso)", str(pdvs_gerados), "#059669")
            with l4: render_card("Conversão Global", f"{taxa_conversao:.1f}%", "#D97706")

            st.write("---")

            # --- GRÁFICOS E TABELA FUNIL ---
            cg1, cg2 = st.columns([3, 2])

            with cg1:
                titulo_secao("Funil de Vendas Global")
                
                # CÁLCULOS DO FUNIL EM MEMÓRIA (Custo zero pro banco)
                qtd_leads = total_leads
                qtd_trabalhados = len(df_leads[df_leads['status_atual'] != 'PROSPECTAR'])
                qtd_agendados = len(df_leads[df_leads['fase_atual'] == 2])
                
                # Para saber os realizados: todo mundo da fase 2 pra cima JÁ fez meet, além de quem está com status 'MEET REALIZADO' agora
                qtd_realizados = len(df_leads[(df_leads['fase_atual'] >= 2) | (df_leads['status_atual'] == 'MEET REALIZADO')])
                
                qtd_cadastrados = len(df_leads[df_leads['fase_atual'] == 3])
                qtd_pdv = pdvs_gerados

                # Função auxiliar para percentagem
                def calc_perc(valor):
                    if qtd_leads == 0: return "0,00%"
                    return f"{(valor / qtd_leads) * 100:.2f}%".replace('.', ',')

                # Tabela em HTML idêntica à solicitada
                html_tabela_funil = f"""
                <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; text-align: center; border: 1px solid black; margin-top: 15px;">
                    <thead>
                        <tr>
                            <th style="border: 1px solid black; background-color: transparent; padding: 10px;"></th>
                            <th style="border: 1px solid black; background-color: transparent; padding: 10px; font-weight: bold; color: #d4d4d8;">FUNIL OPERACIONAL</th>
                            <th style="border: 1px solid black; background-color: transparent; padding: 10px; font-weight: bold; color: #d4d4d8;">Perc. %</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="border: 1px solid black; padding: 10px; font-weight: bold; text-align: right; color: #d4d4d8;">LEADs</td>
                            <td style="border: 1px solid black; padding: 10px; background-color: #5b9bd5; color: white; font-weight: bold; font-size: 16px;">{qtd_leads}</td>
                            <td style="border: 1px solid black; padding: 10px; color: #d4d4d8;">-</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid black; padding: 10px; font-weight: bold; text-align: right; color: #d4d4d8;">LEADs TRABALHADOS</td>
                            <td style="border: 1px solid black; padding: 10px; background-color: #4472c4; color: white; font-weight: bold; font-size: 16px;">{qtd_trabalhados}</td>
                            <td style="border: 1px solid black; padding: 10px; color: #d4d4d8;">{calc_perc(qtd_trabalhados)}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid black; padding: 10px; font-weight: bold; text-align: right; color: #d4d4d8;">MEET AGENDADO</td>
                            <td style="border: 1px solid black; padding: 10px; background-color: #38a581; color: white; font-weight: bold; font-size: 16px;">{qtd_agendados}</td>
                            <td style="border: 1px solid black; padding: 10px; color: #d4d4d8;">{calc_perc(qtd_agendados)}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid black; padding: 10px; font-weight: bold; text-align: right; color: #d4d4d8;">REALIZADO</td>
                            <td style="border: 1px solid black; padding: 10px; background-color: #38a581; color: white; font-weight: bold; font-size: 16px;">{qtd_realizados}</td>
                            <td style="border: 1px solid black; padding: 10px; color: #d4d4d8;">{calc_perc(qtd_realizados)}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid black; padding: 10px; font-weight: bold; text-align: right; color: #d4d4d8;">CADASTRADO</td>
                            <td style="border: 1px solid black; padding: 10px; background-color: #2ca05a; color: white; font-weight: bold; font-size: 16px;">{qtd_cadastrados}</td>
                            <td style="border: 1px solid black; padding: 10px; color: #d4d4d8;">{calc_perc(qtd_cadastrados)}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid black; padding: 10px; font-weight: bold; text-align: right; color: #d4d4d8;">PDV GERADO</td>
                            <td style="border: 1px solid black; padding: 10px; background-color: #2ca05a; color: white; font-weight: bold; font-size: 16px;">{qtd_pdv}</td>
                            <td style="border: 1px solid black; padding: 10px; color: #d4d4d8;">{calc_perc(qtd_pdv)}</td>
                        </tr>
                    </tbody>
                </table>
                """
                st.markdown(html_tabela_funil, unsafe_allow_html=True)

            with cg2:
                titulo_secao("Leads por Especialista (Fase 2+)")
                df_esp = df_leads[df_leads['fase_atual'] >= 2]
                if not df_esp.empty:
                    df_esp_agrupado = df_esp.groupby('nome_especialista').size().reset_index(name='Qtd').sort_values('Qtd')
                    fig_esp = px.bar(df_esp_agrupado, x='Qtd', y='nome_especialista', orientation='h', text='Qtd', color_discrete_sequence=['#a855f7'])
                    fig_esp.update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_esp, use_container_width=True)
                else:
                    st.info("Nenhum lead chegou ao Comercial neste período.")

            # ==============================================================================
            # NOVO: DETALHAMENTO DE STATUS POR ETAPA (O GRÁFICO VERTICAL)
            # ==============================================================================
            st.write("---")
            titulo_secao("🔍 Diagnóstico: Onde os leads estão parados?")
            
            # Seletor interativo em formato de botões
            opcoes_fase = ["🔵 Fase 1 (Pré-Venda)", "🟣 Fase 2 (Comercial)", "🟠 Fase 3 (Backoffice)"]
            fase_selecionada = st.radio("Selecione a fase para detalhar os status:", opcoes_fase, horizontal=True)

            # Lógica de filtro e cores baseada no clique
            if "Fase 1" in fase_selecionada:
                df_detalhe = df_leads[df_leads['fase_atual'] == 1]
                cor_barras = "#3b82f6"
            elif "Fase 2" in fase_selecionada:
                df_detalhe = df_leads[df_leads['fase_atual'] == 2]
                cor_barras = "#a855f7"
            else:
                df_detalhe = df_leads[df_leads['fase_atual'] == 3]
                cor_barras = "#f97316"

            if df_detalhe.empty:
                st.info("Não há leads parados nesta fase no período selecionado.")
            else:
                # Agrupa os status, conta e ordena do maior pro menor
                df_status_detalhe = df_detalhe.groupby('status_atual').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False)
                
                # Gera o gráfico vertical
                fig_bar_detalhe = px.bar(
                    df_status_detalhe, 
                    x='status_atual', 
                    y='Quantidade', 
                    text='Quantidade',
                    color_discrete_sequence=[cor_barras]
                )
                
                # Ajuste de layout para o gráfico vertical
                fig_bar_detalhe.update_traces(textposition='outside')
                fig_bar_detalhe.update_layout(
                    xaxis_title="Status Atual", 
                    yaxis_title="Volume de Leads", 
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis_tickangle=-45 # Inclina o texto para caber certinho se tiver nomes compridos
                )
                st.plotly_chart(fig_bar_detalhe, use_container_width=True)

            # --- EXPORTAÇÃO DOS LEADS BRUTOS ---
            st.write("---")
            with st.expander("📊 Ver Base de Leads (Bruto) e Exportar"):
                colunas_leads = {
                    "cnpj": "CNPJ", "nome_empresa": "Empresa", "origem": "Origem",
                    "fase_atual": "Fase", "status_atual": "Status", 
                    "nome_pre_venda": "Pré-Venda", "nome_especialista": "Especialista Comercial",
                    "data_criacao": "Data Entrada"
                }
                cols_existentes_leads = [c for c in colunas_leads.keys() if c in df_leads.columns]
                df_leads_exibicao = df_leads[cols_existentes_leads].rename(columns=colunas_leads)

                st.dataframe(df_leads_exibicao, use_container_width=True, hide_index=True)

                buffer_leads = io.BytesIO()
                with pd.ExcelWriter(buffer_leads, engine='xlsxwriter') as writer:
                    df_leads_exibicao.to_excel(writer, index=False, sheet_name='Leads')
                
                st.download_button(
                    label="📥 Baixar Base de Leads (Excel)",
                    data=buffer_leads.getvalue(),
                    file_name=f"relatorio_leads_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

    # ==============================================================================
    # ABA 2: GESTÃO DE MEETS
    # ==============================================================================
    with aba_meets:
        if isinstance(dados_meets, str) and dados_meets.startswith("erro:"):
            st.error(f"Erro ao buscar meets: {dados_meets}")
        elif not dados_meets:
            st.warning("Nenhum meet encontrado para o período.")
        else:
            df_meets = pd.DataFrame(dados_meets)
            
            df_meets['nome_operador'] = df_meets['usuario_id'].map(lambda uid: mapa_usuarios.get(uid, "Desconhecido"))
            df_meets['data_criacao'] = pd.to_datetime(df_meets['created_at']).dt.strftime('%d/%m/%Y')

            st.write("")
            op_disp = sorted(df_meets['nome_operador'].unique().tolist())
            ops_selecionados = st.multiselect("Filtrar Dashboard de Meets por Operador(es):", options=op_disp, default=[])

            df_filtrado_meets = df_meets[df_meets['nome_operador'].isin(ops_selecionados)] if ops_selecionados else df_meets

            if df_filtrado_meets.empty:
                st.info("Nenhum meet para o(s) operador(es) selecionado(s).")
            else:
                # --- KPIS MEETS ---
                t_meets = len(df_filtrado_meets)
                concluidos = len(df_filtrado_meets[df_filtrado_meets['status_meet'] == 'Concluído'])
                cancelados = len(df_filtrado_meets[df_filtrado_meets['status_meet'].isin(['Cancelado', 'Cancelado No-Show'])])
                tx_suc = (concluidos / t_meets * 100) if t_meets > 0 else 0

                k1, k2, k3, k4 = st.columns(4)
                with k1: render_card("Total Agendado", str(t_meets), "#1E3A8A")
                with k2: render_card("Concluídos", str(concluidos), "#059669")
                with k3: render_card("Cancelados", str(cancelados), "#DC2626")
                with k4: render_card("Taxa de Comparecimento", f"{tx_suc:.1f}%", "#7C3AED")

                st.write("---")

                # --- GRÁFICOS MEETS ---
                cm1, cm2 = st.columns([3, 2])
                with cm1:
                    titulo_secao("Volume Temporal de Meets")
                    df_temp_meet = df_filtrado_meets.groupby('data_criacao').size().reset_index(name='Qtd')
                    df_temp_meet['data_ordem'] = pd.to_datetime(df_temp_meet['data_criacao'], format='%d/%m/%Y')
                    df_temp_meet = df_temp_meet.sort_values('data_ordem')
                    
                    fig_linha_meet = px.line(df_temp_meet, x='data_criacao', y='Qtd', markers=True, color_discrete_sequence=['#2563EB'])
                    fig_linha_meet.update_layout(xaxis_title="", yaxis_title="Meets", margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_linha_meet, use_container_width=True)

                with cm2:
                    titulo_secao("Ações Realizadas")
                    df_acao = df_filtrado_meets.groupby('acao').size().reset_index(name='Qtd')
                    fig_pizza = px.pie(df_acao, values='Qtd', names='acao', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_pizza.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_pizza, use_container_width=True)

                # --- EXPORTAÇÃO DOS MEETS BRUTOS ---
                st.write("---")
                with st.expander("📊 Ver Dados de Meets (Bruto) e Exportar"):
                    colunas_amigaveis = {
                        "meet_id": "ID", "nome_operador": "Dono do Meet", "cnpj": "CNPJ", "pdv": "PDV",
                        "nome_lojista": "Lojista", "contato_lojista": "Contato", "data_meet": "Data Agendada",
                        "status_meet": "Status", "observacao": "Observação", "data_criacao": "Data de Criação"
                    }
                    
                    cols_existentes_meets = [c for c in colunas_amigaveis.keys() if c in df_filtrado_meets.columns]
                    df_meets_exibicao = df_filtrado_meets[cols_existentes_meets].rename(columns=colunas_amigaveis)

                    st.dataframe(df_meets_exibicao, use_container_width=True, hide_index=True)

                    buffer_meets = io.BytesIO()
                    with pd.ExcelWriter(buffer_meets, engine='xlsxwriter') as writer:
                        df_meets_exibicao.to_excel(writer, index=False, sheet_name='Meets')
                    
                    st.download_button(
                        label="📥 Baixar Dados de Meets (Excel)",
                        data=buffer_meets.getvalue(),
                        file_name=f"relatorio_meets_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
