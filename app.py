import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

# 1. PARAMÉTRAGE STREAMLIT MOBILE PORTRAIT
st.set_page_config(page_title="Tennis Dataland Pro", layout="centered", page_icon="🎾")

# 2. DEFINITION PRIORITAIRE DES NOMS DANS LA BARRE LATÉRALE
st.sidebar.header("⚙️ Paramètres")
player_a = st.sidebar.text_input("Joueur A", value="Joueur A")
rank_a = st.sidebar.text_input("Classement A", value="N/C")
st.sidebar.markdown("---")
player_b = st.sidebar.text_input("Joueur B", value="Joueur B")
rank_b = st.sidebar.text_input("Classement B", value="N/C")
st.sidebar.markdown("---")
match_date = st.sidebar.date_input("Date match", datetime.now())

# 3. STOCKAGE SESSIONS PERSISTANT SANS PERTE
if 'all_match_summaries' not in st.session_state: st.session_state.all_match_summaries = []
if 'all_points_logs' not in st.session_state: st.session_state.all_points_logs = []
if 'match_data' not in st.session_state: st.session_state.match_data = []
if 'score' not in st.session_state:
    st.session_state.score = {
        "pA_points": 0, "pB_points": 0, "pA_jeux": 0, "pB_jeux": 0, "pA_sets": 0, "pB_sets": 0,
        "sets_history_A": [], "sets_history_B": [], "in_tiebreak": False, "in_supertb": False,
        "serveur_actuel": player_a, "pts_servis_tb": 0, "abandon_player": None
    }
if 'score_history' not in st.session_state: st.session_state.score_history = []
if 'service_history' not in st.session_state: st.session_state.service_history = []
if 'service_state' not in st.session_state: st.session_state.service_state = "1ère Balle"
if 'pending_event' not in st.session_state: st.session_state.pending_event = None

# 4. LE CSS INVIOLABLE QUI FORCE LE BLOCAGE DE L'EN-TÊTE ET LE CÔTE À CÔTE À DEUX POUCES
st.markdown("""
<style>
    .stApp { background-color: #b14d2a !important; }
    .sticky-score-wrapper {
        position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important;
        background-color: #0b110b !important; z-index: 99999 !important; padding: 6px !important;
        margin: 0 !important; width: 100vw !important; border-bottom: 2px solid #ffeb3b !important;
    }
    .main-control-spacer { margin-top: 110px !important; }
    .stWidgetForm label, .stMarkdown p, p, h3, h4, .player-label-grid { 
        color: #ffffff !important; font-weight: 900 !important; font-size: 11px !important; text-align: center !important; margin: 2px 0 !important;
    }
    /* FORCE LES COLONNES DU CLAVIER DE JEU À RETER CÔTE À CÔTE (50% / 50%) */
    [data-testid="column"] { width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; padding: 0 3px !important; }
    .btn-srv [data-testid="column"] { width: 33.33% !important; flex: 1 1 33.33% !important; min-width: 33.33% !important; }
    .stButton > button, .stButton > button p, .stButton > button span {
        color: #000000 !important; font-weight: 900 !important; font-size: 10px !important; line-height: 1.1 !important;
        padding: 4px 2px !important; min-height: 38px !important; max-height: 38px !important; width: 100% !important; border-radius: 6px !important;
    }
    div.btn-srv .stButton > button { background-color: #a7f3d0 !important; border: 2px solid #065f46 !important; }
    div.btn-blue .stButton > button { background-color: #bfdbfe !important; border: 2px solid #1e40af !important; }
    div.btn-red .stButton > button { background-color: #fecaca !important; border: 2px solid #991b1b !important; }
    div.btn-undo .stButton > button { background-color: #fef08a !important; border: 2px solid #854d0e !important; min-height: 28px !important; max-height: 28px !important; }
    .score-banner-box { background-color: #0b110b; padding: 5px; border-radius: 6px; border: 1px solid #1e2b1e; text-align: center; }
</style>
""", unsafe_allow_html=True)
if not st.session_state.match_data and st.session_state.score["pA_points"] == 0 and st.session_state.score["pA_jeux"] == 0 and len(st.session_state.score["sets_history_A"]) == 0:
    st.session_state.score["serveur_actuel"] = st.sidebar.selectbox("Serveur tirage :", [player_a, player_b])

app_mode = st.sidebar.radio("📍 Mode Écran :", ["🕹️ Arbitrage en Direct", "📊 Statistiques Saison"])
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reset Match Courant"):
    st.session_state.match_data, st.session_state.score_history, st.session_state.service_history, st.session_state.service_state, st.session_state.pending_event = [], [], [], "1ère Balle", None
    st.session_state.score = {"pA_points": 0, "pB_points": 0, "pA_jeux": 0, "pB_jeux": 0, "pA_sets": 0, "pB_sets": 0, "sets_history_A": [], "sets_history_B": [], "in_tiebreak": False, "in_supertb": False, "serveur_actuel": player_a, "pts_servis_tb": 0, "abandon_player": None}
    st.rerun()

if st.sidebar.button("⚠️ Effacer TOUT l'historique de la saison"):
    st.session_state.all_match_summaries, st.session_state.all_points_logs, st.session_state.service_history, st.session_state.service_state, st.session_state.pending_event = [], [], [], "1ère Balle", None
    st.sidebar.success("Historique global vidé !")
    st.rerun()
def alterner_serveur():
    sc = st.session_state.score
    sc["serveur_actuel"] = player_b if sc["serveur_actuel"] == player_a else player_a

def valider_fin_set(winner_set):
    sc = st.session_state.score
    sc["sets_history_A"].append(sc["pA_jeux"])
    sc["sets_history_B"].append(sc["pB_jeux"])
    if winner_set == player_a: sc["pA_sets"] += 1
    else: sc["pB_sets"] += 1
    sc["pA_jeux"], sc["pB_jeux"], sc["pA_points"], sc["pB_points"], sc["in_tiebreak"], sc["pts_servis_tb"] = 0, 0, 0, 0, False, 0

def update_score(winner):
    sc = st.session_state.score
    st.session_state.score_history.append(sc.copy())
    st.session_state.service_history.append(st.session_state.service_state)
    if winner == player_a: sc["pA_points"] += 1
    else: sc["pB_points"] += 1
    evenement = "Point"
    if sc["in_supertb"]:
        sc["pts_servis_tb"] += 1
        if sc["pts_servis_tb"] % 2 == 1: alterner_serveur()
        if sc["pA_points"] >= 10 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] = sc["pA_points"]; sc["pB_jeux"] = sc["pB_points"]; valider_fin_set(player_a); evenement = "🎉 FIN DE MATCH"
        elif sc["pB_points"] >= 10 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pA_jeux"] = sc["pA_points"]; sc["pB_jeux"] = sc["pB_points"]; valider_fin_set(player_b); evenement = "🎉 FIN DE MATCH"
    elif sc["in_tiebreak"]:
        sc["pts_servis_tb"] += 1
        if sc["pts_servis_tb"] % 2 == 1: alterner_serveur()
        if sc["pA_points"] >= 7 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] = 7; sc["pB_jeux"] = 6; valider_fin_set(player_a); alterner_serveur(); evenement = "🎉 SET"
        elif sc["pB_points"] >= 7 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pA_jeux"] = 6; sc["pB_jeux"] = 7; valider_fin_set(player_b); alterner_serveur(); evenement = "🎉 SET"
    else:
        if sc["pA_points"] >= 4 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] += 1; sc["pA_points"], sc["pB_points"] = 0, 0; alterner_serveur(); evenement = "Jeu"
        elif sc["pB_points"] >= 4 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pB_jeux"] += 1; sc["pA_points"], sc["pB_points"] = 0, 0; alterner_serveur(); evenement = "Jeu"
        if sc["pA_points"] >= 4 and sc["pB_points"] >= 4 and sc["pA_points"] == sc["pB_points"]: sc["pA_points"], sc["pB_points"] = 3, 3
        if sc["pA_jeux"] == 6 and sc["pB_jeux"] == 6: sc["in_tiebreak"] = True; sc["pts_servis_tb"] = 0
        elif sc["pA_jeux"] >= 6 and (sc["pA_jeux"] - sc["pB_jeux"]) >= 2: valider_fin_set(player_a); evenement = "🎉 SET"
        elif sc["pB_jeux"] >= 6 and (sc["pB_jeux"] - sc["pA_jeux"]) >= 2: valider_fin_set(player_b); evenement = "🎉 SET"
    if sc["pA_sets"] == 1 and sc["pB_sets"] == 1 and not sc["in_supertb"]: sc["in_supertb"] = True; sc["pts_servis_tb"] = 0
    return evenement

def get_pts(pa, pb, in_tb, in_stb):
    if in_tb or in_stb: return str(pa), str(pb)
    if pa >= 3 and pb >= 3:
        if pa == pb: return "40", "40"
        return ("Ad", "40") if pa > pb else ("40", "Ad")
    return {0:"0", 1:"15", 2:"30", 3:"40"}.get(pa,"0"), {0:"0", 1:"15", 2:"30", 3:"40"}.get(pb,"0")

def undo_last_point():
    if st.session_state.match_data and st.session_state.score_history:
        st.session_state.match_data.pop()
        st.session_state.score = st.session_state.score_history.pop()
        st.session_state.service_state = st.session_state.service_history.pop()
        st.rerun()
sc = st.session_state.score
pt_a, pt_b = get_pts(sc["pA_points"], sc["pB_points"], sc["in_tiebreak"], sc["in_supertb"])
match_termine = sc["pA_sets"] == 2 or sc["pB_sets"] == 2 or sc["abandon_player"] is not None

# FORMATAGE DES SETS COMPACT (ex: 6/1 6/0) SANS CROCHETS PYTHON
text_score_visuel = ""
for i in range(len(sc["sets_history_A"])): text_score_visuel += f" {sc['sets_history_A'][i]}/{sc['sets_history_B'][i]}"
if not match_termine: text_score_visuel += f" ({sc['pA_jeux']}/{sc['pB_jeux']})"

if not match_termine and len(st.session_state.match_data) > 0:
    st.sidebar.markdown("---")
    if st.sidebar.button(f"Abandon de {player_a}", key="abandon_a"): sc["abandon_player"] = player_a; st.rerun()
    if st.sidebar.button(f"Abandon de {player_b}", key="abandon_b"): sc["abandon_player"] = player_b; st.rerun()

# GENERATION DU MARQUEUR FIGÉ SANS ÉTIQUETTES HTML PARASITES
st.markdown('<div class="sticky-score-wrapper">', unsafe_allow_html=True)
st.markdown(f"""
<div class="score-banner-box">
    <p style='margin:0; font-size:14px; font-family:sans-serif; color:#ffffff;'><b>{player_a[:8]}</b> vs <b>{player_b[:8]}</b> | <span style='color:#ffeb3b;'>{text_score_visuel.strip()}</span></p>
    <p style='margin:1px 0 0 0; font-size:12px; color:#ffeb3b; font-weight:900;'>Score : {pt_a if not match_termine else 'Fin'} - {pt_b if not match_termine else 'Fin'} (Srv : {sc["serveur_actuel"][:8]} 🟡)</p>
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

def queue_event(w, p, t, s="N/A"):
    if t in ["Ace", "Double Faute"]: execute_log(w, p, t, s, "- 4 échanges")
    else: st.session_state.pending_event = {"w": w, "p": p, "t": t, "s": s}; st.rerun()

def execute_log(w, p, t, s, rally_length):
    current_service = st.session_state.service_state; evt_msg = update_score(w)
    st.session_state.match_data.append({
        "Date": match_date.strftime("%d/%m/%Y"), "Match": f"{player_a} vs {player_b}", "Gagnant du point": w,
        "Joueur ayant fait l'action/erreur": p, "Type d'action": t, "Côté du coup": s, "Longueur Échange": rally_length,
        "Serveur du point": sc["serveur_actuel"], "Balle de service": current_service, "Événement Match": evt_msg
    })
    st.session_state.service_state = "1ère Balle"; st.session_state.pending_event = None; st.rerun()
st.markdown('<div class="main-control-spacer"></div>', unsafe_allow_html=True)

if app_mode == "🕹️ Arbitrage en Direct":
    if st.session_state.pending_event is not None:
        pe = st.session_state.pending_event
        st.markdown("<p style='text-align:center; font-size:11px; margin:0;'>Frappes Échange :</p>", unsafe_allow_html=True)
        c_r1, c_r2, c_r3 = st.columns(3)
        with c_r1: st.button("📉 - 4", key="r_s", on_click=execute_log, args=(pe["w"], pe["p"], pe["t"], pe["s"], "- 4 échanges"))
        with c_r2: st.button("⚖️ 4-8", key="r_m", on_click=execute_log, args=(pe["w"], pe["p"], pe["t"], pe["s"], "4-8 échanges"))
        with c_r3: st.button("🚀 + 8", key="r_l", on_click=execute_log, args=(pe["w"], pe["p"], pe["t"], pe["s"], "+ 8 échanges"))
    elif match_termine:
        if st.button("💾 Clôturer et Archiver ce Match Maintenant", use_container_width=True, type="primary"):
            df_t = pd.DataFrame(st.session_state.match_data)
            if not df_t.empty:
                v_a_1 = len(df_t[(df_t["Serveur du point"] == player_a) & (df_t["Balle de service"] == "1ère Balle")])
                v_a_2 = len(df_t[(df_t["Serveur du point"] == player_a) & (df_t["Balle de service"] == "2e Balle")])
                v_b_1 = len(df_t[(df_t["Serveur du point"] == player_b) & (df_t["Balle de service"] == "1ère Balle")])
                v_b_2 = len(df_t[(df_t["Serveur du point"] == player_b) & (df_t["Balle de service"] == "2e Balle")])
                tot = max(1, len(df_t)); tot_ue_a = max(1, len(df_t[(df_t["Joueur ayant fait l'action/erreur"] == player_a) & (df_t["Type d'action"] == "Faute Directe")]))
                tot_ue_b = max(1, len(df_t[(df_t["Joueur ayant fait l'action/erreur"] == player_b) & (df_t["Type d'action"] == "Faute Directe")]))
                status_label = f" (Victoire de {player_b if sc['abandon_player'] == player_a else player_a}) Score: {text_score_visuel.strip()}"
                summary = {
                    "Date": match_date.strftime("%d/%m/%Y"), "Match": f"{player_a} ({rank_a}) vs {player_b} ({rank_b}){status_label}", "Total Points": tot,
                    f"Aces % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Ace')]) / tot):.1%}", f"Aces % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Ace')]) / tot):.1%}",
                    f"% 1er Srv In {player_a}": f"{(v_a_1/max(1,v_a_1+v_a_2)):.1%}", f"% Pts Gagne 1er Srv {player_a}": f"{(len(df_t[(df_t['Serveur du point'] == player_a) & (df_t['Balle de service'] == '1ère Balle') & (df_t['Gagnant du point'] == player_a)])/max(1,v_a_1)):.1%}", f"% Pts Gagne 2nd Srv {player_a}": f"{(len(df_t[(df_t['Serveur du point'] == player_a) & (df_t['Balle de service'] == '2e Balle') & (df_t['Gagnant du point'] == player_a)])/max(1,v_a_2)):.1%}",
                    f"% 1er Srv In {player_b}": f"{(v_b_1/max(1,v_b_1+v_b_2)):.1%}", f"% Pts Gagne 1er Srv {player_b}": f"{(len(df_t[(df_t['Serveur du point'] == player_b) & (df_t['Balle de service'] == '1ère Balle') & (df_t['Gagnant du point'] == player_b)])/max(1,v_b_1)):.1%}", f"% Pts Gagne 2nd Srv {player_b}": f"{(len(df_t[(df_t['Serveur du point'] == player_b) & (df_t['Balle de service'] == '2e Balle') & (df_t['Gagnant du point'] == player_b)])/max(1,v_b_2)):.1%}",
                    f"CD Winners % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}", f"REV Winners % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"CD Winners % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}", f"REV Winners % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"Fautes Directes CD % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot_ue_a):.1%}", f"Fautes Directes REV % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Revers')]) / tot_ue_a):.1%}",
                    f"Fautes Directes CD % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot_ue_b):.1%}", f"Fautes Directes REV % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Revers')]) / tot_ue_b):.1%}",
                    f"F. Provoquées CD % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}", f"F. Provoquées REV % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"F. Provoquées CD % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}", f"F. Provoquées REV % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"Rallyes Courts (-4) % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Longueur Échange'] == '- 4 échanges')]) / tot):.1%}", f"Rallyes Moyens (4-8) % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Longueur Échange'] == '4-8 échanges')]) / tot):.1%}", f"Rallyes Longs (+8) % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Longueur Échange'] == '+ 8 échanges')]) / tot):.1%}",
                    f"Rallyes Courts (-4) % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Longueur Échange'] == '- 4 échanges')]) / tot):.1%}", f"Rallyes Moyens (4-8) % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Longueur Échange'] == '4-8 échanges')]) / tot):.1%}", f"Rallyes Longs (+8) % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Longueur Échange'] == '+ 8 échanges')]) / tot):.1%}",
                }
                st.session_state.all_match_summaries.append(summary)
                if st.session_state.match_data: st.session_state.match_data[-1]["Événement Match"] = "🎉 FIN DE MATCH"
                st.session_state.all_points_logs.extend(st.session_state.match_data)
            st.session_state.match_data, st.session_state.score_history, st.session_state.service_state = [], [], "1ère Balle"
            st.session_state.score = {"pA_points":0,"pB_points":0,"pA_jeux":0,"pB_jeux":0,"pA_sets":0,"pB_sets":0,"sets_history_A":[],"sets_history_B":[],"in_tiebreak":False,"in_supertb":False,"serveur_actuel":player_a,"pts_servis_tb":0, "abandon_player":None}
            st.rerun()
    else:
        st.markdown('<div class="btn-srv">', unsafe_allow_html=True)
        cs1, cs2, cs3 = st.columns(3)
        with cs1: st.button("🔄 2e Srv", disabled=st.session_state.service_state == "2e Balle", key="sec_bal")
        with cs2: st.button("🎯 Ace", on_click=queue_event, args=(sc["serveur_actuel"], sc["serveur_actuel"], "Ace", "Service"), key="ace_b")
        with cs3: st.button("❌ DblF", on_click=queue_event, args=(player_b if sc["serveur_actuel"] == player_a else player_a, sc["serveur_actuel"], "Double Faute", "Service"), key="df_b")
        st.markdown('</div>', unsafe_allow_html=True)
        cpA, cpB = st.columns(2)
        with cpA:
            st.markdown(f"<p class='player-label-grid'>{player_a[:11]}</p>", unsafe_allow_html=True)
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            st.button("🔥 CD Gagnant", key="w_cd_a", on_click=queue_event, args=(player_a, player_a, "Winner", "Coup Droit"))
            st.button("🔥 Revers Gagnant", key="w_rev_a", on_click=queue_event, args=(player_a, player_a, "Winner", "Revers"))
            st.button("📉 Faute CD", key="ue_cd_a", on_click=queue_event, args=(player_b, player_a, "Faute Directe", "Coup Droit"))
            st.button("📉 Faute Rev", key="ue_rev_a", on_click=queue_event, args=(player_b, player_a, "Faute Directe", "Revers"))
            st.button("🛡️ F.Prov CD", key="fe_cd_a", on_click=queue_event, args=(player_b, player_a, "Faute Provoquée", "Coup Droit"))
            st.button("🛡️ F.Prov Rev", key="fe_rev_a", on_click=queue_event, args=(player_b, player_a, "Faute Provoquée", "Revers"))
            st.markdown('</div>', unsafe_allow_html=True)
        with cpB:
            st.markdown(f"<p class='player-label-grid'>{player_b[:11]}</p>", unsafe_allow_html=True)
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            st.button("🔥 CD Gagnant ", key="w_cd_b", on_click=queue_event, args=(player_b, player_b, "Winner", "Coup Droit"))
            st.button("🔥 Revers Gagnant ", key="w_rev_b", on_click=queue_event, args=(player_b, player_b, "Winner", "Revers"))
            st.button("📉 Faute CD ", key="ue_cd_b", on_click=queue_event, args=(player_a, player_b, "Faute Directe", "Coup Droit"))
            st.button("📉 Faute Rev ", key="ue_rev_b", on_click=queue_event, args=(player_a, player_b, "Faute Directe", "Revers"))
            st.button("🛡️ F.Prov CD ", key="fe_cd_b", on_click=queue_event, args=(player_a, player_b, "Faute Provoquée", "Coup Droit"))
            st.button("🛡️ F.Prov Rev ", key="fe_rev_b", on_click=queue_event, args=(player_a, player_b, "Faute Provoquée", "Revers"))
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="btn-undo">', unsafe_allow_html=True)
        if st.button("↩️ Annuler le dernier coup", disabled=not st.session_state.match_data, key="un_c"): undo_last_point()
        st.markdown('</div>', unsafe_allow_html=True)
        c_abd1, c_abd2 = st.columns(2)
        with c_abd1:
            st.markdown('<div class="btn-undo">', unsafe_allow_html=True)
            if st.button(f"🤕 Ab. {player_a[:8]}", key="s_abd_a"): sc["abandon_player"] = player_a; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_abd2:
            st.markdown('<div class="btn-undo">', unsafe_allow_html=True)
            if st.button(f"🤕 Ab. {player_b[:8]}", key="s_abd_b"): sc["abandon_player"] = player_b; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    df_active = pd.DataFrame(st.session_state.all_points_logs)
    if not st.session_state.all_match_summaries: st.info("Aucun match archivé.")
    else:
        df_gs = pd.DataFrame(st.session_state.all_match_summaries); st.dataframe(df_gs, use_container_width=True, hide_index=True)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_gs.to_excel(writer, sheet_name='Efficacite Service Saison', index=False)
            df_active.to_excel(writer, sheet_name='Historique Detaille Points', index=False)
            workbook = writer.book; from openpyxl.styles import PatternFill, Border, Side
            fA, fB, fE = PatternFill(start_color="E6F0FA", fill_type="solid"), PatternFill(start_color="FCE8E6", fill_type="solid"), PatternFill(start_color="C3E6CB", fill_type="solid")
            ts = Side(style='thin', color='CBD5E1'); db = Border(bottom=Side(style='double', color='155724')); sb = Border(left=ts, right=ts, top=ts, bottom=ts)
            ws_s = writer.sheets['Efficacite Service Saison']
            for r in range(2, len(df_gs) + 2):
                for c in range(1, len(df_gs.columns) + 1):
                    cell = ws_s.cell(row=r, column=c); cell.border = sb; h_name = ws_s.cell(row=1, column=c).value
                    if h_name and player_a in str(h_name): cell.fill = fA
                    elif h_name and player_b in str(h_name): cell.fill = fB
            ws_p = writer.sheets['Historique Detaille Points']
            for r in range(2, len(df_active) + 2):
                is_f = any("FIN DE MATCH" in str(ws_p.cell(row=r, column=c).value).upper() for c in range(1, len(df_active.columns)+1) if ws_p.cell(row=r, column=c).value)
                act = ws_p.cell(row=r, column=4).value
                for c in range(1, len(df_active.columns) + 1):
                    cell = ws_p.cell(row=r, column=c); cell.border = sb
                    if is_f: cell.fill = fE; cell.border = db
                    elif act == player_a: cell.fill = fA
                    elif act == player_b: cell.fill = fB
        st.download_button(label="📥 Télécharger (.xlsx)", data=excel_buffer.getvalue(), file_name="bilan_tennis.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
