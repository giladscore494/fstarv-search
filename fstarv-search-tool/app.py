import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="FstarV Search Tool", layout="wide")

@st.cache_data
def load_players():
    return pd.read_csv("players_simplified_2025.csv")

players = load_players()
players.columns = players.columns.str.strip()

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

# חישוב YSP + תרומה ל־90 דקות
players["YSP"] = players.apply(calculate_ysp_score, axis=1)
players["Contribution90"] = ((players["Gls"] + players["Ast"] + players["Succ"] * 0.5 + players["KP"] * 0.5) / players["Min"]) * 90

# סינונים
min_age = st.slider("גיל מינימלי", 16, 30, 16)
position_filter = st.selectbox("בחר עמדה", ["All", "GK", "DF", "MF", "FW"])
min_kp = st.slider("מסירות מפתח מינימליות", 0, 50, 0)
min_dribbles = st.slider("דריבלים מוצלחים מינימליים", 0, 50, 0)
min_contrib = st.slider("תרומה ל־90 דקות (xG+xA+KP) מינימלית", 0.0, 3.0, 0.0, step=0.1)

filtered = players[players["Age"] >= min_age]
if position_filter != "All":
    filtered = filtered[filtered["Pos"].str.contains(position_filter)]
filtered = filtered[filtered["KP"] >= min_kp]
filtered = filtered[filtered["Succ"] >= min_dribbles]
filtered = filtered[filtered["Contribution90"] >= min_contrib]

# תצוגה
st.markdown("## תוצאות סינון שחקנים")
roi_results = []

for idx, row in filtered.iterrows():
    col1, col2, col3 = st.columns([3, 3, 2])
    col1.markdown(f"**{row['Player']}** ({int(row['Age'])}) – {row['Pos']}")
    col1.markdown(f"ליגה: {row['Comp']} | דקות: {int(row['Min'])}")
    col1.markdown(f"גולים: {row['Gls']} | בישולים: {row['Ast']}")
    col1.markdown(f"YSP: **{row['YSP']}** | תרומה ל־90: {round(row['Contribution90'],2)}")

    # קישור ל־Transfermarkt
    search_query = f"{row['Player']} site:transfermarkt.com"
    search_url = f"https://duckduckgo.com/?q={search_query.replace(' ', '+')}"
    col1.markdown(f"[🔎 עמוד שחקן ב־Transfermarkt]({search_url})")

    market_input = col2.text_input("שווי שוק (במיליוני אירו)", key=f"mv_{idx}")
    if market_input:
        try:
            market_millions = float(market_input.strip())
            if market_millions > 200:
                col3.error("⛔ הזן ערך במיליוני אירו בלבד – לדוגמה 5")
            else:
                market_value = market_millions * 1_000_000
                roi = (row['YSP'] / market_value) * 1_000_000

                if roi > 15:
                    col3.success("🟢 שחקן משתלם מאוד – ROI גבוה")
                elif roi > 10:
                    col3.info("🔵 משתלם – כדאי לבדוק")
                elif roi > 5:
                    col3.warning("🟠 שחקן במחיר סביר")
                else:
                    col3.error("🔴 יקר ביחס לפוטנציאל – ROI נמוך")

                roi_results.append((row['Player'], row['YSP'], row['Contribution90'], roi))
        except:
            col3.warning("⚠ הזן מספר חוקי בלבד – לדוגמה: 4.5")

# גרף השוואה
if roi_results:
    st.markdown("## 🔍 השוואה גרפית בין שחקנים")
    df_plot = pd.DataFrame(roi_results, columns=["Player", "YSP", "Contribution90", "ROI"])
    st.bar_chart(df_plot.set_index("Player")[["YSP", "Contribution90"]])

    # הורדה
    csv = df_plot.to_csv(index=False).encode('utf-8')
    st.download_button("📥 הורד תוצאות כ־CSV", data=csv, file_name="filtered_players.csv", mime="text/csv")
