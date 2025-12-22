import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Eco-Cost Analyzer",
    layout="wide",
    page_icon="☀️"
)

# --- 2. CUSTOM CSS (FIX FONT HILANG & UI MODERN) ---
# PERBAIKAN UTAMA: Memaksa warna teks secara spesifik agar tidak bentrok dengan Dark Mode
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Poppins:wght@600;700&display=swap');

    /* 1. RESET GLOBAL & BACKGROUND (PAKSA LIGHT MODE) */
    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important; /* Abu-abu muda bersih */
    }
    
    /* 2. PAKSA SEMUA TEKS JADI GELAP (Agar terlihat di background terang) */
    html, body, p, div, span, label, li {
        font-family: 'Inter', sans-serif;
        color: #1e293b !important; /* Slate Dark */
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif;
        color: #0f172a !important; /* Hitam Pekat */
        font-weight: 700;
    }

    /* 3. HERO BANNER (PENGECUALIAN WARNA TEKS) */
    /* Karena background banner gelap, teks di sini WAJIB PUTIH */
    .hero-banner {
        background-image: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 60px 40px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .hero-banner h1 {
        color: #ffffff !important; /* Override jadi Putih */
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }
    .hero-banner p {
        color: #e2e8f0 !important; /* Override jadi Putih Abu */
        font-size: 1.1rem;
        max-width: 800px;
        margin: 0 auto;
    }

    /* 4. CARD CONTAINER (KOTAK PUTIH) */
    .card-style {
        background-color: #ffffff !important;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }

    /* 5. INPUT FIELDS (FIX DARK MODE ISSUE) */
    /* Memaksa background input jadi putih dan teks jadi hitam */
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput div[data-baseweb="input"] > div {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
        color: #1e293b !important;
    }
    .stSelectbox div[data-baseweb="select"] span {
        color: #1e293b !important;
    }
    input {
        color: #1e293b !important;
    }
    label {
        color: #334155 !important;
        font-weight: 600 !important;
    }

    /* 6. METRIC BOX */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b !important; /* Label Abu */
        font-size: 0.9rem;
    }
    div[data-testid="stMetricValue"] {
        color: #0f172a !important; /* Nilai Hitam */
        font-size: 1.8rem;
    }

    /* 7. INFO BOX */
    .info-box {
        padding: 15px;
        background-color: #eff6ff !important;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        margin-top: 15px;
    }
    .info-box, .info-box b, .info-box span {
        color: #1e3a8a !important; /* Teks Biru Tua */
    }

    /* 8. TABLE FIX */
    .styled-table { width: 100%; border-collapse: collapse; }
    .styled-table th { background-color: #f1f5f9; color: #334155 !important; padding: 12px; text-align: left; }
    .styled-table td { border-bottom: 1px solid #e2e8f0; color: #1e293b !important; padding: 12px; }

    /* HIDE MENU */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# --- 3. KONSTANTA PROYEK ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
WP_CHOICES = [300, 350, 400, 450, 500, 550] 
MIN_PV_MODULES = 1 
MAX_PV_MODULES = 50 
TAHUN_ANALISIS = 15 
ASUMSI_INFLASI_LISTRIK = 0.05 
BIAYA_AWAL_PV_PER_Wp = 15000 

# --- 4. FUNGSI UTILITY ---
def format_rupiah(x):
    if x >= 1e9: return f"Rp {x/1e9:,.2f} M"
    if x >= 1e6: return f"Rp {x/1e6:,.1f} Jt"
    return f"Rp {x:,.0f}"

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, delimiter=',')
        if len(df.columns) <= 2: df = pd.read_csv(file_path, delimiter=';')
        if df.columns[0].lower() in ['no', 'no.']: df = df.iloc[:, 1:].copy() 
        df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object: 
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True).str.replace(' kWh/kWp', '', regex=False) 
            df[col] = pd.to_numeric(df[col], errors='coerce') 
        df.dropna(inplace=True) 
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

data_solar = load_data(FILE_DATA)
if data_solar.empty: st.stop()


# --- 5. HEADER (JUDUL ASLI) ---
st.markdown("""
    <div class="hero-banner">
        <h1>☀️ Analisis Penghematan Biaya dan Pengurangan Emisi Ketika Menggunakan PV Rumahan</h1>
        <p>Aplikasi ini membantu Anda menghitung potensi <b>penghematan biaya listrik (Rp)</b> dan <b>dampak lingkungan (emisi CO2)</b> dengan beralih ke energi surya mandiri.</p>
    </div>
""", unsafe_allow_html=True)


# --- 6. BAGIAN INPUT USER ---
if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4 

st.markdown('<div class="card-style">', unsafe_allow_html=True)
st.subheader("⚙️ Data Input dan Instalasi")
st.write("---")

col_input1, col_input2, col_input3 = st.columns(3, gap="medium")

with col_input1:
    provinsi_pilihan = st.selectbox("Pilih Lokasi (Provinsi):", data_solar['Provinsi'].tolist(), key='provinsi_key')
    data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
    radiasi_harian = data_lokasi['Produksi_Harian_kWh']
    faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']
    
    st.markdown(f"""
    <div class="info-box">
        <b>Data Wilayah: {provinsi_pilihan}</b><br>
        ☀️ PV Out: {radiasi_harian} kWh/kWp<br>
        🏭 Emisi Grid: {faktor_emisi_lokal} kg/kWh
    </div>
    """, unsafe_allow_html=True)

with col_input2:
    tagihan_input = st.number_input("Tagihan Listrik per Bulan (Rp):", min_value=10000, value=st.session_state['tagihan_bulanan'], step=50000, key='tagihan_bulanan')
    tagihan_bulanan = tagihan_input 

with col_input3:
    wp_pilihan = st.selectbox("Pilih Kapasitas 1 Modul PV (Watt Peak/Wp):", WP_CHOICES, index=WP_CHOICES.index(550), key='pv_module_watt')
    jumlah_modul = st.number_input("Jumlah Modul PV yang Dipasang:", min_value=MIN_PV_MODULES, max_value=MAX_PV_MODULES, value=st.session_state['pv_module_count'], step=1, key='pv_module_count')
    
    kapasitas_pv_wp = wp_pilihan * jumlah_modul
    kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
    st.info(f"Kapasitas Total PV Anda: **{kapasitas_pv_kwp:.2f} kWp**")

st.markdown('</div>', unsafe_allow_html=True)


# --- BAGIAN 2: PROSES ALGORITMA (ASLI) ---
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 
skor_kemandirian = (produksi_pv_bulanan / konsumsi_kwh) * 100
skor_kemandirian = min(skor_kemandirian, 100) 
tagihan_baru = tagihan_bulanan - penghematan_rp
if tagihan_baru < 0: tagihan_baru = 0

biaya_instalasi_pv = kapasitas_pv_wp * BIAYA_AWAL_PV_PER_Wp
biaya_kumulatif_tanpa_pv = []
biaya_kumulatif_dengan_pv = []

tagihan_bulanan_saat_ini = tagihan_bulanan
tagihan_baru_saat_ini = tagihan_baru

total_biaya_tanpa_pv = 0
total_biaya_dengan_pv = biaya_instalasi_pv 

payback_tahun = TAHUN_ANALISIS + 1 

for tahun in range(1, TAHUN_ANALISIS + 1):
    tagihan_bulanan_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)
    tagihan_baru_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)
    total_biaya_tanpa_pv += tagihan_bulanan_saat_ini * 12
    total_biaya_dengan_pv += tagihan_baru_saat_ini * 12
    biaya_kumulatif_tanpa_pv.append(total_biaya_tanpa_pv)
    biaya_kumulatif_dengan_pv.append(total_biaya_dengan_pv)
    if total_biaya_dengan_pv <= total_biaya_tanpa_pv and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = tahun
    
emisi_total_ton = emisi_dicegah_total * 12 * TAHUN_ANALISIS / 1000 
df_proyeksi = pd.DataFrame({'Tahun': range(1, TAHUN_ANALISIS + 1), 'Tanpa PV': biaya_kumulatif_tanpa_pv, 'Dengan PV': biaya_kumulatif_dengan_pv})
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- BAGIAN 3: OUTPUT DASHBOARD ---
st.divider()
st.header(f"📊 Hasil Analisis Dampak untuk {provinsi_pilihan}")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("💰 Hemat Biaya Bulanan", f"{format_rupiah(int(penghematan_rp))}", delta=f"Tagihan Akhir: {format_rupiah(int(tagihan_baru))}")
with m2:
    payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"
    st.metric("⏳ Masa Balik Modal", payback_display, help=f"Total biaya sistem PV adalah {format_rupiah(biaya_instalasi_pv)}")
with m3:
    st.metric("🌱 Emisi CO₂ Dicegah (Bln)", f"{emisi_dicegah_total:.1f} kg", help=f"Total Emisi Dicegah selama {TAHUN_ANALISIS} tahun: {emisi_total_ton:.1f} ton CO₂")
with m4:
    st.metric("⚡ Skor Kemandirian Energi", f"{skor_kemandirian:.1f}%", help="Persentase kebutuhan listrik bulanan yang dipenuhi PV Anda.")

st.write("") 

# --- BAGIAN 4: VISUALISASI ---
tab1, tab2, tab3, tab4 = st.tabs(["📉 Analisis Biaya Bulanan", "📈 Proyeksi Jangka Panjang", "🌍 Analisis Lingkungan (Emisi)", "ℹ️ Detail Teknis"])

COLOR_MAIN = "#10b981"
COLOR_GRAY = "#94a3b8"

with tab1:
    col_gr, col_txt = st.columns([2, 1])
    with col_gr:
        st.subheader("Komparasi Tagihan Listrik Bulanan")
        data_biaya = pd.DataFrame({'Kategori': ['Tagihan Awal', 'Tagihan Akhir'], 'Rupiah': [tagihan_bulanan, tagihan_baru], 'Teks': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]})
        fig_bar = px.bar(data_biaya, x='Kategori', y='Rupiah', text='Teks', color='Kategori', color_discrete_map={'Tagihan Awal': COLOR_GRAY, 'Tagihan Akhir': COLOR_MAIN})
        fig_bar.update_layout(yaxis_title="", xaxis_title="", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        if penghematan_rp > 0 and tagihan_baru < tagihan_bulanan:
            fig_bar.add_annotation(x=0.5, y=(tagihan_bulanan + tagihan_baru)/2, text=f"Hemat: {format_rupiah(penghematan_rp)}", showarrow=False, font=dict(size=14, color="#15803d"), bgcolor="#dcfce7", borderpad=4)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_txt:
        st.write("")
        st.markdown("#### Status Kemandirian")
        st.info(f"Sistem PV Anda menyuplai **{skor_kemandirian:.1f}%** dari total kebutuhan listrik.")
        st.progress(int(skor_kemandirian))

with tab2:
    st.subheader(f"Proyeksi Biaya Listrik Kumulatif Selama {TAHUN_ANALISIS} Tahun")
    df_plot_longterm = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total Biaya Kumulatif')
    fig_proj = px.line(df_plot_longterm, x='Tahun', y='Total Biaya Kumulatif', color='Skenario', color_discrete_map={'Tanpa PV': '#ef4444', 'Dengan PV': COLOR_MAIN}, title='Perbandingan Biaya Kumulatif Jangka Panjang', markers=True)
    fig_proj.update_layout(yaxis=dict(tickformat=",.0f", tickprefix="Rp "), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1))
    if payback_tahun <= TAHUN_ANALISIS:
        payback_cost = df_proyeksi[df_proyeksi['Tahun'] == payback_tahun]['Dengan PV'].iloc[0]
        fig_proj.add_scatter(x=[payback_tahun], y=[payback_cost], mode='markers', marker=dict(size=10, color='#3b82f6'), name='Masa Balik Modal', showlegend=False)
    st.plotly_chart(fig_proj, use_container_width=True)
    st.markdown(f"* **Asumsi:** Kenaikan tarif listrik sebesar {ASUMSI_INFLASI_LISTRIK*100}% per tahun.")

with tab3:
    st.subheader("Porsi Pengurangan Jejak Karbon (CO₂)")
    c_don, c_txt = st.columns([1.5, 1])
    with c_don:
        labels = ['Dicegah (PV)', 'Sisa (PLN)']
        values = [emisi_dicegah_grafik, emisi_tersisa_pln]
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7, marker_colors=[COLOR_MAIN, '#cbd5e1'], hoverinfo="label+value+percent", textinfo='percent')])
        fig_donut.update_layout(annotations=[dict(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=20, showarrow=False)], showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)
    with c_txt:
        st.info(f"Dengan PV, Anda berhasil mengurangi emisi sebesar **{emisi_dicegah_grafik:.1f} kg CO₂** dari konsumsi rumah Anda.")
        st.markdown(f"**Setara dengan:**\n\n🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**\n\n🚗 Menghapus **{int(emisi_dicegah_total*5)} km** perjalanan mobil")

with tab4:
    col_tech1, col_tech2 = st.columns(2)
    def create_custom_table(title, data_dict):
        rows = "".join([f"<tr><td>{k}</td><td><strong>{v}</strong></td></tr>" for k, v in data_dict.items()])
        return f"""<div style="background:white; padding:15px; border-radius:10px; border:1px solid #e2e8f0; margin-bottom:15px;"><h4 style="margin-bottom:10px; font-family:'Poppins'; color:#334155;">{title}</h4><table class="styled-table">{rows}</table></div>"""
    
    with col_tech1:
        st.markdown(create_custom_table("⚙️ Sistem & Energi", {
            "Kapasitas PV Total": f"{kapasitas_pv_kwp:.2f} kWp",
            "Jumlah Modul": f"{jumlah_modul} unit",
            "Kapasitas 1 Modul": f"{wp_pilihan} Wp",
            "Produksi Energi Bulanan": f"{produksi_pv_bulanan:.2f} kWh"
        }), unsafe_allow_html=True)
    
    with col_tech2:
        st.markdown(create_custom_table("💸 Finansial & Dampak", {
            "Biaya Instalasi Awal": format_rupiah(biaya_instalasi_pv),
            "Tagihan Bulanan Baru": format_rupiah(tagihan_baru),
            "Penghematan Bulanan": format_rupiah(penghematan_rp),
            "Masa Balik Modal": payback_display,
            f"Total Emisi Dicegah ({TAHUN_ANALISIS} Thn)": f"{emisi_total_ton:.1f} ton CO₂"
        }), unsafe_allow_html=True)