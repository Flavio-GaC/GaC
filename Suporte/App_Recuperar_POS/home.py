import streamlit as st
import pandas as pd

def mostrar_home(supabase):
    st.title("Página Inicial - Dashboard de Devoluções")
    
    # Busca o nome do usuário logado para saudação
    uid = st.session_state.get("uid")
    try:
        resposta_usuario = supabase.table("usuarios").select("nome_completo").eq("id", uid).execute()
        if resposta_usuario.data:
            nome = resposta_usuario.data[0]["nome_completo"]
            st.write(f"Bem-vindo(a), **{nome}**!")
    except Exception as e:
        st.error("Erro ao identificar o usuário.")

    st.write("---")
    st.subheader("Consultar Devoluções")

    # Filtros para evitar carregar 100 mil linhas de uma vez
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_pdv = st.text_input("Filtrar por PDV (opcional)")
    with col2:
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "PAC", "COLETA"])
    with col3:
        limite = st.selectbox("Limite de registros (mais recentes)", [100, 500, 1000, 5000])

    if st.button("Buscar Dados", type="primary"):
        with st.spinner("Buscando dados no Supabase..."):
            try:
                # Inicia a query ordenando pelos mais recentes
                query = supabase.table("devolucoes").select("*").order("data_hora", desc=True).limit(limite)
                
                # Aplica os filtros se o usuário tiver preenchido
                if filtro_pdv:
                    query = query.eq("pdv", filtro_pdv)
                if filtro_tipo != "Todos":
                    query = query.eq("tipo_devolucao", filtro_tipo)
                    
                resposta = query.execute()
                dados = resposta.data
                
                if dados:
                    # Converte para DataFrame do Pandas para exibir a tabela bonitinha
                    df = pd.DataFrame(dados)
                    
                    # Oculta colunas de IDs que não importam para o usuário final
                    colunas_ocultas = ["id", "criado_por"]
                    df = df.drop(columns=[col for col in colunas_ocultas if col in df.columns], errors='ignore')
                    
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"Exibindo {len(dados)} registro(s).")
                else:
                    st.warning("Nenhum registro encontrado com os filtros atuais.")
                    
            except Exception as e:
                st.error(f"Erro ao buscar dados: {e}")
