

import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="FstarVfootball - חיפוש שחקנים", layout="wide")

@st.cache_data
def load_players():
    path = os.path.join("data", "players_simplified_2025_with_club.csv")
    df = pd.read_csv(path)
    df = df.dropna(subset=["Age", "xG", "Min"])
    df = df[df["Min"] >= 300]  # מסנן שחקנים שלא שיחקו מספיק
    df["xG_per90"] = df["xG"] / (df["Min"] / 90)
    return df

def calculate_ysp_weighted(row, market_value=None):
    minutes = row["Min"]
    age = row["Age"]
    xG = row["xG"]
    xAG = row["xAG"]
    KP = row["KP"]
    Pos = row["Pos"]

    per90 = 90 / minutes
    xG90 = xG * per90
    xAG90 = xAG * per90
    KP90 = KP * per90

    base_score = xG90 * 25 + xAG90 * 20 + KP90 * 3

    if "FW" in Pos:
        base_score *= 1.1
    elif "MF" in Pos:
        base_score *= 1.0
    elif "DF" in Pos:
        base_score *= 0.8
    elif "GK" in Pos:
        base_score *= 0.6

    if age <= 21:
        base_score *= 1.05
    if age <= 18:
        base_score *= 1.15

    if market_value and market_value > 0:
        multiplier = 1.0
        if market_value < 5000000:
            multiplier += 0.05
        elif market_value < 2000000:
            multiplier += 0.1
        elif market_value > 15000000:
            multiplier -= 0.05
        base_score *= multiplier

    return round(min(base_score, 100), 1)

# טופס סינון
st.title("🔎 מערכת חיפוש שחקנים לפי צרכים")
st.markdown("בחר קריטריונים למציאת שחקנים")

age_limit = st.number_input("גיל מקסימלי", min_value=16, max_value=40, value=21)
position = st.selectbox("עמדה", ["FW", "MF", "DF", "GK"])
xg_threshold = st.slider("xG ל־90 דקות - מינימום", 0.0, 1.0, 0.3, 0.05)

players = load_players()

filtered = players[
    (players["Age"] <= age_limit) &
    (players["Pos"].str.contains(position)) &
    (players["xG_per90"] >= xg_threshold)
]

st.markdown(f"### נמצאו {len(filtered)} שחקנים מתאימים")

for idx, row in filtered.iterrows():
    col1, col2, col3 = st.columns([2, 1, 2])
    col1.markdown(f"**{row['Player']}** ({int(row['Age'])})")
    col2.markdown(f"{row['Pos']}")
    col3.markdown(f"xG/90: `{row['xG_per90']:.2f}`")

    tm_link = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query=" + row['Player'].replace(" ", "+")
    st.markdown(f"[🔗 Transfermarkt]({tm_link})", unsafe_allow_html=True)

    market_input = st.text_input(f"שווי שוק (€) עבור {row['Player']}", key=f"mv_{idx}")
    if market_input:
        try:
            market_clean = market_input.lower().replace("m", "000000").replace("מיליון", "000000").replace("€", "").replace(",", "").strip()
            market_value = float(market_clean)

            ysp_score = calculate_ysp_weighted(row, market_value)
            future_value = market_value * (1.5 + row['xG_per90'])

            st.success(f"YSP: {ysp_score} | שווי עתידי חזוי: €{future_value:,.0f}")

        except:
            st.warning("אנא הזן ערך מספרי תקין (למשל: 8000000 או 10m)")
