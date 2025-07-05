import streamlit as st
import pandas as pd
import os
import urllib.parse

st.set_page_config(page_title="FstarVfootball - ROI חכם", layout="wide")

# ----- טען נתונים -----
@st.cache_data
def load_players():
    path = os.path.join("data", "players_simplified_2025.csv")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
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

# ----- ממשק -----
st.title("🔍 חיפוש מתקדם לשחקני כדורגל + ROI")
players = load_players()

# אפשרות סינון לפי גיל, xG, עמדה וכו'
st.sidebar.header("סינון מתקדם")
position_filter = st.sidebar.selectbox("בחר עמדה", options=["ALL"] + sorted(players["Pos"].unique()))
age_max = st.sidebar.slider("גיל מרבי", 16, 28, 23)
xg_min = st.sidebar.slider("מינימום xG", 0.0, 10.0, 3.0, step=0.1)
dribble_min = st.sidebar.slider("מינימום דריבלים", 0, 100, 20)
keypass_min = st.sidebar.slider("מינימום מסירות מפתח", 0, 100, 20)

filtered = players.copy()
if position_filter != "ALL":
    filtered = filtered[filtered["Pos"] == position_filter]

filtered = filtered[(filtered["Age"] <= age_max) &
                    (filtered["xG"] >= xg_min) &
                    (filtered["Succ"] >= dribble_min) &
                    (filtered["KP"] >= keypass_min)]

# חישוב YSP + הזנת שווי שוק והצגת ROI
st.markdown("---")
st.subheader("תוצאות החיפוש")

for i, row in filtered.iterrows():
    name = row["Player"]
    club = row["Club"]
    pos = row["Pos"]
    league = row["Comp"]
    age = row["Age"]

    ysp = calculate_ysp_score(row)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**{name}** ({pos}) - {club}, גיל {age}, ליגה: {league}")
        st.markdown(f"מדד YSP: **{ysp}**")

        search_url = f"https://duckduckgo.com/?q={urllib.parse.quote(name + ' site:transfermarkt.com')}"
        st.markdown(f"[🔗 עמוד Transfermarkt]( {search_url} )")

    with col2:
        market_value_input = st.text_input(f"שווי שוק במיליוני אירו ({name})", key=f"val_{i}")
        if market_value_input:
            try:
                market_value = float(market_value_input.replace(",", ".")) * 1_000_000
                predicted_value = ysp / 100 * 100_000_000  # חזוי לשיא הקריירה
                roi = round((predicted_value - market_value) / market_value * 100, 2)
                st.success(f"📈 ROI צפוי: {roi}% (שווי עתידי חזוי: €{predicted_value:,.0f})")
                st.caption("ה־ROI מציין את אחוז הרווח המשוער אם תשקיע בשחקן כעת.")
            except:
                st.warning("⚠️ אנא הזן מספר תקין במיליוני אירו בלבד.")
