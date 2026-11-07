from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Bike Sharing Dashboard", layout="wide")

DATA_DIR = Path(__file__).parent
BLUE, GREY = "#2E86AB", "#9AA5B1"
SEASON_ORDER = ["Winter", "Spring", "Summer", "Fall"]
DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# Data loading and caching
@st.cache_data
def load_data():
    day = pd.read_csv(DATA_DIR / "day_clean.csv", parse_dates=["date"])
    hour = pd.read_csv(DATA_DIR / "hour_clean.csv", parse_dates=["date"])
    for df in (day, hour):
        df["temp_c"] = df["temp"] * 41  # dataset stores temp normalised to max 41 C
        df["day_type"] = df["workingday"].map({"Yes": "Working day", "No": "Weekend / holiday"})
    return day, hour


def pct(a, b):
    return (a / b - 1) * 100 if b else float("nan")


day, hour = load_data()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    picked = st.date_input("Date range", value=(day["date"].min(), day["date"].max()),
                           min_value=day["date"].min(), max_value=day["date"].max())
    if len(picked) != 2:
        st.info("Pick an end date to apply the range.")
        st.stop()
    start, end = map(pd.Timestamp, picked)
    seasons = st.multiselect("Season", SEASON_ORDER, default=SEASON_ORDER)
    weathers = st.multiselect("Weather", sorted(day["weather"].unique()),
                              default=sorted(day["weather"].unique()))
    day_types = st.multiselect("Day type", ["Working day", "Weekend / holiday"],
                               default=["Working day", "Weekend / holiday"])
    st.caption("Dataset: Capital Bikeshare, Washington DC, 2011-2012 (UCI).")


def apply(df):
    return df[df["date"].between(start, end) & df["season"].isin(seasons)
              & df["weather"].isin(weathers) & df["day_type"].isin(day_types)]


day, hour = apply(day), apply(hour)
if day.empty:
    st.warning("No data for these filters. Widen the selection in the sidebar.")
    st.stop()

# Header & KPIs
st.title("Bike Sharing Demand Dashboard")
st.caption("When and why do people rent bikes? Use the filters to slice demand, then read the takeaway under each chart.")

by_year = day.groupby("year")["total_user_count"].sum()
yoy = pct(by_year.get(2012, 0), by_year.get(2011, 0)) if {2011, 2012} <= set(by_year.index) else None

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total rentals", f"{day['total_user_count'].sum():,.0f}")
k2.metric("Avg rentals / day", f"{day['total_user_count'].mean():,.0f}")
k3.metric("Registered share", f"{day['registered'].sum() / day['total_user_count'].sum():.0%}")
k4.metric("2012 vs 2011", f"{yoy:+.1f}%" if yoy is not None else "n/a",
          help="Needs both years inside the selected date range.")

tab_trend, tab_env, tab_time, tab_reco = st.tabs(
    ["📈 Trend", "🌦️ Season & Weather", "🕒 Time of Day", "💡 Recommendations"])

# Trend
with tab_trend:
    monthly = (day.groupby(["year", "month"], as_index=False)["total_user_count"].sum()
               .assign(month=lambda x: pd.Categorical(x["month"], MONTH_ORDER, ordered=True))
               .sort_values(["year", "month"]))
    monthly["year"] = monthly["year"].astype(str)
    fig = px.line(monthly, x="month", y="total_user_count", color="year", markers=True,
                  color_discrete_sequence=[GREY, BLUE],
                  labels={"total_user_count": "Rentals", "month": "", "year": "Year"},
                  title="Monthly rentals, 2011 vs 2012")
    st.plotly_chart(fig, width="stretch")

    mix = day.groupby("year")[["casual", "registered"]].sum().reset_index().melt(
        "year", var_name="User type", value_name="Rentals")
    mix["year"] = mix["year"].astype(str)
    fig = px.bar(mix, x="year", y="Rentals", color="User type", barmode="group",
                 color_discrete_sequence=[GREY, BLUE],
                 title="Casual vs registered rentals by year", labels={"year": ""})
    st.plotly_chart(fig, width="stretch")

    peak = monthly.loc[monthly["total_user_count"].idxmax()]
    st.info(f"**Takeaway:** demand peaks in **{peak['month']} {peak['year']}** "
            f"({peak['total_user_count']:,.0f} rentals) and follows a clear seasonal curve "
            "in both years.")

# Season and weather
with tab_env:
    c1, c2 = st.columns(2)
    season_avg = (day.groupby("season", as_index=False)["total_user_count"].mean()
                  .assign(season=lambda x: pd.Categorical(x["season"], SEASON_ORDER, ordered=True))
                  .sort_values("season"))
    top_season = season_avg.loc[season_avg["total_user_count"].idxmax(), "season"]
    season_avg["hl"] = season_avg["season"].astype(str).eq(top_season).map({True: "Peak", False: "Other"})
    fig = px.bar(season_avg, x="season", y="total_user_count", color="hl",
                 color_discrete_map={"Peak": BLUE, "Other": GREY},
                 labels={"total_user_count": "Avg rentals / day", "season": ""},
                 title="Average daily rentals by season")
    fig.update_layout(showlegend=False)
    c1.plotly_chart(fig, width="stretch")
    c1.info(f"**Takeaway:** **{top_season}** is the busiest season "
            f"({season_avg['total_user_count'].max():,.0f} rentals/day on average).")
 
    weather_avg = (day.groupby("weather", as_index=False)
                   .agg(avg=("total_user_count", "mean"), days=("total_user_count", "size"))
                   .sort_values("avg", ascending=False))
    fig = px.bar(weather_avg, x="avg", y="weather", orientation="h", text="days",
                 labels={"avg": "Avg rentals / day", "weather": ""},
                 title="Average daily rentals by weather",
                 color_discrete_sequence=[BLUE])
    fig.update_traces(texttemplate="n=%{text} days", textposition="inside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    c2.plotly_chart(fig, width="stretch")
 
    best, worst = weather_avg.iloc[0], weather_avg.iloc[-1]
    if len(weather_avg) > 1:
        gap = (1 - worst["avg"] / best["avg"]) * 100
        msg = (f"**Takeaway:** **{best['weather']}** days average {best['avg']:,.0f} rentals, "
               f"while **{worst['weather']}** days average {worst['avg']:,.0f} "
               f"(about {gap:.0f}% lower).")
        if worst["days"] < 30:
            msg += f" Only {worst['days']} days fall in the lowest category, so treat the gap as indicative."
    else:
        msg = f"**Takeaway:** only **{best['weather']}** days are selected; widen the weather filter to compare."
    c2.info(msg)


# Time of day
with tab_time:
    by_hour = hour.groupby(["hour", "day_type"], as_index=False)["total_user_count"].mean()
    fig = px.line(by_hour, x="hour", y="total_user_count", color="day_type", markers=True,
                  color_discrete_map={"Working day": BLUE, "Weekend / holiday": GREY},
                  labels={"total_user_count": "Avg rentals / hour", "hour": "Hour of day",
                          "day_type": ""},
                  title="Average rentals by hour: working days vs weekends/holidays")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")

    workday = hour[hour["day_type"] == "Working day"].groupby("hour")["total_user_count"].mean()
    weekend = hour[hour["day_type"] != "Working day"].groupby("hour")["total_user_count"].mean()
    msg = "**Takeaway:** "
    if not workday.empty:
        msg += (f"working days show commuter spikes at **{workday[workday.index < 12].idxmax()}:00** "
                f"and **{workday[workday.index >= 12].idxmax()}:00**; ")
    if not weekend.empty:
        msg += f"weekends/holidays peak midday around **{weekend.idxmax()}:00**."
    st.info(msg)

# Recommendations
with tab_reco:
    st.subheader("What the data suggests")
    st.markdown(
        "- **Rebalance Bikes by Time of Day:** On working days, stock commuter hubs before 8 AM and 5 PM. On weekends, move bikes toward leisure areas for the midday peak.\n"
        "- **Weekend Promotions:** To increase Bike Share usage on weekends, consider offering special promotions such as weekend discounts or morning-specific promotions. These initiatives could help increase rental activity during the morning, similar to weekday patterns, while also encouraging a healthy lifestyle through morning cycling. \n"
        "- **Plan Around Season and Weather:** Schedule maintenance and fleet reductions in spring, and run campaigns in summer and winter. Consider a rain-day discount or weather alert, since rainy days lose about 63% of demand.\n"
    )