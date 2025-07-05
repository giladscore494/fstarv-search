
import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="FstarVfootball - YSP-75 אמיתי", layout="wide")

@st.cache_data
def load_players():
    path = os.path.join("data", "players_simplified_2025_with_club.csv")
    df = pd.read_csv(path)
    df = df.dropna(subset=["Age", "Min", "Gls", "Ast", "Succ", "KP", "Tkl", "Int", "Clr", "Blocks", "Pos", "Comp"])
    return df

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

# ממשק Streamlit
st.title("🔍 מערכת חיפוש עם מדד YSP-75 האמיתי")
st.markdown("בחר קריטריונים לחיפוש שחקנים מתאימים")

age_limit = st.number_input("גיל מקסימלי", min_value=16, max_value=40, value=23)
position = st.selectbox("עמדה", ["FW", "MF", "DF", "GK"])

players = load_players()
filtered = players[
    (players["Age"] <= age_limit) &
    (players["Pos"].str.contains(position))
]

st.markdown(f"### נמצאו {len(filtered)} שחקנים")

for idx, row in filtered.iterrows():
    col1, col2, col3 = st.columns([3, 1, 2])
    col1.markdown(f"**{row['Player']}** ({int(row['Age'])}) - {row['Comp']}")
    col2.markdown(f"עמדה: `{row['Pos']}`")
    ysp_score = calculate_ysp_score(row)
    col3.success(f"מדד YSP-75: {ysp_score}")

    tm_link = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query=" + row['Player'].replace(" ", "+")
    st.markdown(f"[🔗 Transfermarkt]({tm_link})", unsafe_allow_html=True)
