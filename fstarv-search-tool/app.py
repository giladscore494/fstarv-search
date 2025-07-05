import streamlit as st
import pandas as pd
import numpy as np
import os
import urllib.parse

st.set_page_config(page_title="FstarV Search Tool", layout="wide")
st.title("🔍 FstarVfootball - חיפוש שחקנים מתקדם")

@st.cache_data
def load_players():
    path = os.path.join("data", "players_simplified_2025.csv")
    return pd.read_csv(path)

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
            (clearances / bm["Clr"]) * 30 +
            (tackles / bm["Tkl"]) * 20 +
            (blocks / bm["Blocks"]) * 10
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

@st.cache_data
def generate_transfermarkt_link(name):
    query = urllib.parse.quote(f"{name} site:transfermarkt.com")
    return f"https://duckduckgo.com/?q={query}"

players = load_players()
players["YSP"] = players.apply(calculate_ysp_score, axis=1)

positions = sorted(players["Pos"].dropna().unique())
selected_position = st.selectbox("בחר עמדה", positions)
filtered = players[players["Pos"] == selected_position]

age_range = st.slider("🎂 סינון לפי גיל", 16, 40, (16, 40))
filtered = filtered[(filtered["Age"] >= age_range[0]) & (filtered["Age"] <= age_range[1])]

if "xG" in players.columns:
    xg_range = st.slider("⚽️ סינון לפי xG צפוי", 0.0, 25.0, (0.0, 25.0))
    filtered = filtered[(filtered["xG"] >= xg_range[0]) & (filtered["xG"] <= xg_range[1])]

if selected_position == "GK":
    clr_range = st.slider("📊 סינון: הרחקות (Clr)", 0, 100, (0, 100))
    tkl_range = st.slider("📊 תיקולים (Tkl)", 0, 50, (0, 50))
    filtered = filtered[(filtered["Clr"] >= clr_range[0]) & (filtered["Clr"] <= clr_range[1]) &
                         (filtered["Tkl"] >= tkl_range[0]) & (filtered["Tkl"] <= tkl_range[1])]
elif selected_position == "DF":
    int_range = st.slider("📊 חטיפות (Int)", 0, 100, (0, 100))
    clr_range = st.slider("📊 הרחקות (Clr)", 0, 150, (0, 150))
    filtered = filtered[(filtered["Int"] >= int_range[0]) & (filtered["Int"] <= int_range[1]) &
                         (filtered["Clr"] >= clr_range[0]) & (filtered["Clr"] <= clr_range[1])]
elif selected_position == "MF":
    kp_range = st.slider("📊 מסירות מפתח (KP)", 0, 100, (0, 100))
    succ_range = st.slider("📊 דריבלים מוצלחים (Succ)", 0, 100, (0, 100))
    filtered = filtered[(filtered["KP"] >= kp_range[0]) & (filtered["KP"] <= kp_range[1]) &
                         (filtered["Succ"] >= succ_range[0]) & (filtered["Succ"] <= succ_range[1])]
elif selected_position == "FW":
    gls_range = st.slider("📊 שערים (Gls)", 0, 30, (0, 30))
    ast_range = st.slider("📊 בישולים (Ast)", 0, 20, (0, 20))
    filtered = filtered[(filtered["Gls"] >= gls_range[0]) & (filtered["Gls"] <= gls_range[1]) &
                         (filtered["Ast"] >= ast_range[0]) & (filtered["Ast"] <= ast_range[1])]

for idx, row in filtered.iterrows():
    st.markdown(f"**{row['Player']}** | גיל: {row['Age']} | עמדה: {row['Pos']} | דקות: {row['Min']}")
    st.markdown(f"✳️ מדד YSP: {row['YSP']}")
    link = generate_transfermarkt_link(row["Player"])
    st.markdown(f"🔗 [עמוד Transfermarkt של {row['Player']}]({link})")

    market_value = st.number_input(f"💶 הזן שווי שוק נוכחי ב-מיליון אירו עבור {row['Player']}", key=f"mv_{idx}", min_value=0.0, step=0.1, format="%.2f")
    if market_value > 0:
        future_value = (row["YSP"] / 100) * 100
        if future_value > market_value:
            roi_text = "פוטנציאל גבוה משמעותית לעומת השווי הנוכחי"
        elif future_value == market_value:
            roi_text = "שווי השחקן תואם את הפוטנציאל הנוכחי"
        else:
            roi_text = "השווי הנוכחי גבוה מהפוטנציאל - סיכון השקעה"
        st.markdown(f"📈 ROI: {roi_text}")

    st.markdown("---")
