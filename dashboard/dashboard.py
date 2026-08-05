import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

#create dataframe
def create_daily_avg_users(df):
  daily_avg_users = df[['casual', 'registered', 'total_user_count']].mean().reset_index()
  daily_avg_users.columns = ["Jenis User", "Rata-rata"]
  daily_avg_users["Jenis User"] = daily_avg_users["Jenis User"].replace({
        "casual": "Non Members",
        "registered": "Members",
        "total_user_count": "Total Users"
    })
  return daily_avg_users

def create_yearly_usage(df):
  yearly_usage = df.groupby('year')['total_user_count'].sum().reset_index()
  yearly_usage["Growth Rate"] = (yearly_usage["total_user_count"].pct_change() * 100)
  yearly_usage.rename(columns={
    'year':'Year',
    'total_user_count':'Total Users'
  }, inplace=True)
  return yearly_usage

def create_yearly_registered(df):
  yearly_registered = df.groupby('year')['registered'].sum().reset_index()
  yearly_registered['Growth Rate'] = (yearly_registered['registered'].pct_change() * 100)
  yearly_registered.rename(columns={
    'year':'Year',
    'registered':'Total Registered Users'
  }, inplace=True)
  return yearly_registered

def create_average_season(df, selected_seasons):
  avg_season = (
        df[df["season"].isin(selected_seasons)]
        .groupby("season", observed=True)["total_user_count"]
        .mean()
        .reset_index()
    )
  avg_season.rename(columns={
    "season":"Season",
    "total_user_count":"Average Users"
  }, inplace=True)

  season_order = ["Spring", "Summer", "Fall", "Winter"]

  avg_season["Season"] = pd.Categorical(
      avg_season["Season"],
      categories=season_order,
      ordered=True
  )

  return avg_season.sort_values("Season")

def create_average_weather(df):
  avg_weather = df.groupby("weather")["total_user_count"].mean().reset_index()

  avg_weather = avg_weather.sort_values(
    by="total_user_count",
    ascending=False
  )

  return avg_weather
   

def create_daily_hour_avg(df):
  daily_hour_avg = df.groupby("hour")["total_user_count"].mean().reset_index()
  daily_hour_avg.rename(columns={
    "hour":"Hour",
    "total_user_count":"Average Users"
  }, inplace=True)
  return daily_hour_avg

#Import Dataset
df_day = pd.read_csv('day_clean.csv')
df_day['date'] = pd.to_datetime(df_day['date'])
df_hour = pd.read_csv('hour_clean.csv')


with st.sidebar:
    st.header("Bike Sharing Analysis")
    st.write("Analisa Data penggunaan Bike Sharing Tahun 2011–2012.")
    season = st.sidebar.multiselect(
       "Seasons",
       options=df_day['season'].unique(),
       default=df_day['season'].unique()
    )

#Header
st.title("Analisa Bike Sharing")

#Visualize Total Rent by Year
st.header("Pertumbuhan Penggunaan Bike Share")
tab1, tab2, tab3 = st.tabs(["Rata-rata User per Hari", "Total User per Tahun", "Pertumbuhan User Terdaftar"])

#Rata-rata User per Hari
with tab1:
  st.subheader("Rata-rata Jumlah User per Hari")
  daily_avg_users = create_daily_avg_users(df_day)

  fig, ax = plt.subplots(figsize=(6,5))

  colors = ["#72BCD4", "#9F9F9F", "#9F9F9F"]

  sns.barplot(
      data=daily_avg_users.sort_values("Rata-rata", ascending=False),
      x="Jenis User",
      y="Rata-rata",
      palette=colors,
      hue="Jenis User",
      legend=False,
      ax=ax
  )

  for container in ax.containers:
    ax.bar_label(
        container,
        fmt="{:,.0f}",
    )
  ax.set_title("Rata-rata Jumlah Bike Share per Hari untuk Setiap Jenis User")
  ax.set_xlabel("")
  ax.set_ylabel("Rata-rata User")
  st.pyplot(fig)

#Total user per tahun
with tab2:
    st.subheader("Total Bike Share per Tahun")
    yearly_usage = create_yearly_usage(df_day)

    fig, ax = plt.subplots(figsize=(6,5))

    sns.barplot(
        data=yearly_usage,
        x="Year",
        y="Total Users",
        color="#9F9F9F",
        errorbar=None,
        ax=ax,
    )

    colors = [
        "#72BCD4" if value == yearly_usage["Total Users"].max() else "#9F9F9F"
        for value in yearly_usage["Total Users"]
    ]
    for patch, color in zip(ax.patches, colors):
        patch.set_facecolor(color)

    for container in ax.containers:
      ax.bar_label(container, labels=yearly_usage["Total Users"].apply(lambda x: f"{x:,.0f}"), label_type='center', color='black', fontsize=12)
      ax.bar_label(container, labels=yearly_usage["Growth Rate"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else ""), label_type='edge', color='black', fontsize=12)

    ax.set_title("Total Bike Share per Tahun")
    ax.set_xlabel("")
    ax.set_ylabel("")

    st.pyplot(fig)

#Pertumbuhan user terdaftar
with tab3:
  st.subheader("Growth Rate User Terdaftar per Tahun")
  yearly_registered = create_yearly_registered(df_day)

  fig, ax = plt.subplots(figsize=(6, 5))

  sns.barplot(
      data=yearly_registered,
      x="Year",
      y="Total Registered Users",
      color="#9F9F9F",
      errorbar=None,
      ax=ax,
  )

  colors = [
      "#72BCD4" if value == yearly_registered["Total Registered Users"].max() else "#9F9F9F"
      for value in yearly_registered["Total Registered Users"]
  ]
  for patch, color in zip(ax.patches, colors):
      patch.set_facecolor(color)

  for container in ax.containers:
    ax.bar_label(container, labels=yearly_registered["Total Registered Users"].apply(lambda x: f"{x:,.0f}"), label_type='center', color='black', fontsize=12)
    ax.bar_label(container, labels=yearly_registered["Growth Rate"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else ""), label_type='edge', color='black', fontsize=12)

  ax.set_title("Growth Rate User Terdaftar per Tahun")
  ax.set_xlabel("")
  ax.set_ylabel("")

  st.pyplot(fig)

#Average Rent by Season & Weather
st.header("Rata-Rata Rental per Musim dan Cuaca ")

col1, col2 = st.columns(2)

#Average Rent by Season
with col1:
  st.subheader("Rata-rata Bike Share per Musim")
  avg_season = create_average_season(df_day, season)

  fig, ax = plt.subplots(figsize=(8,4))

  colors = [
        "#72BCD4" if value == avg_season["Average Users"].max()
        else "#8F8F8F"
        for value in avg_season["Average Users"]
  ]

  sns.barplot(
    data=avg_season,
    x="Season",
    y="Average Users",
    hue="Season",
    palette = colors,
    errorbar=None,
    legend=False,
    ax=ax
  )

  plt.title("Rata-rata Bike Share per Musim", fontsize=16)
  plt.xlabel("")
  plt.ylabel("")
  st.pyplot(fig)

#Average Rent by Weather
with col2:
  st.subheader("Rata-rata Bike Share per Cuaca")
  weather_avg = create_average_weather(df_day)

  fig, ax = plt.subplots(figsize=(8, 4))
  
  sns.barplot(
      data=weather_avg,
      x="total_user_count",
      y="weather",
      hue="weather",
      palette = ["#72BCD4", "#8f8f8f", "#8f8f8f"],
      ax=ax
  )
  plt.title('Rata-rata Bike Share per Cuaca')
  plt.xlabel("")
  plt.ylabel("")
  st.pyplot(fig)

st.header("Rata-Rata Rental per Jam dan Hari Kerja")
#Daily Hours Rent
st.subheader("Rata-rata Rental per Jam")
hour_avg = create_daily_hour_avg(df_hour)

fig, ax = plt.subplots(figsize=(12,4))

sns.barplot(
    data=hour_avg,
    x="Hour",
    y="Average Users",
    errorbar=None,
    ax=ax
)

plt.title("Rata-rata bike share per jam", fontsize=16)
plt.xlabel("")
plt.ylabel("User")
st.pyplot(fig)


#Average hours weekend vs workday
st.subheader("Rental per Jam: Hari Kerja & Hari Libur")
hour_work = (
    df_hour
    .groupby(["hour","workingday"])["total_user_count"]
    .mean()
    .reset_index()
)

fig, ax = plt.subplots(figsize=(12,4))

sns.lineplot(
  data=df_hour,
  x="hour",
  y="total_user_count",
  hue="workingday",
  palette = ["#8f8f8f", "#72BCD4"],
  linewidth=2.5,
  marker="o"
)

plt.title("Rata-rata bike share per jam", fontsize=16)
plt.xlabel("")
plt.ylabel("User")
plt.xticks(range(24))
st.pyplot(fig)