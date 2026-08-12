import streamlit as st

def mostrar_cadastro(supabase):
    st.subheader("Registrar Nova Devolução")
    
    # 1. Movido para FORA do form para a tela atualizar na hora
    tipo_devolucao = st.selectbox("Tipo de Devolução *", ["", "PAC", "COLETA"])
    
    # 2. Lógica dinâmica das opções e bloqueios
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
        # Padrão caso não tenha escolhido ainda
        opcoes_motivo = ["", "DEVOLUÇÃO DE POS", "COLETA DE POS", "DEVOLUÇÃO ACESSORIOS", "COLETA DE ACESSÓRIO"]

    with st.form("form_nova_devolucao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            pdv = st.text_input("Código do PDV *", help="Obrigatório. Deve existir na tabela PDV.")
            modelo = st.selectbox("Modelo da Máquina", ["", "S920", "P2 A11", "D195", "Q92X"])
            qtd = st.number_input("Quantidade", min_value=1, step=1)
            valor_reais = st.number_input("Valor (R$)", value=1050.0 if modelo != "D195" else 500.0, format="%.2f")

        with col2:
            setor = st.selectbox("Setor", ["", "RECUPERAÇÃO", "SUPORTE"])
            motivo = st.selectbox("Motivo da Devolução", opcoes_motivo)
            
            # 3. Aplicando os bloqueios dinâmicos nos campos
            cod_pac = st.text_input("Código PAC", disabled=bloquear_pac)
            cod_rastreio = st.text_input("Código de Rastreio", disabled=bloquear_rastreio)
            
        st.caption("Os campos de Data/Hora e Criado Por serão preenchidos automaticamente pelo sistema.")
        submit = st.form_submit_button("Registrar Devolução", type="primary")

        if submit:
            if not tipo_devolucao:
                st.error("Selecione o Tipo de Devolução antes de registrar.")
            elif not pdv:
                st.error("O campo Código do PDV é obrigatório.")
            elif motivo not in opcoes_motivo:
                st.error("Conflito: O Motivo selecionado não corresponde ao Tipo de Devolução. Selecione o motivo novamente.")
            else:
                try:
                    resposta_pdv = supabase.table("pdv").select("contato, fantasia, endereco, cidade, uf, cep").eq("pdv", pdv).execute()
                    if not resposta_pdv.data:
                        st.error("PDV não encontrado no banco de dados.")
                        st.stop()
                    dados_pdv = resposta_pdv.data[0]

                    uid = st.session_state.get("uid")
                    resposta_usuario = supabase.table("usuarios").select("nome_completo").eq("id", uid).execute()
                    nome_consultor = resposta_usuario.data[0]["nome_completo"] if resposta_usuario.data else None
                    
                    usuario_auth = supabase.auth.get_user()
                    email_usuario = usuario_auth.user.email if usuario_auth else None

                    pac_final = None if (bloquear_pac or not cod_pac) else cod_pac
                    rastreio_final = None if (bloquear_rastreio or not cod_rastreio) else cod_rastreio

                    dados = {
                        "pdv": pdv,
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
                    
                    supabase.table("devolucoes").insert(dados).execute()
                    st.success("Devolução registrada com sucesso!")
                    
                except Exception as e:
                    st.error(f"Erro ao registrar: {e}")
