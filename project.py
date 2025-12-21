import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Eco-Cost Analyzer", 
    page_icon="☀️",
    layout="wide"
)

# --- CUSTOM CSS UNTUK UI LEBIH BAGUS ---
st.markdown("""
<style>
    /* Mengubah background utama menjadi sedikit abu-abu lembut agar konten menonjol */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Styling untuk container metric agar terlihat seperti kartu */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Warna Judul */
    h1, h2, h3 {
        color: #2c3e50;
    }
    
    /* Highlight text penting */
    .highlight {
        color: #27ae60;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- KONSTANTA PROYEK ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
# Batas pilihan Wp hanya sampai 550 sesuai request
WP_CHOICES = [300, 350, 400, 450, 500, 550] 
MIN_PV_MODULES = 1 
MAX_PV_MODULES = 50 # Batas maksimal modul
TAHUN_ANALISIS = 15 
ASUMSI_INFLASI_LISTRIK = 0.05 
BIAYA_AWAL_PV_PER_Wp = 15000 

# --- FUNGSI UTILITY ---
def format_rupiah(x):
    if x >= 1e9:
        return f"Rp {x/1e9:,.2f} M"
    if x >= 1e6:
        return f"Rp {x/1e6:,.1f} Jt"
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
        if df.empty:
            st.error("Data tidak valid.")
        return df
    except Exception as e:
        st.error(f"Error memuat data: {e}")
        return pd.DataFrame()

data_solar = load_data(FILE_DATA)
if data_solar.empty:
    st.stop()


# --- BAGIAN HEADER & BANNER ---
# Menambahkan gambar banner agar lebih menarik
st.image("https://images.unsplash.com/photo-1509391366360-2e959784a276?q=80&w=2072&auto=format&fit=crop", use_container_width=True)
st.title("☀️ Eco-Cost Analyzer: Solusi Energi Surya Rumahan")
st.markdown("""
Simulasi cerdas untuk menghitung **penghematan biaya listrik** dan **kontribusi lingkungan** Anda 
dengan beralih ke Pembangkit Listrik Tenaga Surya (PLTS) Atap.
""")
st.divider()

# --- BAGIAN 1: INPUT USER & KONTEKS WILAYAH ---

if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4 

st.subheader("⚙️ Parameter Instalasi")

col_input, col_info = st.columns([2, 1])

with col_input:
    c1, c2 = st.columns(2)
    with c1:
        provinsi_pilihan = st.selectbox("📍 Pilih Lokasi (Provinsi):", data_solar['Provinsi'].tolist())
        tagihan_input = st.number_input("💸 Tagihan Listrik per Bulan (Rp):", min_value=10000, value=st.session_state['tagihan_bulanan'], step=50000)
    
    with c2:
        wp_pilihan = st.selectbox("panas Pilih Kapasitas Panel (Wp):", WP_CHOICES, index=WP_CHOICES.index(550))
        # Pembatasan jumlah modul max 50
        jumlah_modul = st.number_input("📦 Jumlah Modul (Max 50):", min_value=1, max_value=MAX_PV_MODULES, value=st.session_state['pv_module_count'], step=1)

# Lookup Data Lokasi
data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
radiasi_harian = data_lokasi['Produksi_Harian_kWh']
faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']

# Menampilkan Info Provinsi di Kolom Sebelah Kanan (UI Request)
with col_info:
    st.info(f"""
    **Data Lingkungan: {provinsi_pilihan}**
    
    ☀️ **Potensi Surya (PV Out):**
    `{radiasi_harian} kWh/kWp/hari`
    
    🏭 **Faktor Emisi Grid:**
    `{faktor_emisi_lokal} kg CO₂/kWh`
    """)

# --- BAGIAN 2: PROSES ALGORITMA ---
kapasitas_pv_wp = wp_pilihan * jumlah_modul
kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
tagihan_bulanan = tagihan_input

konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 

# Logika agar tidak minus jika produksi > konsumsi
skor_kemandirian = (produksi_pv_bulanan / konsumsi_kwh) * 100
skor_kemandirian = min(skor_kemandirian, 100) 

tagihan_baru = tagihan_bulanan - penghematan_rp
if tagihan_baru < 0: tagihan_baru = 0

# --- HITUNGAN PAYBACK PERIOD ---
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
df_proyeksi = pd.DataFrame({'Tahun': range(1, TAHUN_ANALISIS + 1),'Tanpa PV': biaya_kumulatif_tanpa_pv,'Dengan PV': biaya_kumulatif_dengan_pv})

# Data untuk Donut Chart
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik

# --- BAGIAN 3: DASHBOARD METRIC ---
st.write("---")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("💰 Hemat Biaya/Bulan", f"{format_rupiah(int(penghematan_rp))}", delta=f"Sisa Tagihan: {format_rupiah(int(tagihan_baru))}", delta_color="inverse")
with m2:
    payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"
    st.metric("⏳ Balik Modal (ROI)", payback_display, help="Estimasi waktu hingga modal awal kembali.")
with m3:
    st.metric("🌱 Reduksi CO₂/Bulan", f"{emisi_dicegah_total:.1f} kg", help="Kontribusi pengurangan jejak karbon Anda.")
with m4:
    st.metric("⚡ Kemandirian Energi", f"{skor_kemandirian:.1f}%", help="Persentase kebutuhan listrik yang dipenuhi sendiri.")

st.write("") 

# --- BAGIAN 4: VISUALISASI ---
tab1, tab2, tab3, tab4 = st.tabs(["📉 Analisis Biaya", "📈 Proyeksi ROI", "🌍 Dampak Lingkungan", "ℹ️ Rincian Teknis"])

# 1. BAR CHART BIAYA (PLOTLY)
with tab1:
    st.subheader("Komparasi Tagihan Listrik Bulanan")
    df_biaya = pd.DataFrame({
        'Kategori': ['Sebelum Pasang PV', 'Sesudah Pasang PV'],
        'Biaya': [tagihan_bulanan, tagihan_baru],
        'Label': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
    })
    
    fig_bar = px.bar(df_biaya, x='Kategori', y='Biaya', text='Label', 
                     color='Kategori', color_discrete_map={'Sebelum Pasang PV': '#95a5a6', 'Sesudah Pasang PV': '#2ecc71'})
    fig_bar.update_traces(textposition='auto', textfont_size=14)
    fig_bar.update_layout(showlegend=False, yaxis_visible=False, xaxis_title="", plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_bar, use_container_width=True)

# 2. LINE CHART PROYEKSI (PLOTLY)
with tab2:
    st.subheader("Kapan Modal Anda Kembali?")
    df_longterm = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Kumulatif')
    fig_line = px.line(df_longterm, x='Tahun', y='Kumulatif', color='Skenario', markers=True,
                       color_discrete_map={'Tanpa PV': '#e74c3c', 'Dengan PV': '#27ae60'})
    
    # Menandai titik payback
    if payback_tahun <= TAHUN_ANALISIS:
        val_payback = df_proyeksi.loc[df_proyeksi['Tahun'] == payback_tahun, 'Dengan PV'].values[0]
        fig_line.add_annotation(x=payback_tahun, y=val_payback, text=f"Balik Modal: Th ke-{payback_tahun}",
                                showarrow=True, arrowhead=2, ax=0, ay=-40, bgcolor="#f1c40f")

    fig_line.update_layout(yaxis_tickformat=",.0f", hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_line, use_container_width=True)

# 3. DONUT CHART EMISI (PLOTLY - IMPROVED)
with tab3:
    c_chart, c_text = st.columns([1.5, 1])
    
    with c_chart:
        # Data untuk Plotly Pie
        labels = ['Diserap PV (Bersih)', 'Sisa Grid (Kotor)']
        values = [emisi_dicegah_grafik, emisi_tersisa_pln]
        colors = ['#2ecc71', '#bdc3c7'] # Hijau Cerah & Abu-abu

        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.6, # Membuat lubang donat
            marker_colors=colors,
            hoverinfo="label+value+percent",
            textinfo='percent',
            textfont_size=16
        )])

        fig_donut.update_layout(
            title_text="Proporsi Pengurangan Emisi",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=40, b=0, l=0, r=0)
        )
        
        # Tambahkan teks di tengah donat
        fig_donut.add_annotation(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=30, showarrow=False, font_color="#27ae60")
        fig_donut.add_annotation(text="Cleaner", x=0.5, y=0.4, font_size=12, showarrow=False)
        
        st.plotly_chart(fig_donut, use_container_width=True)

    with c_text:
        st.markdown("### 🌍 Dampak Nyata")
        st.markdown(f"""
        Setiap bulannya, sistem Anda mencegah:
        ## **{emisi_dicegah_total:.1f} kg CO₂**
        
        Ini setara dengan:
        - 🌳 Menanam **{int(emisi_dicegah_total / 20)} pohon** setiap bulan.
        - 🚗 Menghemat perjalanan mobil sejauh **{int(emisi_dicegah_total * 5)} km**.
        """)
        if skor_kemandirian >= 100:
            st.success("🎉 LUAR BIASA! Rumah Anda sudah **Net Zero Emission** untuk kelistrikan!")

# 4. DETAIL TEKNIS
with tab4:
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.caption("Spesifikasi Sistem")
        st.table(pd.DataFrame({
            'Parameter': ['Total Kapasitas', 'Jumlah Modul', 'Jenis Modul', 'Produksi Estimasi'],
            'Nilai': [f"{kapasitas_pv_kwp:.2f} kWp", f"{jumlah_modul} Unit", f"{wp_pilihan} Wp", f"{produksi_pv_bulanan:.2f} kWh/bln"]
        }).set_index('Parameter'))
    
    with col_t2:
        st.caption("Asumsi Finansial")
        st.table(pd.DataFrame({
            'Parameter': ['Investasi Awal', 'Tarif PLN', 'Inflasi Listrik', 'Total Hemat (15 Th)'],
            'Nilai': [format_rupiah(biaya_instalasi_pv), "Rp 1.400 /kWh", "5% /tahun", format_rupiah(total_biaya_tanpa_pv - total_biaya_dengan_pv)]
        }).set_index('Parameter'))