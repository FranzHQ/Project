# -*- coding: utf-8 -*-
"""
Created on Fri Dec 12 09:19:36 2025

@author: acer
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Eco-Cost Analyzer", layout="wide")

# --- KONSTANTA PROYEK ---
TARIF_PLN = 1400  # Rupiah per kWh (Tarif non-subsidi acuan)
FILE_DATA = 'produksi_emisi_provinsi.csv' # Nama file CSV Anda

# --- FUNGSI LOAD DATA (KODE ROBUST) ---
@st.cache_data
def load_data(file_path):
    """Memuat data, mencoba kedua delimiter, dan mengonversi format desimal."""
    try:
        # 1. Coba baca dengan delimiter KOMA (,)
        df = pd.read_csv(file_path, delimiter=',')
        
        # 2. Jika gagal, coba delimiter TITIK KOMA (;)
        if len(df.columns) <= 2:
            df = pd.read_csv(file_path, delimiter=';')

        # Penamaan ulang kolom
        df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        
        # 3. KOREKSI FORMAT ANGKA (Mengubah koma desimal ke titik desimal)
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object: 
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
            
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(inplace=True) 
        
        if df.empty:
            st.error("Data tidak valid. Pastikan kolom data Anda terisi angka.")
            
        return df
        
    except FileNotFoundError:
        st.error(f"File data tidak ditemukan: {file_path}. Pastikan nama file sudah benar.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fatal saat memproses data: {e}. Periksa kembali struktur data Anda.")
        return pd.DataFrame()

# Panggil fungsi untuk memuat data
data_solar = load_data(FILE_DATA)

# Jika data gagal dimuat, hentikan aplikasi
if data_solar.empty:
    st.stop()


# --- BAGIAN HEADER & JUDUL ---
st.title("☀️ Analisis Penghematan Biaya dan Penekanan Emisi Ketika Menggunakan PV Rumahan")
st.markdown("""
Aplikasi ini membantu Anda menghitung potensi **penghematan biaya listrik (Rp)** dan **dampak lingkungan (emisi CO2)**
dengan beralih ke energi surya mandiri, disesuaikan dengan **lokasi provinsi** dan **konsumsi listrik** Anda.
""")
st.divider()

# --- BAGIAN 1: INPUT USER (Menggunakan Session State untuk Interaktivitas) ---

# Inisialisasi Session State (untuk memastikan nilai default terbaca)
if 'tagihan_bulanan' not in st.session_state:
    st.session_state['tagihan_bulanan'] = 500000

if 'kapasitas_pv' not in st.session_state:
    st.session_state['kapasitas_pv'] = 2.0


st.subheader("⚙️ Data Input dan Instalasi")
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    # INPUT 1: Lokasi (Provinsi)
    provinsi_pilihan = st.selectbox(
        "Pilih Lokasi (Provinsi):", 
        data_solar['Provinsi'].tolist(),
        key='provinsi_key' 
    )

with col_input2:
    # INPUT 2: Konsumsi (Uang)
    st.number_input(
        "Tagihan Listrik per Bulan (Rp):", 
        min_value=10000, 
        value=st.session_state['tagihan_bulanan'], 
        step=50000,
        key='tagihan_bulanan' # Nilai input terikat ke session state
    )
    # Ambil nilai yang sudah diupdate dari session state
    tagihan_bulanan = st.session_state['tagihan_bulanan']

with col_input3:
    # INPUT 3: Kapasitas PV (kWp)
    st.slider(
        "Kapasitas Panel Surya yang Dipasang (kWp):", 
        1.0, 
        10.0, 
        value=st.session_state['kapasitas_pv'], 
        step=0.5,
        key='kapasitas_pv' # Nilai input terikat ke session state
    )
    # Ambil nilai yang sudah diupdate dari session state
    kapasitas_pv = st.session_state['kapasitas_pv']


# --- BAGIAN 2: PROSES ALGORITMA ---

# A. Lookup Data Spesifik Lokasi
data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
radiasi_harian = data_lokasi['Produksi_Harian_kWh']
faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']

# B. Perhitungan Konsumsi & Produksi
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv
produksi_pv_bulanan = produksi_pv_harian * 30

# C. Hitung Output Kritis
# 1. Penghematan Biaya (Rp)
penghematan_rp = produksi_pv_bulanan * TARIF_PLN

# 2. Pengurangan Emisi (kg CO2)
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 

# 3. Skor Kemandirian Energi (%)
skor_kemandirian = (produksi_pv_bulanan / konsumsi_kwh) * 100
skor_kemandirian = min(skor_kemandirian, 100) 

# D. Hitung Tagihan Akhir
tagihan_baru = tagihan_bulanan - penghematan_rp
if tagihan_baru < 0: tagihan_baru = 0

# E. VARIABEL KHUSUS UNTUK GRAFIK DONUT (Fix Negative Value Error)
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- BAGIAN 3: OUTPUT DASHBOARD ---

st.divider()
st.header(f"📊 Hasil Analisis Dampak untuk {provinsi_pilihan}")

# --- 3 METRIK UTAMA (Scorecards - Harus dijamin terupdate) ---
m1, m2, m3 = st.columns(3)

# 1. HEMAT BIAYA
with m1:
    penghematan_tampil = int(penghematan_rp) 
    tagihan_akhir_tampil = int(tagihan_baru)
    
    st.metric(
        "💰 Total Hemat Biaya (Rp/Bulan)", 
        f"Rp {penghematan_tampil:,.0f}", 
        delta=f"Tagihan Akhir: Rp {tagihan_akhir_tampil:,.0f}"
    )

# 2. EMISI DICEGAH
with m2:
    emisi_tampil = emisi_dicegah_total
    pohon_setara = (emisi_tampil * 12) / 22 
    
    st.metric(
        "🌱 Emisi CO₂ Dicegah (kg/Bulan)", 
        f"{emisi_tampil:.1f} kg", 
        help=f"Setara dengan menanam {pohon_setara:.0f} pohon per tahun."
    )

# 3. SKOR KEMANDIRIAN
with m3:
    kemandirian_tampil = skor_kemandirian
    
    st.metric(
        "⚡ Skor Kemandirian Energi", 
        f"{kemandirian_tampil:.1f}%", 
        help="Persentase kebutuhan listrik bulanan yang dipenuhi PV Anda."
    )

st.write("") 

# --- BAGIAN 4: VISUALISASI GRAFIK (Perbaikan Keterbacaan) ---

tab1, tab2, tab3 = st.tabs(["📉 Analisis Biaya & Kemandirian", "🌍 Analisis Lingkungan (Emisi)", "ℹ️ Detail Teknis"])

# GRAFIK 1: Analisis Biaya dan Kemandirian (Stacked Bar Chart)
with tab1:
    st.subheader("Komparasi Biaya Listrik Bulanan")
    
    
    data_biaya = pd.DataFrame({
        'Kategori': ['Tagihan Awal', 'Tagihan Akhir (Dampak PV)'],
        'Dibayar ke PLN': [tagihan_bulanan, tagihan_baru],
        'Disuplai PV': [0, penghematan_rp]
    })
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Bar Tagihan Awal
    bar_awal = ax.bar(data_biaya['Kategori'][0], data_biaya['Dibayar ke PLN'][0], color='#cccccc', label='Total Biaya Awal')
    
    # Stacked Bar Tagihan Akhir
    bar_pln = ax.bar(data_biaya['Kategori'][1], data_biaya['Dibayar ke PLN'][1], color='#e74c3c', label='Masih Dibayar (PLN)')
    bar_pv = ax.bar(data_biaya['Kategori'][1], data_biaya['Disuplai PV'][1], bottom=data_biaya['Dibayar ke PLN'][1], color='#2ecc71', label='Disuplai PV (Hemat)')
    
    # Menambahkan Label Angka di Atas Bar (Agar mudah dibaca orang awam)
    ax.bar_label(bar_awal, fmt='Rp %.0f', padding=5)
    total_akhir = tagihan_baru + penghematan_rp
    ax.text(data_biaya['Kategori'][1], total_akhir, f'Rp {total_akhir:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Setting
    ax.set_title('Perbandingan Struktur Biaya Listrik (Rp)', fontsize=14)
    ax.set_ylabel('Rupiah (Rp)', fontsize=12)
    ax.ticklabel_format(style='plain', axis='y') 
    plt.legend(loc='upper left')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    st.pyplot(fig)
    st.progress(int(skor_kemandirian))
    st.caption(f"Skor Kemandirian Energi Anda adalah **{skor_kemandirian:.1f}%**.")

# GRAFIK 2: Analisis Emisi (Donut Chart)
with tab2:
    st.subheader("Porsi Pengurangan Jejak Karbon")
    
    
    labels_donut = ['Emisi yang Dicegah', 'Emisi yang Tersisa']
    sizes_donut = [emisi_dicegah_grafik, emisi_tersisa_pln] 
    colors_donut = ['#3498db', '#f1c40f']

    fig2, ax2 = plt.subplots(figsize=(6, 6))
    
    # Menampilkan Persen dan Kilogram di label
    wedges, texts, autotexts = ax2.pie(
        sizes_donut, 
        labels=labels_donut, 
        colors=colors_donut, 
        autopct=lambda p: '{:.1f}%\n({:.1f} kg)'.format(p, p * emisi_awal_total / 100) if p > 0 else '', # Hanya tampilkan jika porsi > 0
        startangle=90, 
        pctdistance=0.75, 
        wedgeprops=dict(width=0.4)
    )
    
    # Draw circle for donut effect
    centre_circle = plt.Circle((0,0),0.60,fc='white')
    fig2.gca().add_artist(centre_circle)

    ax2.set_title(f'Total Jejak Karbon Awal: {emisi_awal_total:.1f} kg CO₂/Bulan', fontsize=14)
    st.pyplot(fig2)
    
    st.info(f"Dengan PV, Anda berhasil mengurangi emisi sebesar **{emisi_dicegah_grafik:.1f} kg CO₂** dari konsumsi rumah Anda.")

# TAB 3: Detail Teknis
with tab3:
    st.subheader("Data Teknis dan Angka Kunci")
    st.table(pd.DataFrame({
        "Deskripsi": [
            "Konsumsi Energi Total Rumah",
            "Produksi Energi dari PV",
            "Faktor Emisi Lokal",
            "Radiasi Harian Lokal"
        ],
        "Nilai": [
            f"{konsumsi_kwh:.2f} kWh/bulan",
            f"{produksi_pv_bulanan:.2f} kWh/bulan",
            f"{faktor_emisi_lokal:.2f} kg CO₂/kWh",
            f"{radiasi_harian:.2f} kWh/hari"
        ]
    }))