import streamlit as st
import pandas as pd
from datetime import datetime

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

def mostrar_home(supabase):
    st.title("Dashboard de Devoluções")
    
    uid = st.session_state.get("uid")
    try:
        resposta_usuario = supabase.table("usuarios").select("nome_completo").eq("id", uid).execute()
        if resposta_usuario.data:
            st.write(f"Bem-vindo(a), **{resposta_usuario.data[0]['nome_completo']}**!")
    except Exception:
        pass

    st.write("---")
    
    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_pdv = st.text_input("Buscar por PDV (opcional)")
    with col_f2:
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "PAC", "COLETA"])
    with col_f3:
        limite = st.selectbox("Quantidade de registros", [50, 100, 500])

    if st.button("Buscar Dados", type="primary"):
        with st.spinner("Buscando dados no Supabase..."):
            try:
                query = supabase.table("devolucoes").select("*").order("data_hora", desc=True).limit(limite)
                
                if filtro_pdv:
                    query = query.eq("pdv", filtro_pdv)
                if filtro_tipo != "Todos":
                    query = query.eq("tipo_devolucao", filtro_tipo)
                    
                resposta = query.execute()
                dados = resposta.data
                
                if dados:
                    st.success(f"{len(dados)} registro(s) encontrado(s).")
                    
                    # Desenha um quadro (card) para cada registro
                    for linha in dados:
                        with st.container(border=True):
                            # Cabeçalho do Card
                            st.subheader(f"🏢 PDV: {linha.get('pdv', 'N/A')} - {linha.get('nome_fantasia', 'N/A')}")
                            
                            # Divide as informações em 3 colunas dentro do quadro
                            c1, c2, c3 = st.columns(3)
                            
                            with c1:
                                st.markdown(f"**📅 Data/Hora:** {formatar_data(linha.get('data_hora'))}")
                                st.markdown(f"**🔄 Tipo:** {linha.get('tipo_devolucao', 'N/A')}")
                                st.markdown(f"**⚠️ Motivo:** {linha.get('motivo', 'N/A')}")
                                st.markdown(f"**👤 Consultor:** {linha.get('consultor', 'N/A')}")
                                st.markdown(f"**🏢 Setor:** {linha.get('setor', 'N/A')}")
                                st.markdown(f"**📧 Registrado por:** {linha.get('email', 'N/A')}")
                            
                            with c2:
                                qtd = linha.get('qtd') or 0
                                valor_unitario = linha.get('valor_reais') or 0
                                valor_total = qtd * float(valor_unitario)
                                
                                st.markdown(f"**💻 Modelo:** {linha.get('modelo', 'N/A')}")
                                st.markdown(f"**📦 Qtd:** {qtd}")
                                
                                # Formatação de moeda estilo BR
                                valor_formatado = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                st.markdown(f"**💰 Valor Total:** {valor_formatado}")
                                
                                # Exibição condicional de PAC / Rastreio
                                tipo = linha.get('tipo_devolucao')
                                if tipo == "PAC" and linha.get("cod_pac"):
                                    st.markdown(f"**📮 Cód. PAC:** `{linha.get('cod_pac')}`")
                                elif tipo == "COLETA" and linha.get("cod_rastreio"):
                                    st.markdown(f"**🚚 Cód. Rastreio:** `{linha.get('cod_rastreio')}`")
                                    
                            with c3:
                                st.markdown(f"**🤝 Cliente:** {linha.get('cliente', 'N/A')}")
                                st.markdown(f"**📍 Endereço:** {linha.get('endereco', 'N/A')}")
                                st.markdown(f"**🏙️ Cidade/UF:** {linha.get('cidade', 'N/A')} - {linha.get('uf', 'N/A')}")
                                st.markdown(f"**📮 CEP:** {linha.get('cep', 'N/A')}")
                                
                else:
                    st.warning("Nenhum registro encontrado com os parâmetros atuais.")
                    
            except Exception as e:
                st.error(f"Erro ao exibir dados: {e}")
