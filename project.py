import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Eco-Cost Analyzer", 
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS (UI MODERN, FONT, & DARK MODE FIX) ---
st.markdown("""
<style>
    /* Import Font Modern: Plus Jakarta Sans */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background Utama: Sedikit abu-abu terang agar elemen putih menonjol */
    .stApp {
        background-color: #f8fafc;
    }

    /* --- KARTU METRIC (METODE PAKSA WARNA) --- */
    /* Ini memastikan kartu tetap putih dan teks hitam walau di Dark Mode */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Paksa Label menjadi Abu-abu */
    div[data-testid="stMetricLabel"] p {
        color: #64748b !important;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    /* Paksa Angka menjadi Hitam */
    div[data-testid="stMetricValue"] div {
        color: #0f172a !important;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Paksa Simbol Delta */
    div[data-testid="stMetricDelta"] svg, div[data-testid="stMetricDelta"] > div {
        color: #10b981 !important;
    }

    /* --- INFO BOX CUSTOM --- */
    .custom-info-box {
        background-color: #f0f9ff;
        border-left: 5px solid #0ea5e9;
        padding: 15px;
        border-radius: 8px;
        color: #0c4a6e;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. KONSTANTA PROYEK ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
# [REQUEST] Batas Wp sampai 550
WP_CHOICES = [300, 350, 400, 450, 500, 550] 
MIN_PV_MODULES = 1 
# [REQUEST] Batas Modul sampai 50
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
        if len(df.columns) <= 2:
            df = pd.read_csv(file_path, delimiter=';')
        if df.columns[0].lower() in ['no', 'no.']:
            df = df.iloc[:, 1:].copy() 
        df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object: 
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
                df[col] = df[col].astype(str).str.replace(' kWh/kWp', '', regex=False) 
            df[col] = pd.to_numeric(df[col], errors='coerce') 
        df.dropna(inplace=True) 
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

data_solar = load_data(FILE_DATA)
if data_solar.empty: st.stop()


# --- 5. HERO BANNER (VERSI HTML INLINE - GAMBAR PASTI MUNCUL) ---
st.markdown("""
    <div style="
        position: relative;
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.4)), url('https://images.unsplash.com/photo-1592833159057-65a284572477?q=80&w=2070');
        background-size: cover;
        background-position: center;
        padding: 80px 40px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    ">
        <h1 style="color: white; font-size: 3rem; font-weight: 800; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.6);">
            Solar Eco-Cost Analyzer
        </h1>
        <p style="color: #f0f0f0; font-size: 1.2rem; font-weight: 500; margin: 0 auto; max-width: 800px; text-shadow: 0 1px 3px rgba(0,0,0,0.6);">
            Hitung potensi penghematan biaya listrik dan dampak positif lingkungan dari rumah Anda.
        </p>
    </div>
""", unsafe_allow_html=True)


# --- 6. BAGIAN INPUT USER ---
if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4 

st.subheader("⚙️ Parameter Instalasi")

col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    provinsi_pilihan = st.selectbox("📍 Pilih Lokasi (Provinsi):", data_solar['Provinsi'].tolist())
    
    # [REQUEST] Tampilkan Info Wilayah (PV Out & Emisi)
    data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
    radiasi_harian = data_lokasi['Produksi_Harian_kWh']
    faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']
    
    # Menggunakan HTML langsung agar style konsisten
    st.markdown(f"""
    <div class="custom-info-box">
        <b>Data Wilayah: {provinsi_pilihan}</b><br>
        ☀️ Potensi Surya: {radiasi_harian} kWh/kWp<br>
        🏭 Emisi Grid: {faktor_emisi_lokal} kg/kWh
    </div>
    """, unsafe_allow_html=True)

with col_input2:
    tagihan_input = st.number_input("💸 Tagihan Listrik (Rp/Bln):", min_value=10000, value=st.session_state['tagihan_bulanan'], step=50000)
    tagihan_bulanan = tagihan_input 

with col_input3:
    wp_pilihan = st.selectbox("⚡ Kapasitas Panel (Wp):", WP_CHOICES, index=WP_CHOICES.index(550))
    # [REQUEST] Batas Max 50
    jumlah_modul = st.number_input("📦 Jumlah Modul (Max 50):", min_value=MIN_PV_MODULES, max_value=MAX_PV_MODULES, value=st.session_state['pv_module_count'])
    
    kapasitas_pv_wp = wp_pilihan * jumlah_modul
    kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
    st.caption(f"**Total Kapasitas:** {kapasitas_pv_kwp:.2f} kWp")


# --- 7. PROSES ALGORITMA (SESUAI KODE ACUAN) ---
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 
skor_kemandirian = min((produksi_pv_bulanan / konsumsi_kwh) * 100, 100) 
tagihan_baru = max(tagihan_bulanan - penghematan_rp, 0)

biaya_instalasi_pv = kapasitas_pv_wp * BIAYA_AWAL_PV_PER_Wp
biaya_kumulatif_tanpa_pv = []
biaya_kumulatif_dengan_pv = []
total_biaya_tanpa_pv = 0
total_biaya_dengan_pv = biaya_instalasi_pv 
payback_tahun = TAHUN_ANALISIS + 1 

tagihan_bulanan_saat_ini = tagihan_bulanan
tagihan_baru_saat_ini = tagihan_baru

for tahun in range(1, TAHUN_ANALISIS + 1):
    tagihan_bulanan_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)
    tagihan_baru_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)
    total_biaya_tanpa_pv += tagihan_bulanan_saat_ini * 12
    total_biaya_dengan_pv += tagihan_baru_saat_ini * 12
    
    biaya_kumulatif_tanpa_pv.append(total_biaya_tanpa_pv)
    biaya_kumulatif_dengan_pv.append(total_biaya_dengan_pv)
    
    if total_biaya_dengan_pv <= total_biaya_tanpa_pv and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = tahun

# [SOLUSI NAME ERROR] Variabel ini harus didefinisikan DI LUAR kolom
payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"

emisi_total_ton = emisi_dicegah_total * 12 * TAHUN_ANALISIS / 1000 
df_proyeksi = pd.DataFrame({'Tahun': range(1, TAHUN_ANALISIS + 1),'Tanpa PV': biaya_kumulatif_tanpa_pv,'Dengan PV': biaya_kumulatif_dengan_pv})
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- 8. DASHBOARD METRICS ---
st.divider()
st.subheader(f"📊 Hasil Analisis: {provinsi_pilihan}")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("💰 Hemat Biaya/Bulan", format_rupiah(penghematan_rp), delta=f"Tagihan Akhir: {format_rupiah(tagihan_baru)}")
with m2: st.metric("⏳ ROI (Balik Modal)", payback_display, help=f"Modal: {format_rupiah(biaya_instalasi_pv)}")
with m3: st.metric("🌱 Reduksi CO₂/Bulan", f"{emisi_dicegah_total:.1f} kg", help="Jejak karbon yang hilang.")
with m4: st.metric("⚡ Kemandirian", f"{skor_kemandirian:.1f}%", help="% Listrik dari Matahari.")

st.write("") 


# --- 9. VISUALISASI ---
tab1, tab2, tab3, tab4 = st.tabs(["📉 Grafik Biaya", "📈 Proyeksi ROI", "🌍 Lingkungan", "ℹ️ Rincian"])

# Konfigurasi Font Plotly
font_style = dict(family="Plus Jakarta Sans, sans-serif", size=14)

with tab1:
    st.subheader("Komparasi Tagihan")
    df_bar = pd.DataFrame({
        'Kategori': ['Sebelum', 'Sesudah'], 
        'Nilai': [tagihan_bulanan, tagihan_baru],
        'Label': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
    })
    
    # [SOLUSI ANKA HILANG] Pastikan text='Label' dan textposition='auto'
    fig_bar = px.bar(df_bar, x='Kategori', y='Nilai', text='Label', color='Kategori',
                     color_discrete_map={'Sebelum': '#64748b', 'Sesudah': '#22c55e'})
    
    # Menghapus yaxis_visible=False agar indikator sumbu X dan Y MUNCUL
    fig_bar.update_layout(
        showlegend=False, 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=font_style,
        xaxis_title=None,
        yaxis_title="Rupiah (Rp)" # Menambahkan label sumbu Y
    )
    fig_bar.update_traces(textposition='auto', textfont_size=16)
    
    if penghematan_rp > 0 and tagihan_baru < tagihan_bulanan:
        fig_bar.add_annotation(
            x=0.5, y=(tagihan_bulanan + tagihan_baru)/2,
            text=f"Hemat: {format_rupiah(penghematan_rp)}",
            showarrow=False, bgcolor="white", bordercolor="#22c55e", borderwidth=1, borderpad=5
        )
        
    st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("Kapan Modal Kembali?")
    df_long = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total')
    fig_line = px.line(df_long, x='Tahun', y='Total', color='Skenario', markers=True, 
                       color_discrete_map={'Tanpa PV': '#ef4444', 'Dengan PV': '#22c55e'})
    fig_line.update_layout(yaxis_tickformat=",.0f", plot_bgcolor='rgba(0,0,0,0)', font=font_style, legend=dict(orientation="h", y=1.1))
    
    if payback_tahun <= 15:
        val_bep = df_proyeksi.loc[df_proyeksi['Tahun'] == payback_tahun, 'Dengan PV'].values[0]
        fig_line.add_scatter(x=[payback_tahun], y=[val_bep], mode='markers', marker=dict(size=12, color='blue'), name='Titik BEP', showlegend=False)
        
    st.plotly_chart(fig_line, use_container_width=True)

with tab3:
    c_pie, c_txt = st.columns([1.5, 1])
    with c_pie:
        # [REQUEST] Donut Chart Plotly (Upgrade dari Matplotlib)
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Dicegah (PV)', 'Sisa (PLN)'], 
            values=[emisi_dicegah_grafik, emisi_tersisa_pln], 
            hole=.65, 
            marker_colors=['#22c55e', '#cbd5e1'],
            textinfo='percent'
        )])
        fig_donut.update_layout(
            annotations=[dict(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=26, showarrow=False, font_family="Plus Jakarta Sans", font_color="#15803d")],
            showlegend=True, margin=dict(t=20, b=0, l=0, r=0), font=font_style
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with c_txt:
        st.info(f"Anda mencegah **{emisi_dicegah_total:.1f} kg CO₂** per bulan.")
        st.markdown(f"""
        **Setara dengan:**
        \n🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**
        \n🚗 Menghapus **{int(emisi_dicegah_total*5)} km** perjalanan mobil
        """)

# --- 10. DETAIL TEKNIS (STRUKTUR SAMA DENGAN ACUAN) ---
with tab4:
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("### ⚙️ Spesifikasi Sistem")
        st.write("---")
        # Menggunakan Dictionary agar stabil
        data_dict_sistem = {
            "Keterangan": ["Kapasitas PV Total", "Jumlah Modul", "Kapasitas 1 Modul", "Produksi Energi Bulanan"],
            "Nilai": [f"{kapasitas_pv_kwp:.2f} kWp", f"{jumlah_modul} unit", f"{wp_pilihan} Wp", f"{produksi_pv_bulanan:.2f} kWh"]
        }
        st.table(pd.DataFrame(data_dict_sistem).set_index('Keterangan'))
        
    with col_t2:
        st.markdown("### 💸 Finansial & Dampak")
        st.write("---")
        # Menggunakan payback_display yang sudah didefinisikan (TIDAK AKAN NAME ERROR LAGI)
        data_dict_finansial = {
            "Keterangan": ["Biaya Instalasi Awal", "Tagihan Bulanan Baru", "Penghematan Bulanan", "Masa Balik Modal", f"Total Emisi Dicegah ({TAHUN_ANALISIS} Thn)"],
            "Nilai": [format_rupiah(biaya_instalasi_pv), format_rupiah(tagihan_baru), format_rupiah(penghematan_rp), payback_display, f"{emisi_total_ton:.1f} ton CO₂"]
        }
        st.table(pd.DataFrame(data_dict_finansial).set_index('Keterangan'))