import streamlit as st

def checar_notificacoes(supabase, uid, setor_usuario):
    # Garante que o setor seja tratado como texto maiúsculo
    setor_usuario = str(setor_usuario).strip().upper()

    # ==========================================
    # NOTIFICAÇÕES PARA O SETOR COMERCIAL
    # ==========================================
    if setor_usuario == "COMERCIAL":
        # 1. Checar Novo Lead (Apenas os que foram enviados para ele)
        try:
            resp_lead = supabase.table("leads").select("id, nome_empresa").eq("id_especialista", uid).eq("fase_atual", 2).order("updated_at", desc=True).limit(1).execute()
            if resp_lead.data:
                id_novo_lead = resp_lead.data[0]["id"]
                nome_empresa = resp_lead.data[0].get("nome_empresa", "Novo Lojista")

                if "ultimo_lead_comercial" not in st.session_state:
                    st.session_state["ultimo_lead_comercial"] = id_novo_lead
                elif st.session_state["ultimo_lead_comercial"] != id_novo_lead:
                    st.toast(f"**Novo Lead na fila:** {nome_empresa}", icon="🎯")
                    st.session_state["ultimo_lead_comercial"] = id_novo_lead
        except Exception:
            pass

        # 2. Checar Novo Meet (Agendados para ele)
        try:
            resp_meet = supabase.table("meets").select("meet_id, nome_lojista").eq("usuario_id", uid).order("created_at", desc=True).limit(1).execute()
            if resp_meet.data:
                id_novo_meet = resp_meet.data[0]["meet_id"]
                lojista_meet = resp_meet.data[0].get("nome_lojista", "Lojista")

                if "ultimo_meet_comercial" not in st.session_state:
                    st.session_state["ultimo_meet_comercial"] = id_novo_meet
                elif st.session_state["ultimo_meet_comercial"] != id_novo_meet:
                    st.toast(f"**Novo Meet agendado:** {lojista_meet}", icon="📅")
                    st.session_state["ultimo_meet_comercial"] = id_novo_meet
        except Exception:
            pass

    # ==========================================
    # NOTIFICAÇÕES PARA O SETOR BACKOFFICE (BKO)
    # ==========================================
    elif setor_usuario == "BACKOFFICE":
        try:
            # Busca o último lead que entrou na Fase 3 (fila geral do BKO)
            resp_bko = supabase.table("leads").select("id, nome_empresa").eq("fase_atual", 3).order("updated_at", desc=True).limit(1).execute()
            if resp_bko.data:
                id_novo_bko = resp_bko.data[0]["id"]
                nome_empresa_bko = resp_bko.data[0].get("nome_empresa", "Novo Lojista")

                if "ultimo_lead_bko" not in st.session_state:
                    st.session_state["ultimo_lead_bko"] = id_novo_bko
                elif st.session_state["ultimo_lead_bko"] != id_novo_bko:
                    st.toast(f"**Novo Contrato para Auditoria:** {nome_empresa_bko}", icon="📑")
                    st.session_state["ultimo_lead_bko"] = id_novo_bko
        except Exception:
            pass
