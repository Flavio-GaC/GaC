import html as _html
import streamlit as st



LOGO_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSk-QaUmTV7hcYg5cDpuEUoLCfscN-OVuiCZcJukputzg&s=10ttps://i.imgur.com/eG4PhxC.png"


def aplicar_tema():
    """Injeta a identidade visual global com suporte a modo claro/escuro."""
    tema_atual = st.session_state.get("tema", "dark")

    if tema_atual == "dark":
        PRIMARIA = "#0B5FFF"
        PRIMARIA_ESCURA = "#0846C4"
        TEXTO = "#F8FAFC"
        TEXTO_SUAVE = "#94A3B8"
        BORDA = "#1E293B"
        FUNDO = "#0B1220"
        SUPERFICIE = "#111C2E"
        RAIO = "12px"
        SOMBRA = "0 4px 6px -1px rgba(0,0,0,0.5), 0 2px 4px -1px rgba(0,0,0,0.3)"
        INK_LABEL = "#F8FAFC" 
    else:
        PRIMARIA = "#0B5FFF"
        PRIMARIA_ESCURA = "#0846C4"
        TEXTO = "#0F172A"
        TEXTO_SUAVE = "#64748B"
        BORDA = "#E2E8F0"
        FUNDO = "#F6F8FB"
        SUPERFICIE = "#FFFFFF"
        RAIO = "12px"
        SOMBRA = "0 1px 2px rgba(16,24,40,.05), 0 8px 24px -12px rgba(16,24,40,.18)"
        INK_LABEL = "#334155" 

    st.markdown(
        f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {{
  --brand: {PRIMARIA};
  --brand-dark: {PRIMARIA_ESCURA};
  --ink: {TEXTO};
  --ink-soft: {TEXTO_SUAVE};
  --line: {BORDA};
  --bg: {FUNDO};
  --surface: {SUPERFICIE};
  --radius: {RAIO};
  --shadow: {SOMBRA};
  --ink-label: {INK_LABEL};
}}

/* Oculta o cabeçalho superior e rodapé nativo */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stAppDeployButton"], footer {{
    display: none !important;
}}

html, body, [class*="css"], .stApp {{
  font-family: 'Inter', -apple-system, "Segoe UI", sans-serif;
}}

.stApp {{ background: var(--bg); color: var(--ink); }}

.block-container {{
  padding-top: 2rem;
  padding-bottom: 3rem;
  max-width: 1280px;
}}

h1, h2, h3, h4 {{ color: var(--ink); letter-spacing: -.02em; font-weight: 700; }}
h1 {{ font-size: 1.9rem !important; }}
h2 {{ font-size: 1.4rem !important; }}
h3 {{ font-size: 1.15rem !important; }}

/* SIDEBAR MANTÉM ESCURA */
[data-testid="stSidebar"] {{
  background: #0B1220;
  border-right: 1px solid rgba(255,255,255,.06);
}}
[data-testid="stSidebar"] * {{ color: #E2E8F0; }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: #FFFFFF; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.10); }}

/* MENU MODERNO */
[data-testid="stSidebar"] [role="radiogroup"] {{ gap: .25rem; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
  display: flex; align-items: center; padding: .6rem .75rem;
  border-radius: 10px; border: 1px solid transparent;
  transition: background .15s ease, border-color .15s ease; cursor: pointer;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: rgba(255,255,255,.06); }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background: rgba(11,95,255,.18); border-color: rgba(11,95,255,.55); font-weight: 600;
}}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{ display: none; }}

.sb-brand {{ text-align:center; padding: .25rem 0 1rem; }}
.sb-user {{
  display:flex; align-items:center; gap:.65rem; background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.08); border-radius: 10px; padding: .7rem .8rem; margin-top:.25rem;
}}
.sb-avatar {{
  width:34px; height:34px; min-width:34px; border-radius:50%; background: var(--brand); color:#fff !important;
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:.85rem;
}}
.sb-user small {{ color:#94A3B8 !important; display:block; line-height:1.1; }}
.sb-user strong {{ font-size:.88rem; line-height:1.25; }}

/* BOTÕES */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
  border-radius: 10px; font-weight: 600; padding: .55rem 1.1rem; border: 1px solid var(--line);
  background: var(--surface); color: var(--ink); transition: all .15s ease; box-shadow: none;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
  border-color: #CBD5E1; background: #F8FAFC; color: #0F172A;
}}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
  background: var(--brand); border-color: var(--brand); color: #fff; box-shadow: 0 6px 16px -8px rgba(11,95,255,.8);
}}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {{
  background: var(--brand-dark); border-color: var(--brand-dark); color:#fff;
}}

/* CAMPOS DINÂMICOS */
label, .stTextInput label, .stSelectbox label, .stNumberInput label, .stDateInput label, .stTimeInput label, .stTextArea label {{
  font-weight: 600 !important; font-size: .84rem !important; color: var(--ink-label) !important;
}}
.stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, .stTextArea textarea {{
  border-radius: 10px !important; border: 1px solid var(--line) !important;
  padding: .55rem .75rem !important; background: var(--surface) !important; color: var(--ink) !important;
}}

/* Ajuste fino para os Selectboxes (caixas de seleção) */
[data-baseweb="select"] > div {{
  border-radius: 10px !important; border: 1px solid var(--line) !important; 
  background-color: var(--surface) !important;
}}
[data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] svg {{
  color: var(--ink) !important; background-color: transparent !important;
}}

/* Menu suspenso do Selectbox */
[data-baseweb="popover"] > div {{
  background-color: var(--surface) !important; border: 1px solid var(--line) !important;
}}
[data-baseweb="menu"] li {{
  color: var(--ink) !important; background-color: transparent !important;
}}
[data-baseweb="menu"] li:hover {{
  background-color: rgba(11, 95, 255, 0.1) !important;
}}

/* Foco */
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus, [data-baseweb="select"] > div:focus-within {{
  border-color: var(--brand) !important; box-shadow: 0 0 0 3px rgba(11,95,255,.15) !important;
}}
[data-testid="stForm"] {{
  background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
  padding: 1.4rem 1.4rem .6rem; box-shadow: var(--shadow);
}}

/* CONTAINERS / ALERTAS / COMPONENTES / TIMELINE (Mantidos iguais) */
[data-testid="stVerticalBlockBorderWrapper"] {{ background: var(--surface); border-radius: 14px !important; border-color: var(--line) !important; box-shadow: var(--shadow); }}
[data-testid="stAlert"] {{ border-radius: 12px; border: 1px solid var(--line); }}
.page-head {{ display:flex; flex-wrap:wrap; gap:.75rem 1rem; align-items:flex-start; justify-content:space-between; margin-bottom: 1.2rem; }}
.page-head h1 {{ margin:0 0 .2rem 0; }}
.page-head p {{ margin:0; color: var(--ink-soft); font-size:.92rem; }}
.kpi {{ background: var(--surface); border:1px solid var(--line); border-radius: 14px; padding: 1rem 1.1rem; box-shadow: var(--shadow); height: 100%; }}
.kpi .kpi-label {{ font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; color: var(--ink-soft); font-weight:700; margin-bottom:.35rem; }}
.kpi .kpi-value {{ font-size:1.6rem; font-weight:800; line-height:1.1; }}
.badge {{ display:inline-block; padding:.2rem .6rem; border-radius:999px; font-size:.72rem; font-weight:700; letter-spacing:.03em; border:1px solid transparent; white-space:nowrap; }}
.badge-pac {{ background:#EFF6FF; color:#1D4ED8; border-color:#BFDBFE; }}
.badge-coleta {{ background:#F0FDF4; color:#15803D; border-color:#BBF7D0; }}
.badge-neutro {{ background:#F1F5F9; color:#475569; border-color:#E2E8F0; }}
.rec-head {{ display:flex; flex-wrap:wrap; align-items:center; gap:.6rem; justify-content:space-between; margin-bottom:.6rem; padding-bottom:.6rem; border-bottom:1px solid var(--line); }}
.rec-title {{ font-weight:700; font-size:1.02rem; min-width:0; }}
.rec-title span {{ color: var(--ink-soft); font-weight:500; }}
.field {{ margin-bottom:.45rem; font-size:.88rem; }}
.field .k {{ display:block; font-size:.7rem; text-transform:uppercase; letter-spacing:.05em; color: var(--ink-soft); font-weight:700; }}
.field .v {{ color: var(--ink); word-break: break-word; }}
.mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #1E293B; border: 1px solid var(--line); padding: .05rem .35rem; border-radius: 6px; font-size: .82rem; color: #F8FAFC; }}
.empty {{ text-align:center; padding:2.5rem 1rem; background:var(--surface); border:1px dashed #CBD5E1; border-radius:14px; }}
.empty .icon {{ font-size:2rem; }}
.empty h4 {{ margin:.5rem 0 .25rem; }}
.empty p {{ color:var(--ink-soft); margin:0; font-size:.9rem; }}
.section-title {{ font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:var(--ink-soft); font-weight:800; margin:.2rem 0 .6rem; }}

/* RODAPÉ */
.custom-footer {{ margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid var(--line); text-align: center; font-size: 13px; color: var(--ink-soft); }}
.custom-footer a {{ color: var(--ink-soft); text-decoration: underline; text-decoration-color: rgba(148, 163, 184, 0.3); transition: color 0.2s ease; }}
.custom-footer a:hover {{ color: var(--ink); }}

/* TIMELINE DO HISTÓRICO */
.timeline-container {{ position: relative; padding-left: 2rem; margin-bottom: 1.5rem; }}
.timeline-container::before {{ content: ''; position: absolute; left: 7px; top: 0; bottom: -1.5rem; width: 2px; background-color: var(--line); }}
.timeline-container:last-child::before {{ display: none; }}
.timeline-dot {{ position: absolute; left: 0; top: 5px; width: 16px; height: 16px; border-radius: 50%; background-color: var(--surface); border: 3px solid var(--brand); z-index: 1; }}
.timeline-content {{ background-color: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 1.2rem; box-shadow: var(--shadow); }}
.tl-header {{ display: flex; justify-content: space-between; margin-bottom: 0.8rem; align-items: center; }}
.tl-date {{ color: var(--ink-soft); font-size: 0.85rem; font-weight: 600; }}
.tl-status {{ font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 6px; border: 1px solid var(--line); background-color: rgba(255,255,255, 0.05); }}
.tl-grid {{ display: grid; grid-template-columns: 1fr; gap: 0.5rem; margin-bottom: 0.8rem; font-size: 0.9rem; }}
.tl-label {{ color: var(--ink-soft); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
.tl-value {{ font-weight: 600; color: var(--ink); }}
.tl-obs {{ background-color: var(--bg); padding: 0.8rem; border-radius: 6px; font-style: italic; font-size: 0.85rem; color: var(--ink-soft); border-left: 3px solid var(--line); }}

/* RESPONSIVO */
@media (max-width: 640px) {{
  .block-container {{ padding-left: 1rem; padding-right: 1rem; padding-top: 1rem; }}
  h1 {{ font-size: 1.5rem !important; }}
  .kpi .kpi-value {{ font-size:1.3rem; }}
  [data-testid="stForm"] {{ padding: 1rem 1rem .4rem; }}
  [data-testid="column"] {{ min-width: 100% !important; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )

# --- HELPERS DE UI ------------------------------------------------------
def _e(valor):
    return _html.escape(str(valor if valor not in (None, "") else "N/A"))


def cabecalho_pagina(titulo, subtitulo=""):
    st.markdown(
        f"""<div class="page-head"><div>
        <h1>{_e(titulo)}</h1>
        {f'<p>{_e(subtitulo)}</p>' if subtitulo else ''}
        </div></div>""",
        unsafe_allow_html=True,
    )


def kpi(label, valor, dica=""):
    st.markdown(
        f"""<div class="kpi">
          <div class="kpi-label">{_e(label)}</div>
          <div class="kpi-value">{_e(valor)}</div>
          {f'<div class="kpi-hint">{_e(dica)}</div>' if dica else ''}
        </div>""",
        unsafe_allow_html=True,
    )


def badge(texto):
    t = (texto or "").upper()
    classe = "badge-pac" if t == "PAC" else "badge-coleta" if t == "COLETA" else "badge-neutro"
    return f'<span class="badge {classe}">{_e(texto or "—")}</span>'


def campo(rotulo, valor, mono=False):
    v = _e(valor)
    if mono:
        v = f'<span class="mono">{v}</span>'
    st.markdown(
        f'<div class="field"><span class="k">{_e(rotulo)}</span>'
        f'<span class="v">{v}</span></div>',
        unsafe_allow_html=True,
    )


def estado_vazio(titulo, descricao, icone="🗂️"):
    st.markdown(
        f"""<div class="empty">
          <div class="icon">{icone}</div>
          <h4>{_e(titulo)}</h4>
          <p>{_e(descricao)}</p>
        </div>""",
        unsafe_allow_html=True,
    )


def titulo_secao(texto):
    st.markdown(f'<div class="section-title">{_e(texto)}</div>', unsafe_allow_html=True)


def rodape():
    st.markdown(
        """
        <div class="custom-footer">
            © 2026 Grupo Adriano Cobuccio. Todos os direitos reservados. <br>
            Desenvolvido por <a href="https://linktr.ee/flaviodavi" target="_blank">Flávio Davi</a>
        </div>
        """,
        unsafe_allow_html=True
    )
