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
    cabecalho_pagina("Dashboard de Meets", "Acompanhe a volumetria, os resultados da equipe e a evolução dos agendamentos.")

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
    def buscar_dados_dashboard(data_inicio_str, data_fim_str):
        try:
            resp = supabase.table("meets").select("*").gte("created_at", f"{data_inicio_str} 00:00:00").lte("created_at", f"{data_fim_str} 23:59:59").execute()
            return resp.data if resp.data else []
        except Exception as e:
            return f"erro: {e}"

    # ==========================================
    # FILTROS GLOBAIS
    # ==========================================
    with st.container(border=True):
        st.subheader("⚙️ Filtros de Período e Equipe")
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

    # Processamento dos dados no clique ou usando o cache da sessão
    if btn_atualizar or "dash_meets_dados_brutos" in st.session_state:
        if btn_atualizar:
            with st.spinner("Buscando dados no Supabase..."):
                str_ini = d_inicio.strftime("%Y-%m-%d")
                str_fim = d_fim.strftime("%Y-%m-%d")
                
                # Executa a busca cacheada
                dados_brutos = buscar_dados_dashboard(str_ini, str_fim)
                st.session_state["dash_meets_dados_brutos"] = dados_brutos

        dados = st.session_state.get("dash_meets_dados_brutos", [])

        if isinstance(dados, str) and dados.startswith("erro:"):
            st.error(f"Erro ao buscar dados para o dashboard: {dados}")
        elif not dados:
            st.warning("Nenhum dado encontrado para o período de datas selecionado.")
        else:
            # Transforma em DataFrame do Pandas para facilitar as agregações e filtros
            df = pd.DataFrame(dados)
            
            # Mapeia os nomes dos usuários a partir dos IDs
            mapa_usuarios = obter_mapa_usuarios()
            df['nome_operador'] = df['usuario_id'].map(lambda uid: mapa_usuarios.get(uid, "Usuário Desconhecido"))
            
            # Adiciona coluna de Data formatada (tirando a hora) para a linha temporal
            df['data_criacao'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y')

            # --- FILTRO EM MEMÓRIA POR OPERADOR ---
            st.write("")
            operadores_disponiveis = sorted(df['nome_operador'].unique().tolist())
            operadores_selecionados = st.multiselect(
                "Filtrar por Operador(es):", 
                options=operadores_disponiveis, 
                default=[],
                help="Deixe vazio para ver o resultado de todos os operadores."
            )

            # Aplica o filtro de operador no DataFrame (sem bater no banco de novo)
            if operadores_selecionados:
                df_filtrado = df[df['nome_operador'].isin(operadores_selecionados)]
            else:
                df_filtrado = df

            if df_filtrado.empty:
                st.info("Nenhum dado para o(s) operador(es) selecionado(s).")
                st.stop()

            # ==========================================
            # KPIS EM CARTÕES ESTILIZADOS
            # ==========================================
            st.write("---")
            
            total_meets = len(df_filtrado)
            concluidos = len(df_filtrado[df_filtrado['status_meet'] == 'Concluído'])
            cancelados = len(df_filtrado[df_filtrado['status_meet'].isin(['Cancelado', 'Cancelado No-Show'])])
            taxa_sucesso = (concluidos / total_meets * 100) if total_meets > 0 else 0

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                render_card("Total de Meets", str(total_meets), "#1E3A8A")  # Azul escuro
            with k2:
                render_card("Concluídos", str(concluidos), "#059669")       # Verde
            with k3:
                render_card("Cancelados", str(cancelados), "#DC2626")       # Vermelho
            with k4:
                render_card("Taxa de Conclusão", f"{taxa_sucesso:.1f}%", "#7C3AED") # Roxo

            st.write("---")

            # ==========================================
            # GRÁFICOS VISUAIS COM PLOTLY
            # ==========================================
            
            # LINHA 1 DE GRÁFICOS: Temporal e Pizza
            col_graf1, col_graf2 = st.columns([3, 2])

            with col_graf1:
                titulo_secao("Evolução Temporal (Meets por Dia)")
                df_temporal = df_filtrado.groupby('data_criacao').size().reset_index(name='Quantidade')
                # Garante ordenação cronológica correta convertendo para datetime novamente
                df_temporal['data_ordem'] = pd.to_datetime(df_temporal['data_criacao'], format='%d/%m/%Y')
                df_temporal = df_temporal.sort_values('data_ordem')
                
                fig_linha = px.line(df_temporal, x='data_criacao', y='Quantidade', markers=True, 
                                   color_discrete_sequence=['#2563EB'])
                fig_linha.update_layout(xaxis_title="", yaxis_title="Qtd de Meets", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_linha, use_container_width=True)

            with col_graf2:
                titulo_secao("Proporção de Ações")
                df_acao = df_filtrado.groupby('acao').size().reset_index(name='Quantidade')
                fig_pizza = px.pie(df_acao, values='Quantidade', names='acao', hole=0.4, 
                                   color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pizza.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_pizza, use_container_width=True)

            # LINHA 2 DE GRÁFICOS: Barras Horizontais (Operadores) e Barras (Status)
            col_graf3, col_graf4 = st.columns(2)

            with col_graf3:
                titulo_secao("Volume por Operador")
                df_op = df_filtrado.groupby('nome_operador').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=True)
                fig_bar_h = px.bar(df_op, x='Quantidade', y='nome_operador', orientation='h', 
                                   text='Quantidade', color_discrete_sequence=['#4F46E5'])
                fig_bar_h.update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_bar_h, use_container_width=True)

            with col_graf4:
                titulo_secao("Volume por Status")
                df_status = df_filtrado.groupby('status_meet').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False)
                fig_status = px.bar(df_status, x='status_meet', y='Quantidade', text='Quantidade', 
                                    color='status_meet', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_status.update_layout(xaxis_title="", yaxis_title="", showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_status, use_container_width=True)
            # ==========================================
            # TABELA DE DADOS E EXPORTAÇÃO
            # ==========================================
            st.write("---")
            with st.expander("📊 Ver Dados Detalhados (Planilha)"):
                # Seleciona e renomeia colunas para deixar a planilha limpa e profissional
                colunas_amigaveis = {
                    "meet_id": "ID",
                    "nome_operador": "Operador",
                    "cnpj": "CNPJ",
                    "pdv": "PDV",
                    "nome_lojista": "Lojista",
                    "contato_lojista": "Contato",
                    "data_meet": "Data Agendada",
                    "hora_meet": "Hora",
                    "acao": "Ação",
                    "status_meet": "Status",
                    "observacao": "Observação",
                    "data_criacao": "Data de Criação"
                }
                
                # Garante que só vai tentar exibir colunas que realmente voltaram do banco
                colunas_existentes = [c for c in colunas_amigaveis.keys() if c in df_filtrado.columns]
                df_exibicao = df_filtrado[colunas_existentes].rename(columns=colunas_amigaveis)

                # Exibe o dataframe interativo (permite ordenar clicando no cabeçalho)
                st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

                # Converte o DataFrame para Excel em memória
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_exibicao.to_excel(writer, index=False, sheet_name='Meets')
                
                # Botão de download
                st.download_button(
                    label="📥 Baixar Dados em Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"relatorio_meets_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
