import streamlit as st
import re
from themes.theme import cabecalho_pagina, titulo_secao

def mostrar_lojistas(supabase):
    cabecalho_pagina("Consulta de Lojistas", "Pesquise rapidamente os dados cadastrais por PDV ou CNPJ.")

    # Função com cache do Streamlit para economizar requisições ao banco
    @st.cache_data(show_spinner=False, ttl=3600)
    def buscar_dados_lojista(tipo_busca, valor_limpo):
        try:
            # Seleciona a coluna correta da tabela 'pdv' com base no tipo de busca
            coluna = "pdv" if tipo_busca == "PDV" else "cnpj"
            
            # Executa a query baseada na sua estrutura SQL informada
            resp = supabase.table("pdv").select(
                "fantasia, razao, contato, telefone0, telefone1, email, cnpj, pdv, "
                "endereco, complemento, bairro, cidade, uf, cep, "
                "data_contrato, ramo_atividade, agente_bcard, agente_bolt"
            ).eq(coluna, valor_limpo).execute()
            
            return resp.data if resp.data else []
        except Exception as e:
            return f"erro: {e}"

    # Interface de Busca
    c_tipo, c_valor, c_btn = st.columns([2, 3, 1])
    
    with c_tipo:
        tipo_pesquisa = st.selectbox("Buscar por", ["PDV", "CNPJ"])
    
    with c_valor:
        if tipo_pesquisa == "PDV":
            valor_input = st.text_input("Digite o PDV", max_chars=10, placeholder="Apenas números (máx. 10)")
        else:
            valor_input = st.text_input("Digite o CNPJ", max_chars=18, placeholder="Somente números ou formatado")
            
    with c_btn:
        st.write("")
        st.write("")
        btn_pesquisar = st.button("Pesquisar", type="primary", use_container_width=True)

    if btn_pesquisar or "lojista_resultado" in st.session_state:
        if btn_pesquisar:
            valor_limpo = re.sub(r"\D", "", valor_input)
            cnpj_formatado = re.sub(
                                    r"(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})",
                                    r"\1.\2.\3/\4-\5",
                                    valor_limpo
                                    )
            
            if not cnpj_formatado:
                st.warning(f"Digite um {tipo_pesquisa} válido para pesquisar.")
            else:
                with st.spinner("Buscando lojista..."):
                    resultado = buscar_dados_lojista(tipo_pesquisa, cnpj_formatado)
                    st.session_state["lojista_resultado"] = resultado
                    st.session_state["lojista_busca_info"] = (tipo_pesquisa, cnpj_formatado)

        dados_lojista = st.session_state.get("lojista_resultado", [])

        if isinstance(dados_lojista, str) and dados_lojista.startswith("erro:"):
            st.error(f"Erro ao consultar o banco de dados: {dados_lojista}")
        elif not dados_lojista:
            st.info("Nenhum lojista encontrado com este identificador.")
        else:
            # Exibe os dados do lojista encontrado de forma organizada
            lojista = dados_lojista[0]
            
            st.write("---")
            titulo_secao(f"🏢 {lojista.get('fantasia') or 'Lojista Sem Nome Fantasia'}")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"**Razão Social:** {lojista.get('razao', '—')}")
                st.markdown(f"**CNPJ:** {lojista.get('cnpj', '—')}")
                st.markdown(f"**PDV:** {lojista.get('pdv', '—')}")
                st.markdown(f"**Ramo de Atividade:** {lojista.get('ramo_atividade', '—')}")
                st.markdown(f"**Data do Contrato:** {lojista.get('data_contrato', '—')}")
                
                # Montagem limpa do endereço concatenado
                end_partes = [
                    lojista.get('endereco'),
                    lojista.get('complemento'),
                    lojista.get('bairro'),
                    lojista.get('cidade'),
                    f"{lojista.get('uf', '')} - {lojista.get('cep', '')}"
                ]
                endereco_completo = ", ".join([str(p) for p in end_partes if p])
                st.markdown(f"**Endereço:** {endereco_completo if endereco_completo else '—'}")

            with col_b:
                st.markdown(f"**Contato Responsável:** {lojista.get('contato', '—')}")
                st.markdown(f"**Telefone Principal:** {lojista.get('telefone0', '—')}")
                st.markdown(f"**Telefone Secundário:** {lojista.get('telefone1', '—')}")
                st.markdown(f"**E-mail:** {lojista.get('email', '—')}")
                st.markdown(f"**Agente BCard:** {lojista.get('agente_bcard', '—')}")
                st.markdown(f"**Agente Bolt:** {lojista.get('agente_bolt', '—')}")
