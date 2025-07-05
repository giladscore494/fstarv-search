
import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="FstarVfootball - חיפוש מתקדם YSP-75", layout="wide")

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

# UI
st.title("🔬 מערכת חיפוש מתקדמת – YSP-75 + ROI + גרף")
st.markdown("בחר סינונים מתקדמים למציאת שחקנים")

age_limit = st.number_input("גיל מקסימלי", min_value=16, max_value=40, value=23)
position = st.selectbox("עמדה", ["FW", "MF", "DF", "GK"])
kp_min = st.slider("מסירות מפתח מינימלי", 0, 100, 10)
dribbles_min = st.slider("דריבלים מוצלחים מינימלי", 0, 100, 10)
contrib_min = st.slider("תרומה כוללת ל־90 (שערים + בישולים + 0.5×KP + 0.5×דריבלים)", 0.0, 3.0, 0.8, 0.1)

players = load_players()

players["Contribution90"] = ((players["Gls"] + players["Ast"] + players["KP"]*0.5 + players["Succ"]*0.5) / players["Min"]) * 90
players["YSP"] = players.apply(calculate_ysp_score, axis=1)

filtered = players[
    (players["Age"] <= age_limit) &
    (players["Pos"].str.contains(position)) &
    (players["KP"] >= kp_min) &
    (players["Succ"] >= dribbles_min) &
    (players["Contribution90"] >= contrib_min)
]

st.markdown(f"### נמצאו {len(filtered)} שחקנים מתאימים")

# טבלת תצוגה עם שווי שוק ידני + ROI
roi_results = []

for idx, row in filtered.iterrows():
    col1, col2, col3 = st.columns([3, 2, 3])
    col1.markdown(f"**{row['Player']}** ({int(row['Age'])}) – {row['Pos']}")
    col2.markdown(f"YSP: `{row['YSP']}` | תרומה/90: `{row['Contribution90']:.2f}`")

    market_input = st.text_input(f"שווי שוק (€) עבור {row['Player']}", key=f"mv_{idx}")
    if market_input:
        try:
            market_clean = market_input.lower().replace("m", "000000").replace("מיליון", "000000").replace("€", "").replace(",", "").strip()
            market_value = float(market_clean)
            roi = row['YSP'] / (market_value / 1e6)
            col3.success(f"ROI: {roi:.2f}")
            roi_results.append((row['Player'], row['YSP'], row['Contribution90'], roi))
        except:
            col3.warning("הזן ערך מספרי תקין (למשל 8000000)")

# גרף השוואה
if roi_results:
    st.markdown("### 📊 גרף השוואה בין שחקנים")
    chart_df = pd.DataFrame(roi_results, columns=["Player", "YSP", "Contribution90", "ROI"])
    st.bar_chart(chart_df.set_index("Player")[["YSP", "Contribution90", "ROI"]])

# כפתור הורדת CSV
if not filtered.empty:
    csv_data = filtered[["Player", "Age", "Pos", "Comp", "Gls", "Ast", "Succ", "KP", "Contribution90", "YSP"]].copy()
    st.download_button("📥 הורד CSV עם תוצאות", csv_data.to_csv(index=False).encode("utf-8"), file_name="filtered_players.csv", mime="text/csv")
