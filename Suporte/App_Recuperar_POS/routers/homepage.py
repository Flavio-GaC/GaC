import streamlit as st
from themes.theme import tema_home

def mostrar_home(supabase):
    tema_home()

    html_conteudo = """
    <section class="home-wrapper">
      <div class="home-header">
        <h2 class="home-h2">A força de um Grupo que traz credibilidade e segurança.</h2>
        <p class="home-p">O Grupo Adriano Cobuccio expandiu seus negócios nos últimos anos e se solidificou através da diversidade de suas atividades econômicas. O grande leque de atuação do grupo é uma retaguarda comercial e financeira que amplia ainda mais seu mercado. A estratégia é manter sempre essa diversidade, buscando o máximo de eficiência em cada segmento.</p>
        <h3 class="home-h3">Diversidade de atividades para atuar e buscar recursos.</h3>
        <p class="home-sub-p">O Grupo Adriano Cobuccio possui 30 empresas estabelecidas nos três setores de nossa economia:<br><b>produção natural</b>, <b>serviços</b> e <b>produção industrial</b>.</p>
      </div>
      <div class="home-grid-container">
        <div class="home-grid">
          <div class="home-card"><h5>BrasilCard</h5></div>
          <div class="home-card"><h5>Bolt</h5></div>
          <div class="home-card"><h5>BrasilCred</h5></div>
          <div class="home-card"><h5>Cobuccio Usinas Hidrelétricas</h5></div>
          <div class="home-card"><h5>Rede de Postos BrasilPetro</h5></div>
          <div class="home-card"><h5>Brasil Commodities Agrícola</h5></div>
          <div class="home-card"><h5>Produção de Commodities Agrícolas</h5></div>
          <div class="home-card"><h5>Cobuccio Empreendimentos Imobiliários</h5></div>
          <div class="home-card"><h5>Guardian Plano Assistencial</h5></div>
          <div class="home-card"><h5>Cobuccio Locação e Serviços</h5></div>
          <div class="home-card"><h5>Cobuccio Fundo de Investimentos</h5></div>
          <div class="home-card"><h5>Cobuccio Securitizadora de Crédito</h5></div>
          <div class="home-card"><h5>Ágil Empréstimos</h5></div>
          <div class="home-card"><h5>Cobuccio Tecnologia</h5></div>
          <div class="home-card"><h5>Cobuccio Fundo de Investimento Multimercado</h5></div>
          <div class="home-card"><h5>Mineração Rio Pardo</h5></div>
        </div>
      </div>
    </section>
    """
    
    st.markdown(html_conteudo, unsafe_allow_html=True)
