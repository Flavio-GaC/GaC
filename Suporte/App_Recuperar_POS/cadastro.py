import streamlit as st
from datetime import datetime, timedelta

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
@st.dialog("📋 Texto Gerado para o Cliente")
def popup_copiar_texto(texto):
    st.markdown("Clique no **ícone de sobreposição no canto superior direito** da caixa abaixo para copiar o texto inteiro:")
    st.code(texto, language="text")

# --- FUNÇÃO PRINCIPAL DE CADASTRO ---
def mostrar_cadastro(supabase):
    st.subheader("Registrar Nova Devolução")
    st.markdown("##### ⚠️ Atenção aos tipos de devolução")
    st.info("""COLETA: Os Correios vão até o endereço do lojista para recuperar a máquina.\n
PAC: O lojista deve ir até uma agência dos Correios para devolver a máquina.""")
    
    tipo_devolucao = st.selectbox("Tipo de Devolução *", ["", "PAC", "COLETA"])
    
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
                
                # 1. Salva no banco
                supabase.table("devolucoes").insert(dados).execute()
                st.success("Devolução registrada com sucesso!")

                # 2. Gera os dados para o texto
                data_atual = datetime.now()
                data_atual_str = data_atual.strftime("%d/%m/%Y")
                valor_total = qtd * float(valor_reais)
                texto_final = ""

                # 3. Monta o texto com base no tipo
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
{pdv} | {dados_pdv.get('fantasia', 'N/A')}
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

                # 4. Chama a pop-up central na tela
                popup_copiar_texto(texto_final)
                
            except Exception as e:
                st.error(f"Erro ao registrar: {e}")
