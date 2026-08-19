import streamlit as st
from datetime import datetime, timedelta
import re
from themes.theme import cabecalho_pagina, titulo_secao

# --- FUNÇÕES AUXILIARES ---
def adicionar_dias_uteis(data_inicial, dias):
    data_atual = data_inicial
    while dias > 0:
        data_atual += timedelta(days=1)
        # 5 = Sábado, 6 = Domingo
        if data_atual.weekday() < 5:
            dias -= 1
    return data_atual

def formatar_moeda(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- POP-UP PARA COPIAR TEXTO ---
@st.dialog("📋 Texto Gerado para o Cliente", width="large")
def popup_copiar_texto(texto):
    st.markdown("Passe o mouse sobre a caixa abaixo e clique no **ícone de copiar** no canto superior direito para copiar o texto inteiro.")
    st.code(texto, language="text")

# --- FUNÇÃO PRINCIPAL UNIFICADA ---
def mostrar_devolucao(supabase):
    cabecalho_pagina(
        "Gestão de Devoluções",
        "Registre novas ocorrências com texto automatizado e acompanhe o histórico com filtros otimizados.",
    )

    # Abas unificadas: Cadastro e Acompanhamento
    aba_novo, aba_acompanhar = st.tabs(["📝 Registrar Devolução", "🔄 Acompanhar Devoluções"])

    usuario_id = st.session_state.get("uid")

    # ==========================================
    # ABA 1: REGISTRAR DEVOLUÇÃO (SUAS REGRAS ORIGINAIS)
    # ==========================================
    with aba_novo:
        with st.container(border=True):
            titulo_secao("Atenção aos tipos de devolução")
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.info("**COLETA:** os Correios vão até o endereço do lojista para recuperar a máquina.")
            with col_i2:
                st.warning("**PAC:** o lojista deve ir até uma agência dos Correios para devolver a máquina.")

            tipo_devolucao = st.selectbox("Tipo de Devolução *", ["", "PAC", "COLETA"], key="select_tipo_dev")

        opcoes_motivo = [""]
        bloquear_pac = False
        bloquear_rastreio = False

        if tipo_devolucao == "PAC":
            opcoes_motivo = ["", "DEVOLUÇÃO DE POS", "DEVOLUÇÃO ACESSORIOS"]
            bloquear_rastreio = True
        elif tipo_devolucao == "COLETA":
            opcoes_motivo = ["", "COLETA DE POS", "COLETA DE ACESSÓRIO"]
            bloquear_pac = True
        else:
            opcoes_motivo = ["", "DEVOLUÇÃO DE POS", "COLETA DE POS", "DEVOLUÇÃO ACESSORIOS", "COLETA DE ACESSÓRIO"]

        st.write("")
        with st.form("form_nova_devolucao", clear_on_submit=True):
            titulo_secao("Dados da devolução")
            col1, col2 = st.columns(2)

            with col1:
                pdv = st.text_input("Código do PDV *", help="Obrigatório. Deve existir na tabela PDV.", max_chars=10)
                modelo = st.selectbox("Modelo da Máquina", ["", "S920", "P2 A11", "D195", "Q92X", "C680"])
                qtd = st.number_input("Quantidade", min_value=1, step=1)
                valor_reais = st.number_input("Valor (R$)", value=1050.0, format="%.2f")

            with col2:
                setor = st.selectbox("Setor", ["", "RECUPERAÇÃO", "SUPORTE"])
                motivo = st.selectbox("Motivo da Devolução", opcoes_motivo)

                cod_pac = st.text_input("Código PAC", disabled=bloquear_pac)
                cod_rastreio = st.text_input("Código de Rastreio", disabled=bloquear_rastreio)

            st.caption("Campos com * são obrigatórios. Data/Hora e Fuso Horário do Brasil são gerenciados pelo sistema.")
            st.write("")
            submit = st.form_submit_button("Registrar Devolução", type="primary", use_container_width=True)

        if submit:
            if not tipo_devolucao:
                st.error("Selecione o Tipo de Devolução antes de registrar.")
            elif not pdv:
                st.error("O campo Código do PDV é obrigatório.")
            elif motivo not in opcoes_motivo:
                st.error("Conflito: O Motivo selecionado não corresponde ao Tipo de Devolução. Selecione o motivo novamente.")
            else:
                try:
                    with st.spinner("Registrando devolução..."):
                        pdv_limpo = re.sub(r"\D", "", pdv)

                        # Valida PDV no banco
                        resposta_pdv = supabase.table("pdv").select("contato, fantasia, endereco, cidade, uf, cep").eq("pdv", pdv_limpo).execute()
                        if not resposta_pdv.data:
                            # Tenta buscar sem limpar caso o PDV tenha letras/formato customizado
                            resposta_pdv = supabase.table("pdv").select("contato, fantasia, endereco, cidade, uf, cep").eq("pdv", pdv).execute()
                            if not resposta_pdv.data:
                                st.error("PDV não encontrado no banco de dados.")
                                st.stop()
                            pdv_alvo = pdv
                        else:
                            pdv_alvo = pdv_limpo
                        
                        dados_pdv = resposta_pdv.data[0]
                        uid = st.session_state.get("uid")
                        
                        # Busca nome do usuário
                        resposta_usuario = supabase.table("usuarios").select("nome_completo").eq("id", uid).execute()
                        nome_consultor = resposta_usuario.data[0]["nome_completo"] if resposta_usuario.data else None

                        # Busca email de autenticação
                        usuario_auth = supabase.auth.get_user()
                        email_usuario = usuario_auth.user.email if usuario_auth else None

                        pac_final = None if (bloquear_pac or not cod_pac) else cod_pac
                        rastreio_final = None if (bloquear_rastreio or not cod_rastreio) else cod_rastreio

                        dados = {
                            "pdv": pdv_alvo,
                            "tipo_devolucao": tipo_devolucao,
                            "email": email_usuario,
                            "modelo": modelo if modelo else None,
                            "qtd": qtd,
                            "valor_reais": float(valor_reais),
                            "consultor": nome_consultor,
                            "setor": setor if setor else None,
                            "motivo": motivo if motivo else None,
                            "cod_pac": pac_final,
                            "cod_rastreio": rastreio_final,
                            "cliente": dados_pdv.get("contato"),
                            "nome_fantasia": dados_pdv.get("fantasia"),
                            "endereco": dados_pdv.get("endereco"),
                            "cidade": dados_pdv.get("cidade"),
                            "uf": dados_pdv.get("uf"),
                            "cep": dados_pdv.get("cep")
                        }

                        # Insere no banco
                        supabase.table("devolucoes").insert(dados).execute()

                    st.success("Devolução registrada com sucesso!")

                    # Gera o texto formatado original
                    data_atual = datetime.now()
                    data_atual_str = data_atual.strftime("%d/%m/%Y")
                    valor_total = qtd * float(valor_reais)
                    texto_final = ""

                    if tipo_devolucao == "COLETA":
                        texto_final = f"""Prezado(a) {dados_pdv.get('contato', 'N/A')} | {dados_pdv.get('fantasia', 'N/A')},

Você será visitado(a) por um funcionário dos Correios, devidamente uniformizado e portando o crachá de identificação, que efetuará a Coleta de Encomenda em seu endereço, conforme dados abaixo:

Número do Pedido de Coleta: {pac_final or 'N/A'}
Autorizador da Postagem: BOLT CARD INSTITUICAO DE PAGAMENTOS LTDA
Quantidade de objeto: {qtd}
Número(s) do(s) objeto(s): {rastreio_final or 'N/A'}
Data da Coleta: {data_atual_str}
Conteúdo: {qtd}, {modelo or 'N/A'}

Não é necessário imprimir este e-mail.

Serviços Autorizados
PAC Reverso (03301)
Valor Declarado de R$ {formatar_moeda(valor_total)}

Para agilizar a coleta da sua encomenda, solicitamos anotar o número do pedido de coleta ou o número do objeto na embalagem utilizando uma caneta.

Endereço de coleta:
{pdv_alvo} | {dados_pdv.get('fantasia', 'N/A')}
{dados_pdv.get('endereco', 'N/A')}
{dados_pdv.get('cidade', 'N/A')} - {dados_pdv.get('uf', 'N/A')}
CEP: {dados_pdv.get('cep', 'N/A')}

Endereço do Destinatário:
BOLT CARD INSTITUICAO DE PAGAMENTOS LTDA
Avenida Francisco Wenceslau dos Anjos 257, CENTRO
MONTE BELO - MG
CEP: 37115-000"""

                    elif tipo_devolucao == "PAC":
                        data_validade = adicionar_dias_uteis(data_atual, 5)
                        data_validade_str = data_validade.strftime("%d/%m/%Y")
                        valor_pac = qtd * 1050

                        texto_final = f"""Assunto: AUTORIZAÇÃO DE POSTAGEM - BOLTCARD | BRASILCARD

Olá! Tudo bem?

Segue abaixo o código de autorização de postagem solicitado.
Pronto, agora basta embalar a máquina, junto de todos os seus componentes originais e postar nos Correios utilizando o código de devolução da máquina.

Solicitação de Autorização de Postagem em Agência
Código da Autorização de Postagem: {pac_final or 'N/A'}
Emitido em: {data_atual_str}
Data de Validade: {data_validade_str}
Serviço de Encomenda: PAC Reverso (03301)
Remetente autorizado: {dados_pdv.get('contato', 'N/A')} | {dados_pdv.get('fantasia', 'N/A')}
Quantidade de objetos: {qtd}

Para utilizá-la, o consumidor deverá se dirigir a uma Agência Própria ou Franqueada dos Correios, levando consigo, obrigatoriamente, o Código de Autorização e o objeto para postagem.

Serviços Autorizados:
Aquisição de Embalagem: Não
Valor Declarado de R$ {formatar_moeda(valor_pac)}

Ressaltamos que é apenas o valor declarado da máquina, não sendo necessário efetivar nenhum tipo de pagamento, pois esse código é sem custo algum e totalmente gratuito.

Pedimos, por gentileza, que se atente ao prazo de validade do código, pois não conseguimos gerar um novo.
Assim que realizar a postagem, nos encaminhe uma foto do comprovante, por gentileza.

DESTINATÁRIO: ENDEREÇO SEDE BOLT CARD
28.080.769/0001-86
BOLT CARD INSTITUICAO DE PAGAMENTOS LTDA
Av. Jorge Viera 257, Centro
Monte Belo - MG
CEP: 37115000
35 35732600"""

                    popup_copiar_texto(texto_final)

                except Exception as e:
                    st.error(f"Erro ao registrar: {e}")

    # ==========================================
    # ABA 2: ACOMPANHAR DEVOLUÇÕES (COM PAGINAÇÃO E CACHE)
    # ==========================================
    with aba_acompanhar:
        titulo_secao("Filtros de Acompanhamento (Com Paginação)")

        # Inicializa o controle de página no session_state se não existir
        if "dev_pagina" not in st.session_state:
            st.session_state["dev_pagina"] = 0

        # Função com Cache ajustada para aceitar paginação (limit e offset)
        @st.cache_data(show_spinner=False, ttl=1800)
        def buscar_devolucoes_paginadas(modo, param_busca, data_inicio, data_fim, uid_atual, pagina):
            try:
                itens_por_pagina = 10
                inicio = pagina * itens_por_pagina
                fim = inicio + itens_por_pagina - 1

                query = supabase.table("devolucoes").select("*", count="exact")
                
                if modo == "Por PDV":
                    query = query.eq("pdv", param_busca)
                elif modo == "Minhas Devoluções":
                    query = query.eq("criado_por", uid_atual)
                
                # Filtro por intervalo de datas
                query = query.gte("created_at", f"{data_inicio} 00:00:00").lte("created_at", f"{data_fim} 23:59:59")
                
                # Aplica a ordenação e a paginação por range
                resp = query.order("created_at", desc=True).range(inicio, fim).execute()
                
                return {
                    "dados": resp.data if resp.data else [],
                    "total": resp.count if hasattr(resp, "count") and resp.count is not None else 0
                }
            except Exception as e:
                return f"erro: {e}"

        f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
        
        with f1:
            modo_filtro = st.selectbox("Filtrar por", ["Por PDV", "Minhas Devoluções"], key="sel_modo_dev_pag")
        with f2:
            if modo_filtro == "Por PDV":
                val_pdv = st.text_input("Digite o PDV", max_chars=10, placeholder="Ex: 123456", key="input_filtro_pdv_pag")
            else:
                val_pdv = ""
                st.info("Filtro focado no seu usuário.")
        with f3:
            d_inicio = st.date_input("Data Inicial", format="DD/MM/YYYY", key="dev_ini_pag")
            d_fim = st.date_input("Data Final", format="DD/MM/YYYY", key="dev_fim_pag")
        with f4:
            st.write("")
            st.write("")
            btn_filtrar = st.button("Pesquisar", type="primary", use_container_width=True, key="btn_pesq_dev_pag")

        # Se o usuário clicar em pesquisar, reseta a página para a primeira (0)
        if btn_filtrar:
            st.session_state["dev_pagina"] = 0
            if modo_filtro == "Por PDV" and not val_pdv.strip():
                st.warning("Informe o PDV para realizar a busca.")
                st.session_state["devs_resultado"] = {"dados": [], "total": 0}
            else:
                with st.spinner("Buscando registros..."):
                    pdv_limpo = re.sub(r"\D", "", val_pdv) if modo_filtro == "Por PDV" else ""
                    str_inicio = d_inicio.strftime("%Y-%m-%d")
                    str_fim = d_fim.strftime("%Y-%m-%d")
                    
                    resultado = buscar_devolucoes_paginadas(
                        modo_filtro, pdv_limpo, str_inicio, str_fim, usuario_id, st.session_state["dev_pagina"]
                    )
                    st.session_state["devs_resultado"] = resultado

        # Garante que existe resultado carregado na sessão
        resultado_atual = st.session_state.get("devs_resultado", {"dados": [], "total": 0})

        if isinstance(resultado_atual, str) and resultado_atual.startswith("erro:"):
            st.error(f"Erro na consulta: {resultado_atual}")
        else:
            dados_devs = resultado_atual.get("dados", [])
            total_registros = resultado_atual.get("total", 0)

            if total_registros > 0:
                st.write("---")
                st.caption(f"Exibindo página **{st.session_state['dev_pagina'] + 1}** | Total de registros encontrados: **{total_registros}** (10 por página).")
                
                for dev in dados_devs:
                    dev_id = dev.get("id")
                    pdv_val = dev.get("pdv", "N/A")
                    fantasia = dev.get("nome_fantasia", "N/A")
                    tipo = dev.get("tipo_devolucao", "N/A")
                    consultor_nome = dev.get("consultor", "N/A")
                    data_criacao = dev.get("created_at", "")[:10]
                    data_fmt = datetime.strptime(data_criacao, "%Y-%m-%d").strftime("%d/%m/%Y") if data_criacao else "N/A"
                    
                    with st.expander(f"📦 PDV: {pdv_val} | {fantasia} | Tipo: {tipo} | Data: {data_fmt}"):
                        st.markdown(f"**Consultor:** {consultor_nome} | **Setor:** {dev.get('setor', '—')} | **Modelo:** {dev.get('modelo', '—')} (Qtd: {dev.get('qtd', 1)})")
                        st.markdown(f"**Motivo:** {dev.get('motivo', '—')} | **Cliente:** {dev.get('cliente', '—')}")
                        st.markdown(f"**PAC:** {dev.get('cod_pac', 'Não aplicável')} | **Rastreio:** {dev.get('cod_rastreio', 'Não aplicável')}")

                # Controles de Paginação (Botões Anterior e Próxima)
                st.write("")
                col_ant, col_info, col_prox = st.columns([1, 2, 1])
                
                total_paginas = (total_registros - 1) // 10 + 1

                with col_ant:
                    if st.session_state["dev_pagina"] > 0:
                        if st.button("⬅️ Página Anterior", use_container_width=True):
                            st.session_state["dev_pagina"] -= 1
                            # Recarrega a busca com a página anterior
                            pdv_limpo = re.sub(r"\D", "", val_pdv) if modo_filtro == "Por PDV" else ""
                            st.session_state["devs_resultado"] = buscar_devolucoes_paginadas(
                                modo_filtro, pdv_limpo, d_inicio.strftime("%Y-%m-%d"), d_fim.strftime("%Y-%m-%d"), usuario_id, st.session_state["dev_pagina"]
                            )
                            st.rerun()

                with col_info:
                    st.markdown(f"<div style='text-align: center; padding-top: 5px;'>Página <b>{st.session_state['dev_pagina'] + 1}</b> de <b>{total_paginas}</b></div>", unsafe_allow_html=True)

                with col_prox:
                    if (st.session_state["dev_pagina"] + 1) * 10 < total_registros:
                        if st.button("Próxima Página ➡️", use_container_width=True):
                            st.session_state["dev_pagina"] += 1
                            # Recarrega a busca com a próxima página
                            pdv_limpo = re.sub(r"\D", "", val_pdv) if modo_filtro == "Por PDV" else ""
                            st.session_state["devs_resultado"] = buscar_devolucoes_paginadas(
                                modo_filtro, pdv_limpo, d_inicio.strftime("%Y-%m-%d"), d_fim.strftime("%Y-%m-%d"), usuario_id, st.session_state["dev_pagina"]
                            )
                            st.rerun()
