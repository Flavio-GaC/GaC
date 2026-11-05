import io
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from routers.brasilcard.dashboard import buscar_usuarios_dash


# ==========================================
# FUNÇÕES AUXILIARES DA EXTRAÇÃO
# ==========================================
@st.cache_data(show_spinner=False, ttl=3600)
def buscar_mapa_todos_usuarios_extracao(_supabase):
    try:
        resp = _supabase.table("usuarios").select("id, nome_completo").execute()
        return {u["id"]: u["nome_completo"] for u in (resp.data or [])}
    except Exception:
        return {}


@st.cache_data(show_spinner=False, ttl=3600)
def buscar_status_unicos_leads(_supabase):
    status_set = set()
    offset = 0
    try:
        while True:
            resp = (
                _supabase.table("leads")
                .select("status_atual")
                .range(offset, offset + 999)
                .execute()
            )
            if not resp.data:
                break
            for row in resp.data:
                st_val = str(row.get("status_atual") or "").strip()
                if st_val:
                    status_set.add(st_val)
            if len(resp.data) < 1000:
                break
            offset += 1000
    except Exception:
        pass
    return sorted(list(status_set))


def formatar_cnpj_extracao(val):
    if pd.isna(val) or not str(val).strip():
        return ""
    digitos = "".join(filter(str.isdigit, str(val)))
    if len(digitos) == 14:
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    return str(val)


def formatar_data_extracao(serie):
    dt = pd.to_datetime(serie, errors="coerce", utc=True)
    return dt.dt.tz_localize(None).dt.strftime("%d/%m/%Y %H:%M").fillna("")


def mostrar_extrair_leads(supabase):
    # Variáveis que antes vinham dos filtros do topo do Dashboard
    dt_inicio = datetime.now() - timedelta(days=7)
    dt_final = datetime.now()

    usuarios_bd = buscar_usuarios_dash(supabase)
    mapa_usuarios = {u['nome_completo']: u['id'] for u in usuarios_bd}

    st.markdown("### 📥 Central de Extração de Dados")
    st.caption("Configure os parâmetros abaixo para visualizar e exportar relatórios personalizados (limite de até 10.000 linhas por extração).")

    with st.container(border=True):
        st.markdown("#### 1. Configurar Parâmetros da Extração")

        col_ext1, col_ext2, col_ext3 = st.columns([1.4, 1.3, 1])
        with col_ext1:
            tipo_base_ext = st.selectbox(
                "Qual base você deseja extrair?",
                options=[
                    "📋 Base de Leads (Posição Atual)",
                    "🕒 Histórico de Tentativas (Auditoria)"
                ],
                key="ext_tipo_base"
            )
        with col_ext2:
            if tipo_base_ext.startswith("📋"):
                mapa_campo_data = {
                    "Data de Criação (created_at)": "created_at",
                    "Última Atualização (updated_at)": "updated_at",
                    "Data de Geração do PDV (data_pdv_gerado)": "data_pdv_gerado"
                }
            else:
                mapa_campo_data = {
                    "Data da Interação (created_at)": "created_at"
                }
            label_campo_data = st.selectbox(
                "Filtrar período por qual data?",
                options=list(mapa_campo_data.keys()),
                key="ext_campo_data"
            )
            coluna_data_ext = mapa_campo_data[label_campo_data]
        with col_ext3:
            limite_ext = st.number_input(
                "Limite de Linhas (Máx: 10.000)",
                min_value=100,
                max_value=10000,
                value=10000,
                step=500,
                key="ext_limite_linhas"
            )

        col_dt_ext1, col_dt_ext2, col_f_ext1, col_f_ext2 = st.columns([1, 1, 1.2, 1.5])
        with col_dt_ext1:
            dt_ini_ext = st.date_input("Período Inicial", value=dt_inicio, format="DD/MM/YYYY", key="ext_dt_ini")
        with col_dt_ext2:
            dt_fim_ext = st.date_input("Período Final", value=dt_final, format="DD/MM/YYYY", key="ext_dt_fim")

        if tipo_base_ext.startswith("📋"):
            with col_f_ext1:
                fases_sel_ext = st.multiselect(
                    "Fase Atual (Opcional)",
                    options=[1, 2, 3],
                    format_func=lambda x: f"Fase {x} ({'Pré-Venda' if x == 1 else ('Comercial' if x == 2 else 'BKO')})",
                    key="ext_fases_leads"
                )
            with col_f_ext2:
                lista_status_unicos = buscar_status_unicos_leads(supabase)
                opcoes_status_ext = ["Selecionar Todos"] + lista_status_unicos

                if "ext_status_leads" not in st.session_state:
                    st.session_state["ext_status_leads"] = ["Selecionar Todos"]
                if "ext_status_leads_prev" not in st.session_state:
                    st.session_state["ext_status_leads_prev"] = ["Selecionar Todos"]

                def atualizar_selecao_status_ext():
                    atual = st.session_state.get("ext_status_leads", [])
                    anterior = st.session_state.get("ext_status_leads_prev", ["Selecionar Todos"])

                    if len(atual) > 1 and "Selecionar Todos" in atual:
                        if "Selecionar Todos" not in anterior:
                            st.session_state["ext_status_leads"] = ["Selecionar Todos"]
                        else:
                            st.session_state["ext_status_leads"] = [s for s in atual if s != "Selecionar Todos"]

                    st.session_state["ext_status_leads_prev"] = list(st.session_state.get("ext_status_leads", []))

                status_sel_ext = st.multiselect(
                    "Status",
                    options=opcoes_status_ext,
                    key="ext_status_leads",
                    on_change=atualizar_selecao_status_ext
                )
            meios_sel_ext = []
        else:
            with col_f_ext1:
                fases_sel_ext = st.multiselect(
                    "Fase na Época (Opcional)",
                    options=[1, 2, 3],
                    format_func=lambda x: f"Fase {x} ({'Pré-Venda' if x == 1 else ('Comercial' if x == 2 else 'BKO')})",
                    key="ext_fases_hist"
                )
            with col_f_ext2:
                meios_sel_ext = st.multiselect(
                    "Meio de Contato (Opcional)",
                    options=["Whatsapp", "Ligação - VOX", "Ligação - Whatsapp", "Fortics", "E-mail", "Meet"],
                    key="ext_meios_hist"
                )
            status_sel_ext = []

        col_chk, col_btn_ext = st.columns([2.5, 1.2])
        with col_btn_ext:
            btn_buscar_ext = st.button("🔍 Buscar Dados para Extração", type="primary", use_container_width=True)

    if btn_buscar_ext:
        if dt_ini_ext > dt_fim_ext:
            st.error("⚠️ O Período Inicial não pode ser maior que o Período Final.")
        else:
            with st.spinner("Consultando banco de dados e preparando planilha..."):
                try:
                    mapa_nomes_ids = buscar_mapa_todos_usuarios_extracao(supabase)
                    registros_ext = []
                    offset_ext = 0
                    limite_max = int(limite_ext)
                    tabela_alvo = "leads" if tipo_base_ext.startswith("📋") else "historico_leads"

                    ids_filtro_usuario = [u["id"] for u in usuarios_bd]

                    status_filtrados = [s for s in status_sel_ext if s != "Selecionar Todos"]
                    filtrar_por_status = (
                        tabela_alvo == "leads"
                        and bool(status_filtrados)
                        and ("Selecionar Todos" not in status_sel_ext)
                    )

                    while len(registros_ext) < limite_max:
                        tamanho_lote = min(1000, limite_max - len(registros_ext))
                        query_ext = (
                            supabase.table(tabela_alvo)
                            .select("*")
                            .gte(coluna_data_ext, f"{dt_ini_ext} 00:00:00")
                            .lte(coluna_data_ext, f"{dt_fim_ext} 23:59:59")
                        )

                        if tabela_alvo == "leads":
                            if fases_sel_ext:
                                query_ext = query_ext.in_("fase_atual", fases_sel_ext)
                            if filtrar_por_status:
                                query_ext = query_ext.in_("status_atual", status_filtrados)
                            if ids_filtro_usuario:
                                query_ext = query_ext.in_("responsavel_atual", ids_filtro_usuario)
                        else:
                            if fases_sel_ext:
                                query_ext = query_ext.in_("fase_na_epoca", fases_sel_ext)
                            if meios_sel_ext:
                                query_ext = query_ext.in_("meio_contato", meios_sel_ext)
                            if ids_filtro_usuario:
                                query_ext = query_ext.in_("usuario_id", ids_filtro_usuario)

                        resp_ext = (
                            query_ext
                            .order(coluna_data_ext, desc=True)
                            .range(offset_ext, offset_ext + tamanho_lote - 1)
                            .execute()
                        )

                        lote_dados = resp_ext.data or []
                        if not lote_dados:
                            break

                        registros_ext.extend(lote_dados)
                        if len(lote_dados) < tamanho_lote:
                            break
                        offset_ext += tamanho_lote

                    df_bruto = pd.DataFrame(registros_ext)

                    if df_bruto.empty:
                        st.session_state["df_extracao_pronto"] = pd.DataFrame()
                        st.session_state["meta_extracao"] = {"vazio": True}
                    else:
                        if tabela_alvo == "leads":
                            df_tratado = pd.DataFrame()
                            df_tratado["ID LEAD"] = df_bruto.get("id", "")
                            df_tratado["CNPJ"] = df_bruto.get("cnpj", pd.Series(dtype=str)).apply(formatar_cnpj_extracao)
                            df_tratado["EMPRESA"] = df_bruto.get("nome_empresa", "").fillna("")
                            df_tratado["CONTATO DA LOJA"] = df_bruto.get("contato_loja", "").fillna("")
                            df_tratado["TELEFONE"] = df_bruto.get("telefone", "").fillna("").astype(str)
                            df_tratado["SEGMENTO"] = df_bruto.get("segmento", "").fillna("")
                            df_tratado["FATURAMENTO MENSAL"] = df_bruto.get("faturamento_mensal", "").fillna("")
                            df_tratado["ORIGEM"] = df_bruto.get("origem", "").fillna("")
                            df_tratado["FASE ATUAL"] = df_bruto.get("fase_atual", "")
                            df_tratado["STATUS ATUAL"] = df_bruto.get("status_atual", "").fillna("")
                            df_tratado["RESPONSÁVEL ATUAL"] = df_bruto.get("responsavel_atual", pd.Series(dtype=str)).map(mapa_nomes_ids).fillna("")
                            df_tratado["PRÉ-VENDA"] = df_bruto.get("id_pre_venda", pd.Series(dtype=str)).map(mapa_nomes_ids).fillna("")
                            df_tratado["ESPECIALISTA"] = df_bruto.get("id_especialista", pd.Series(dtype=str)).map(mapa_nomes_ids).fillna("")
                            df_tratado["BKO"] = df_bruto.get("id_bko", pd.Series(dtype=str)).map(mapa_nomes_ids).fillna("")
                            df_tratado["MEIO FECHAMENTO"] = df_bruto.get("meio_fechamento", "").fillna("")
                            df_tratado["REDE OU INDIVIDUAL"] = df_bruto.get("rede_ou_individual", "").fillna("")
                            df_tratado["PRIVATE"] = df_bruto.get("is_private", "").fillna("")
                            df_tratado["PRIVATE PAGO"] = df_bruto.get("private_pago", "").fillna("")
                            df_tratado["VALOR ADESÃO"] = df_bruto.get("valor_adesao", "")
                            df_tratado["ADESÃO PAGA"] = df_bruto.get("adesao_paga", "").fillna("")
                            df_tratado["EMITIR OU RECEBER"] = df_bruto.get("emitir_ou_receber", "").fillna("")
                            df_tratado["E-MAIL LOJISTA"] = df_bruto.get("email_loja", "").fillna("")
                            df_tratado["RESPONSÁVEL LOJA"] = df_bruto.get("responsavel_loja", "").fillna("")
                            df_tratado["SUPERVISOR"] = df_bruto.get("supervisor_responsavel", "").fillna("")
                            df_tratado["SETOR INDICAÇÃO"] = df_bruto.get("setor_indicacao", "").fillna("")
                            df_tratado["OBSERVAÇÃO FINAL"] = df_bruto.get("observacao_final", "").fillna("")
                            df_tratado["DATA CRIAÇÃO"] = formatar_data_extracao(df_bruto["created_at"]) if "created_at" in df_bruto else ""
                            df_tratado["ÚLTIMA ATUALIZAÇÃO"] = formatar_data_extracao(df_bruto["updated_at"]) if "updated_at" in df_bruto else ""
                            df_tratado["DATA PDV GERADO"] = formatar_data_extracao(df_bruto["data_pdv_gerado"]) if "data_pdv_gerado" in df_bruto else ""
                        else:
                            df_tratado = pd.DataFrame()
                            df_tratado["ID HISTÓRICO"] = df_bruto.get("id", "")
                            df_tratado["ID LEAD"] = df_bruto.get("lead_id", "")
                            df_tratado["DATA INTERAÇÃO"] = formatar_data_extracao(df_bruto["created_at"]) if "created_at" in df_bruto else ""
                            df_tratado["CONSULTOR"] = df_bruto.get("usuario_id", pd.Series(dtype=str)).map(mapa_nomes_ids).fillna("")
                            df_tratado["FASE NA ÉPOCA"] = df_bruto.get("fase_na_epoca", "")
                            df_tratado["TENTATIVA"] = df_bruto.get("tentativa", "")
                            df_tratado["MEIO DE CONTATO"] = df_bruto.get("meio_contato", "").fillna("")
                            df_tratado["HOUVE CONTATO"] = df_bruto.get("houve_contato", "").fillna("")
                            df_tratado["STATUS ANTERIOR"] = df_bruto.get("status_anterior", "").fillna("")
                            df_tratado["STATUS NOVO"] = df_bruto.get("status_novo", "").fillna("")
                            df_tratado["OBSERVAÇÃO"] = df_bruto.get("observacao", "").fillna("")

                        st.session_state["df_extracao_pronto"] = df_tratado
                        st.session_state["meta_extracao"] = {
                            "vazio": False,
                            "total": len(df_tratado),
                            "limite": limite_max,
                            "tipo": "leads" if tabela_alvo == "leads" else "historico",
                            "dt_ini": dt_ini_ext.strftime("%d-%m-%Y"),
                            "dt_fim": dt_fim_ext.strftime("%d-%m-%Y")
                        }
                except Exception as e:
                    st.error(f"Erro ao realizar a extração: {e}")

    # ==========================================
    # ETAPAS 2 E 3: PRÉ-VISUALIZAÇÃO E DOWNLOAD
    # ==========================================
    meta_ext = st.session_state.get("meta_extracao")
    df_ext_salvo = st.session_state.get("df_extracao_pronto", pd.DataFrame())

    if meta_ext:
        if meta_ext.get("vazio") or df_ext_salvo.empty:
            st.warning("Nenhum registro encontrado para os filtros e período selecionados.")
        else:
            st.write("")
            with st.container(border=True):
                st.markdown("#### 2. Pré-visualização e Seleção de Colunas")

                qtd_encontrada = meta_ext["total"]
                limite_usado = meta_ext["limite"]

                if qtd_encontrada >= limite_usado:
                    st.warning(
                        f"⚠️ **Limite atingido:** Foram extraídas **{qtd_encontrada}** linhas (teto configurado de {limite_usado} registros). "
                        "Caso precise de dados adicionais, reduza o intervalo de datas."
                    )
                else:
                    st.success(f"✅ Extração concluída! Foram encontrados **{qtd_encontrada}** registros dentro dos critérios selecionados.")

                todas_colunas = list(df_ext_salvo.columns)
                colunas_escolhidas = st.multiselect(
                    "Colunas incluídas na planilha (remova ou reordene como preferir):",
                    options=todas_colunas,
                    default=todas_colunas,
                    key="ext_colunas_selecionadas"
                )

                if not colunas_escolhidas:
                    st.warning("Selecione pelo menos uma coluna para visualizar e exportar.")
                else:
                    df_final_export = df_ext_salvo[colunas_escolhidas]

                    st.caption(f"Exibindo prévia das primeiras **{min(50, len(df_final_export))}** linhas de um total de **{len(df_final_export)}**:")
                    st.dataframe(df_final_export.head(50), use_container_width=True, hide_index=True)

                    st.write("---")
                    st.markdown("#### 3. Baixar Planilha")

                    nome_base_arq = f"extracao_{meta_ext['tipo']}_{meta_ext['dt_ini']}_a_{meta_ext['dt_fim']}"
                    csv_bytes = df_final_export.to_csv(index=False, sep=";").encode("utf-8-sig")

                    xlsx_bytes = None
                    for motor_excel in ["openpyxl", "xlsxwriter"]:
                        try:
                            buffer_excel = io.BytesIO()
                            with pd.ExcelWriter(buffer_excel, engine=motor_excel) as writer:
                                df_final_export.to_excel(writer, index=False, sheet_name="Extracao")
                            xlsx_bytes = buffer_excel.getvalue()
                            break
                        except Exception:
                            continue

                    col_dl1, col_dl2, col_dl_esp = st.columns([1.2, 1.2, 2])
                    with col_dl1:
                        if xlsx_bytes is not None:
                            st.download_button(
                                label="📥 Baixar em Excel (.xlsx)",
                                data=xlsx_bytes,
                                file_name=f"{nome_base_arq}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                use_container_width=True
                            )
                        else:
                            st.download_button(
                                label="📥 Baixar Planilha (.csv p/ Excel)",
                                data=csv_bytes,
                                file_name=f"{nome_base_arq}.csv",
                                mime="text/csv",
                                type="primary",
                                use_container_width=True
                            )
                    with col_dl2:
                        st.download_button(
                            label="📄 Baixar em CSV (.csv)",
                            data=csv_bytes,
                            file_name=f"{nome_base_arq}.csv",
                            mime="text/csv",
                            type="secondary",
                            use_container_width=True
                        )
