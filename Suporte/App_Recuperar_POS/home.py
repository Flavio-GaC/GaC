import streamlit as st
import pandas as pd
from datetime import datetime

from theme import cabecalho_pagina, kpi, badge, campo, estado_vazio, titulo_secao

# Função auxiliar para formatar a data que vem do banco
def formatar_data(data_iso):
    if not data_iso:
        return "N/A"
    try:
        # Tira o "Z" ou "+00:00" do final para o datetime do Python entender
        data_limpa = data_iso.split("+")[0].replace("Z", "")
        dt = datetime.fromisoformat(data_limpa)
        return dt.strftime("%d/%m/%Y às %H:%M")
    except:
        return data_iso


def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mostrar_home(supabase):
    uid = st.session_state.get("uid")
    saudacao = ""
    try:
        resposta_usuario = supabase.table("usuarios").select("nome_completo").eq("id", uid).execute()
        if resposta_usuario.data:
            saudacao = f"Bem-vindo(a), {resposta_usuario.data[0]['nome_completo']}"
    except Exception:
        pass

    cabecalho_pagina("Dashboard de Devoluções", saudacao)

    # Filtros
    with st.container(border=True):
        titulo_secao("Filtros de consulta")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_pdv = st.text_input("Buscar por PDV (opcional)", placeholder="Ex.: 123456")
        with col_f2:
            filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "PAC", "COLETA"])
        with col_f3:
            limite = st.selectbox("Quantidade de registros", [10, 50, 100])

        buscar = st.button("Buscar Dados", type="primary")

    if buscar:
        with st.spinner("Buscando dados..."):
            try:
                query = supabase.table("devolucoes").select("*").order("data_hora", desc=True).limit(limite)

                if filtro_pdv:
                    query = query.eq("pdv", filtro_pdv)
                if filtro_tipo != "Todos":
                    query = query.eq("tipo_devolucao", filtro_tipo)

                resposta = query.execute()
                dados = resposta.data

                if dados:
                    # --- RESUMO DOS REGISTROS CARREGADOS ---
                    total_registros = len(dados)
                    total_pac = sum(1 for l in dados if l.get("tipo_devolucao") == "PAC")
                    total_coleta = sum(1 for l in dados if l.get("tipo_devolucao") == "COLETA")
                    total_equipamentos = sum(int(l.get("qtd") or 0) for l in dados)
                    valor_acumulado = sum(
                        (int(l.get("qtd") or 0) * float(l.get("valor_reais") or 0)) for l in dados
                    )

                    titulo_secao("Resumo dos registros carregados")
                    k1, k2, k3, k4 = st.columns(4)
                    with k1:
                        kpi("Registros", total_registros, "Resultado da consulta")
                    with k2:
                        kpi("PAC / Coleta", f"{total_pac} / {total_coleta}", "Por tipo de devolução")
                    with k3:
                        kpi("Equipamentos", total_equipamentos, "Soma das quantidades")
                    with k4:
                        kpi("Valor acumulado", formatar_moeda_br(valor_acumulado), "Qtd × valor unitário")

                    st.write("")
                    titulo_secao(f"{total_registros} registro(s) encontrado(s)")

                    # Desenha um quadro (card) para cada registro
                    for linha in dados:
                        with st.container(border=True):
                            # Cabeçalho do Card
                            st.markdown(
                                f"""<div class="rec-head">
                                      <div class="rec-title">PDV {linha.get('pdv', 'N/A')}
                                        <span>· {linha.get('nome_fantasia', 'N/A')}</span></div>
                                      <div>{badge(linha.get('tipo_devolucao'))}</div>
                                    </div>""",
                                unsafe_allow_html=True,
                            )

                            # Divide as informações em 3 colunas dentro do quadro
                            c1, c2, c3 = st.columns(3)

                            with c1:
                                campo("Data/Hora", formatar_data(linha.get('data_hora')))
                                campo("Motivo", linha.get('motivo'))
                                campo("Consultor", linha.get('consultor'))
                                campo("Setor", linha.get('setor'))
                                campo("Registrado por", linha.get('email'))

                            with c2:
                                qtd = linha.get('qtd') or 0
                                valor_unitario = linha.get('valor_reais') or 0
                                valor_total = qtd * float(valor_unitario)

                                campo("Modelo", linha.get('modelo'))
                                campo("Qtd", qtd)
                                campo("Valor Total", formatar_moeda_br(valor_total))

                                # Exibição condicional de PAC / Rastreio
                                tipo = linha.get('tipo_devolucao')
                                if tipo == "PAC" and linha.get("cod_pac"):
                                    campo("Cód. PAC", linha.get('cod_pac'), mono=True)
                                elif tipo == "COLETA" and linha.get("cod_rastreio"):
                                    campo("Cód. Rastreio", linha.get('cod_rastreio'), mono=True)

                            with c3:
                                campo("Cliente", linha.get('cliente'))
                                campo("Endereço", linha.get('endereco'))
                                campo("Cidade/UF", f"{linha.get('cidade', 'N/A')} - {linha.get('uf', 'N/A')}")
                                campo("CEP", linha.get('cep'))

                else:
                    estado_vazio(
                        "Nenhum registro encontrado",
                        "Nenhum registro encontrado com os parâmetros atuais. Ajuste os filtros e tente novamente.",
                        "🔍",
                    )

            except Exception as e:
                st.error(f"Erro ao buscar dados: {e}")
    else:
        estado_vazio(
            "Pronto para consultar",
            "Defina os filtros acima e clique em “Buscar Dados” para carregar as devoluções."
        )
