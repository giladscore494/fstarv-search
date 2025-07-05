import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="FstarVfootball - חיפוש מתקדם", layout="wide")

# פונקציה לטעינת נתונים
@st.cache_data
def load_players():
    path = os.path.join("/mnt/data", "players_simplified_2025 (5).csv")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

# פונקציית חישוב מדד YSP-75
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

def generate_transfermarkt_link(player_name):
    player_name_encoded = player_name.replace(" ", "+")
    return f"https://www.google.com/search?q={player_name_encoded}+site:transfermarkt.com"

# UI
st.title("🔍 חיפוש מתקדם לפי מדד YSP-75")

players_df = load_players()

# סינון
positions = players_df["Pos"].dropna().unique().tolist()
selected_position = st.selectbox("בחר עמדה", ["All"] + sorted(positions))

age_limit = st.slider("סנן לפי גיל מקסימלי", 16, 30, 23)
min_xg = st.slider("xG מינימלי", 0.0, 15.0, 0.0)
min_kp = st.slider("מסירות מפתח מינימליות", 0, 50, 0)
min_dribbles = st.slider("דריבלים מוצלחים מינימליים", 0, 50, 0)

# הזנת שווי שוק
user_market_value = st.number_input("הזן שווי שוק נוכחי של שחקנים במיליוני אירו", min_value=0.0, step=0.1)

filtered = players_df.copy()
filtered = filtered[filtered["Age"] <= age_limit]
filtered = filtered[filtered["xG"] >= min_xg]
filtered = filtered[filtered["KP"] >= min_kp]
filtered = filtered[filtered["Succ"] >= min_dribbles]
if selected_position != "All":
    filtered = filtered[filtered["Pos"].str.contains(selected_position)]

# חישוב מדד לכל שחקן
filtered["YSP"] = filtered.apply(calculate_ysp_score, axis=1)

# ROI - תחזית רווח
if user_market_value > 0:
    filtered["ROI (€ לעתיד)"] = ((filtered["YSP"] / 100) * 50_000_000) - (user_market_value * 1_000_000)
    st.markdown("🔁 **ROI (החזר צפוי לעומת שווי נוכחי):** מבוסס על שווי עתידי פוטנציאלי של עד €50M")

# תוצאה
st.markdown("### תוצאות החיפוש:")

for _, row in filtered.sort_values(by="YSP", ascending=False).iterrows():
    st.markdown(f"**{row['Player']}** | גיל: {row['Age']} | ליגה: {row['Comp']} | עמדה: {row['Pos']}")
    st.write(f"YSP-75: {row['YSP']}")
    if user_market_value > 0:
        st.write(f"תחזית ROI: €{int(row['ROI (€ לעתיד)']):,}")
    link = generate_transfermarkt_link(row["Player"])
    st.markdown(f"[🔗 עמוד ב־Transfermarkt]({link})", unsafe_allow_html=True)
    st.markdown("---")

st.markdown(f"**ליגה**: {selected_row['Comp']} | **גיל**: {selected_row['Age']} | **עמדה**: {selected_row['Pos']}")
link = generate_transfermarkt_link(selected_row["Player"])
st.markdown(f"🔎 [עמוד השחקן ב־Transfermarkt]({link})", unsafe_allow_html=True)
