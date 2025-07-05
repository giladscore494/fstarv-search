import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# פונקציית חישוב קישור ל-Transfermarkt
def generate_transfermarkt_link(player_name):
    player_name_encoded = player_name.replace(" ", "+")
    return f"https://www.google.com/search?q={player_name_encoded}+site:transfermarkt.com"

# פונקציית חישוב YSP
def calculate_ysp_score(row):
    position = str(row["Pos"])
    minutes = row["Min"]
    goals = row["Gls"]
    assists = row["Ast"]
    dribbles = row["Succ"]
    key_passes = row["KP"]
    tackles = row["Tkl"]
    interceptions = row["Int"]
    clearances = row["Clr"]
    blocks = row["Blocks"]
    age = row["Age"]
    league = row["Comp"]

    benchmarks = {
        "GK": {"Min": 3000, "Clr": 30, "Tkl": 10, "Blocks": 15},
        "DF": {"Tkl": 50, "Int": 50, "Clr": 120, "Blocks": 30, "Min": 3000, "Gls": 3, "Ast": 2},
        "MF": {"Gls": 10, "Ast": 10, "Succ": 50, "KP": 50, "Min": 3000},
        "FW": {"Gls": 20, "Ast": 15, "Succ": 40, "KP": 40, "Min": 3000}
    }

    league_weights = {
        "eng Premier League": 1.00,
        "es La Liga": 0.98,
        "de Bundesliga": 0.96,
        "it Serie A": 0.95,
        "fr Ligue 1": 0.93
    }

    ysp_score = 0
    if "GK" in position:
        bm = benchmarks["GK"]
        ysp_score = (
            (minutes / bm["Min"]) * 40 +
            (clearances / bm["Clr"]) * 20 +
            (tackles / bm["Tkl"]) * 20 +
            (blocks / bm["Blocks"]) * 20
        )
    elif "DF" in position:
        bm = benchmarks["DF"]
        ysp_score = (
            (tackles / bm["Tkl"]) * 18 +
            (interceptions / bm["Int"]) * 18 +
            (clearances / bm["Clr"]) * 18 +
            (blocks / bm["Blocks"]) * 10 +
            (minutes / bm["Min"]) * 10 +
            (goals / bm["Gls"]) * 13 +
            (assists / bm["Ast"]) * 13
        )
    elif "MF" in position:
        bm = benchmarks["MF"]
        ysp_score = (
            (goals / bm["Gls"]) * 20 +
            (assists / bm["Ast"]) * 20 +
            (dribbles / bm["Succ"]) * 20 +
            (key_passes / bm["KP"]) * 20 +
            (minutes / bm["Min"]) * 20
        )
    elif "FW" in position:
        bm = benchmarks["FW"]
        ysp_score = (
            (goals / bm["Gls"]) * 30 +
            (assists / bm["Ast"]) * 25 +
            (dribbles / bm["Succ"]) * 15 +
            (key_passes / bm["KP"]) * 15 +
            (minutes / bm["Min"]) * 15
        )
    else:
        ysp_score = (goals * 3 + assists * 2 + minutes / 250)

    if minutes > 0:
        contribution_per_90 = ((goals + assists + dribbles * 0.5 + key_passes * 0.5) / minutes) * 90
        if contribution_per_90 >= 1.2:
            ysp_score += 15
        elif contribution_per_90 >= 0.9:
            ysp_score += 10
        elif contribution_per_90 >= 0.6:
            ysp_score += 5

    if age <= 20:
        ysp_score *= 1.1
    elif age <= 23:
        ysp_score *= 1.05

    league_weight = league_weights.get(league.strip(), 0.9)
    ysp_score *= league_weight
    return min(round(ysp_score, 2), 100)

# טעינת נתונים
@st.cache_data
def load_players():
    path = os.path.join("data", "players_simplified_2025.csv")
    return pd.read_csv(path)

# ממשק
st.set_page_config("FstarVfootball - Search Tool", layout="wide")
st.title("🔍 חיפוש שחקנים - מדד YSP עם שווי שוק")

players = load_players()
player_names = players["Player"].sort_values().unique()
selected_name = st.selectbox("בחר שחקן", player_names)

selected_row = players[players["Player"] == selected_name].iloc[0]
ysp_score = calculate_ysp_score(selected_row)

st.markdown(f"### 🧠 מדד YSP: `{ysp_score}`")

# הזנת שווי שוק (במיליונים)
market_value_mil = st.number_input("הזן שווי שוק נוכחי של השחקן (במיליוני אירו)", min_value=0.0, step=0.5)

if market_value_mil > 0:
    predicted_future_value = min((ysp_score / 100) * market_value_mil * 2.3, market_value_mil * 4)
    roi = predicted_future_value - market_value_mil
    st.success(f"📈 תחזית שווי עתידי: €{predicted_future_value:.1f}M")
    st.info(f"💡 ROI צפוי (רווח פוטנציאלי): €{roi:.1f}M — מבוסס על הביצועים ומדד הפוטנציאל")
else:
    st.warning("הזן שווי שוק נוכחי כדי לחשב תחזית עתידית ו־ROI")

# פרטי השחקן + קישור
st.markdown(f"**ליגה**: {selected_row['Comp']} | **גיל**: {selected_row['Age']} | **עמדה**: {selected_row['Pos']}")
link = generate_transfermarkt_link(selected_row["Player"])
st.markdown(f"🔎 [עמוד השחקן ב־Transfermarkt]({link})", unsafe_allow_html=True)
