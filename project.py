import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI DASAR & TEMA ---
st.set_page_config(
    page_title="Solar Eco-Cost Analyzer Pro",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE CSS CUSTOM (Mempercantik UI) ---
st.markdown("""
<style>
    .main { background-color: #f9fbfd; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #edf2f7;
    }
    .hero-container {
        background: linear-gradient(135deg, #1a365d 0%, #2a4365 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .provinsi-card {
        background-color: #ebf8ff;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 6px solid #3182ce;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. KONSTANTA SISTEM ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv'
WP_CHOICES = [300, 350, 400, 450, 500, 550] # Dibatasi sampai 550Wp
MAX_MODUL = 50 # Dibatasi sampai 50 modul
BIAYA_PER_WP = 15000 
INFLASI_LISTRIK = 0.05
TAHUN_ANALISIS = 15

# --- 4. FUNGSI PENGOLAH DATA ---
def format_rp(angka):
    if angka >= 1e9: return f"Rp {angka/1e9:,.2f} Milyar"
    if angka >= 1e6: return f"Rp {angka/1e6:,.1f} Juta"
    return f"Rp {angka:,.0f}"

@st.cache_data
def get_clean_data(path):
    try:
        df = pd.read_csv(path, sep=None, engine='python')
        # Pembersihan otomatis kolom
        if df.columns[0].lower() in ['no', 'no.']: df = df.drop(df.columns[0], axis=1)
        df.columns = ['Provinsi', 'Radiasi', 'Emisi']
        # Pastikan angka bersih dari karakter string
        for col in ['Radiasi', 'Emisi']:
            if df[col].dtype == 'O':
                df[col] = df[col].str.replace(',', '.').str.extract(r'(\d+\.?\d*)').astype(float)
        return df.dropna()
    except Exception as e:
        st.error(f"Gagal memuat database: {e}")
        return pd.DataFrame()

# --- 5. LOGIKA APLIKASI UTAMA ---
df_solar = get_clean_data(FILE_DATA)

if df_solar.empty:
    st.warning("Database tidak ditemukan. Pastikan file 'produksi_emisi_provinsi.csv' ada di folder yang sama.")
    st.stop()

# --- HEADER SECTION ---
st.markdown("""
<div class="hero-container">
    <h1 style='color: white; margin: 0;'>☀️ Solar Eco-Cost Analyzer</h1>
    <p style='font-size: 1.2rem; opacity: 0.9;'>Optimalkan Penghematan Listrik & Reduksi Emisi Karbon Anda</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR & INPUT ---
with st.sidebar:
    st.header("👤 Konfigurasi Pengguna")
    provinsi = st.selectbox("Pilih Provinsi Anda:", df_solar['Provinsi'].unique())
    tagihan_bln = st.number_input("Tagihan Listrik (Rp/Bulan):", min_value=50000, value=500000, step=50000)
    
    st.divider()
    st.header("🔌 Spesifikasi Panel")
    wp_val = st.select_slider("Kapasitas per Modul (Wp):", options=WP_CHOICES, value=550)
    jml_modul = st.number_input("Jumlah Modul PV (Maks 50):", min_value=1, max_value=MAX_MODUL, value=4)
    
    # Detail teknis instan di sidebar
    total_kwp = (wp_val * jml_modul) / 1000
    st.success(f"Total Kapasitas: **{total_kwp:.2f} kWp**")

# --- DATA LOOKUP ---
data_prov = df_solar[df_solar['Provinsi'] == provinsi].iloc[0]
val_radiasi = data_prov['Radiasi']
val_emisi = data_prov['Emisi']

# --- PERHITUNGAN INTI ---
konsumsi_kwh_bln = tagihan_bln / TARIF_PLN
produksi_kwh_bln = val_radiasi * total_kwp * 30
hemat_rp_bln = produksi_kwh_bln * TARIF_PLN
skor_mandiri = min((produksi_kwh_bln / konsumsi_kwh_bln) * 100, 100)
tagihan_setelah_pv = max(tagihan_bln - hemat_rp_bln, 0)

biaya_investasi = (wp_val * jml_modul) * BIAYA_PER_WP
emisi_dicegah_bln = produksi_kwh_bln * val_emisi

# Kalkulasi ROI/Payback
list_tanpa_pv = []
list_dengan_pv = [biaya_investasi]
total_tanpa = 0
total_dengan = biaya_investasi
tahun_balik_modal = "Belum Tercapai"

for thn in range(1, TAHUN_ANALISIS + 1):
    inflasi = (1 + INFLASI_LISTRIK)**thn
    total_tanpa += (tagihan_bln * 12) * inflasi
    total_dengan += (tagihan_setelah_pv * 12) * inflasi
    list_tanpa_pv.append(total_tanpa)
    list_dengan_pv.append(total_dengan)
    if total_dengan <= total_tanpa and tahun_balik_modal == "Belum Tercapai":
        tahun_balik_modal = f"{thn} Tahun"

# --- TAMPILAN DASHBOARD ---
col_main, col_info = st.columns([2.5, 1])

with col_main:
    # Row 1: Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Penghematan/Bulan", format_rp(hemat_rp_bln))
    m2.metric("🌱 Reduksi CO2/Bulan", f"{emisi_dicegah_bln:.2f} kg")
    m3.metric("⏳ Masa Balik Modal", tahun_balik_modal)
    
    # Row 2: Tabs
    t1, t2, t3 = st.tabs(["📊 Analisis Grafik", "🌳 Dampak Lingkungan", "📑 Detail Biaya"])
    
    with t1:
        st.subheader("Proyeksi Pengeluaran Kumulatif (15 Tahun)")
        df_lirik = pd.DataFrame({
            'Tahun': range(1, TAHUN_ANALISIS + 1),
            'Tanpa PV': list_tanpa_pv,
            'Dengan PV': list_dengan_pv[1:]
        })
        fig_lirik = px.line(df_lirik, x='Tahun', y=['Tanpa PV', 'Dengan PV'], 
                             markers=True, color_discrete_sequence=['#e53e3e', '#38a169'])
        fig_lirik.update_layout(yaxis_title="Rupiah", plot_bgcolor='white')
        st.plotly_chart(fig_lirik, use_container_width=True)

    with t2:
        c_don, c_txt = st.columns([1, 1])
        with c_don:
            # Donut Chart Modern
            emisi_total_awal = konsumsi_kwh_bln * val_emisi
            fig_don = go.Figure(data=[go.Pie(
                labels=['Emisi Berhasil Dicegah', 'Sisa Emisi Grid'],
                values=[emisi_dicegah_bln, max(emisi_total_awal - emisi_dicegah_bln, 0)],
                hole=.6,
                marker_colors=['#48bb78', '#edf2f7']
            )])
            fig_don.update_layout(showlegend=False, annotations=[dict(text=f"{skor_mandiri:.0f}%", x=0.5, y=0.5, font_size=30, showarrow=False, font_color='#2f855a')])
            st.plotly_chart(fig_don, use_container_width=True)
        with c_txt:
            st.markdown(f"### Kemandirian Energi: **{skor_mandiri:.1f}%**")
            st.write(f"Sistem Anda mampu mencegah emisi sebesar **{emisi_dicegah_bln:.2f} kg CO2** setiap bulan.")
            st.info(f"Ini setara dengan menanam **{int(emisi_dicegah_bln/20)} pohon dewasa** per bulan!")

    with t3:
        data_tabel = {
            "Deskripsi": ["Investasi Awal", "Kapasitas Terpasang", "Estimasi Produksi", "Total Hemat 15 Thn"],
            "Nilai": [format_rp(biaya_investasi), f"{total_kwp:.2f} kWp", f"{produksi_kwh_bln:.2f} kWh/Bulan", format_rp(hemat_rp_bln * 12 * 15)]
        }
        st.table(pd.DataFrame(data_tabel))

with col_info:
    st.markdown(f"""
    <div class="provinsi-card">
        <h3 style='margin-top:0;'>📍 Detail Wilayah</h3>
        <p><b>Provinsi:</b><br>{provinsi}</p>
        <hr>
        <p>☀️ <b>PV Out (Potensi):</b><br>{val_radiasi} kWh/kWp/hari</p>
        <hr>
        <p>🏭 <b>Faktor Emisi:</b><br>{val_emisi} kg CO2/kWh</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning(f"**Info:** Perhitungan menggunakan asumsi kenaikan tarif listrik {INFLASI_LISTRIK*100}% per tahun.")