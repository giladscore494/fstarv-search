import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="FstarVfootball Search", layout="wide")
st.title("🔍 FstarVfootball – חיפוש מתקדם לפי מדדי פוטנציאל")

@st.cache_data
def load_players():
    path = os.path.join("data", "players_simplified_2025.csv")  # ודא שהקובץ קיים שם
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

# פונקציית חישוב מדד YSP
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

# UI: סינון מתקדם
df = load_players()
position_filter = st.selectbox("בחר עמדה", options=["FW", "MF", "DF", "GK"])
filtered_df = df[df["Pos"].str.contains(position_filter)]

age_limit = st.slider("סינון גיל מירבי", 16, 28, 22)
xg_min = st.slider("סינון xG מינימלי", 0.0, 15.0, 1.0)
kp_min = st.slider("סינון מסירות מפתח", 0, 100, 10)
dribbles_min = st.slider("סינון דריבלים מוצלחים", 0, 100, 10)

filtered_df = filtered_df[
    (filtered_df["Age"] <= age_limit) &
    (filtered_df["xG"] >= xg_min) &
    (filtered_df["KP"] >= kp_min) &
    (filtered_df["Succ"] >= dribbles_min)
]

# הזנת שווי שוק ידני
market_value = st.number_input("הזן שווי שוק נוכחי של שחקן במיליוני יורו", min_value=0.0, format="%.2f")
st.caption("📌 הזן שווי שוק נוכחי כדי לחשב ROI עתידי. הקלט במיליונים בלבד.")

# חישוב תוצאה לכל שחקן
filtered_df["YSP-75"] = filtered_df.apply(calculate_ysp_score, axis=1)
if market_value > 0:
    filtered_df["Market Value (€M)"] = market_value
    filtered_df["Expected Future Value (€M)"] = filtered_df["YSP-75"].apply(lambda x: round(x / 100 * 80, 2))
    filtered_df["ROI (פי רווח עתידי)"] = (filtered_df["Expected Future Value (€M)"] - market_value).round(2)
else:
    filtered_df["Expected Future Value (€M)"] = "לא חושב"
    filtered_df["ROI (פי רווח עתידי)"] = "אין שווי שוק"

# קישור טרנספרמרקט אוטומטי
def generate_transfermarkt_link(player_name):
    query = player_name.replace(" ", "+")
    return f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={query}"

filtered_df["Transfermarkt"] = filtered_df["Player"].apply(
    lambda name: f"[עמוד שחקן](https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={name.replace(' ', '+')})"
)

# הצגת התוצאות
st.markdown("### תוצאות מסוננות")
st.dataframe(
    filtered_df[[
        "Player", "Age", "Pos", "Comp", "Min", "Gls", "Ast",
        "xG", "Succ", "KP", "YSP-75",
        "Expected Future Value (€M)", "ROI (פי רווח עתידי)", "Transfermarkt"
    ]],
    use_container_width=True
)
