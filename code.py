import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# ================================
# CONFIG STREAMLIT
# ================================
st.set_page_config(
    page_title="Analisis Energi Surya & Angin – Cibodas",
    layout="wide"
)

st.title("🔎 Analisis Potensi Energi Surya dan Angin – Desa Cibodas")
st.write("Aplikasi ini melakukan analisis data NASA POWER (GHI & Wind Speed).")

# ================================
# 1) FILE UPLOADER
# ================================
st.header("📂 Upload File NASA POWER")
uploaded_file = st.file_uploader("Upload file CSV NASA POWER (misal: Cibodas.csv)", type=["csv"])

if uploaded_file is not None:
    # ================================
    # 2) LOAD DATA
    # ================================
    df = pd.read_csv(uploaded_file, skiprows=11)

    st.subheader("📌 Kolom Terbaca")
    st.write(list(df.columns))

    # ================================
    # 3) DATA CLEANING
    # ================================
    df.replace(-999.0, np.nan, inplace=True)
    df.dropna(inplace=True)

    df[['YEAR', 'MO', 'DY', 'HR']] = df[['YEAR', 'MO', 'DY', 'HR']].astype(int)

    # ================================
    # 4) KONVERSI DATETIME WIB
    # ================================
    df['Datetime'] = pd.to_datetime(
        df['YEAR'].astype(str) + "-" +
        df['MO'].astype(str).str.zfill(2) + "-" +
        df['DY'].astype(str).str.zfill(2) + " " +
        df['HR'].astype(str) + ":00"
    )

    df = df.set_index('Datetime')
    df.index = df.index.tz_localize("Asia/Jakarta")

    st.success("⏱ Zona waktu berhasil diset ke Asia/Jakarta (WIB).")

    # ================================
    # 5) ENERGY ANALYSIS (DAILY)
    # ================================
    ghi_daily = df['ALLSKY_SFC_SW_DWN'].resample("D").sum() / 1000
    ghi_daily.name = "GHI_kWh_m2_day"

    wind_daily = df['WS10M'].resample("D").mean()
    wind_daily.name = "Wind_Speed_m_s"

    energy_stats = pd.concat([ghi_daily, wind_daily], axis=1).dropna()

    # ================================
    # 6) VISUALIZATION
    # ================================
    st.header("📊 Visualisasi Data Energi")

    # ——— Plot GHI & Wind Speed ———
    fig, ax = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    fig.suptitle("Analisis Potensi Energi Desa Cibodas (WIB)", fontsize=16, weight='bold')

    ax[0].plot(energy_stats.index, energy_stats['GHI_kWh_m2_day'], linewidth=1.3, color="orange")
    ax[0].set_ylabel("GHI (kWh/m²/hari)")
    ax[0].set_title("Potensi Energi Surya")

    ax[1].plot(energy_stats.index, energy_stats['Wind_Speed_m_s'], linewidth=1.3, color="blue")
    ax[1].set_ylabel("Kecepatan Angin (m/s)")
    ax[1].set_title("Potensi Energi Angin")
    ax[1].set_xlabel("Tanggal (WIB)")

    st.pyplot(fig)

    # ================================
    # 7) Statistik
    # ================================
    st.subheader("📈 Statistik Harian")
    st.dataframe(energy_stats.describe())

    st.write(f"☀️ **Rata-rata GHI Tahunan:** {energy_stats['GHI_kWh_m2_day'].mean():.2f} kWh/m²/hari")
    st.write(f"💨 **Rata-rata Kecepatan Angin Tahunan:** {energy_stats['Wind_Speed_m_s'].mean():.2f} m/s")

    # ================================
    # 8) VISUALISASI BARU (Area Chart + Boxplot)
    # ================================
    st.header("📊 Visualisasi Tambahan")

    # Tambahkan kolom bulan
    energy_stats['Month'] = energy_stats.index.month_name(locale='id_ID')

    # ——— Area Chart GHI ———
    fig1 = plt.figure(figsize=(15, 5))
    plt.fill_between(energy_stats.index, energy_stats['GHI_kWh_m2_day'], alpha=0.4, color='orange')
    plt.plot(energy_stats.index, energy_stats['GHI_kWh_m2_day'], color='darkorange', linewidth=1.5)
    plt.title("☀️ Tren Harian Potensi Energi Surya (GHI)", fontsize=14, weight='bold')
    plt.ylabel("GHI (kWh/m²/hari)")
    plt.grid(alpha=0.3)
    st.pyplot(fig1)

    # ——— Boxplot Wind Speed per Bulan ———
    fig2 = plt.figure(figsize=(15, 5))
    sns.boxplot(data=energy_stats, x='Month', y='Wind_Speed_m_s', palette="Blues")
    plt.title("💨 Distribusi Kecepatan Angin Berdasarkan Bulan", fontsize=14, weight='bold')
    plt.ylabel("Kecepatan Angin (m/s)")
    plt.grid(axis="y", linestyle='--', alpha=0.3)
    st.pyplot(fig2)

else:
    st.info("Silakan upload file CSV untuk memulai analisis.")
