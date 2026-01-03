import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Solar Analyzer", 
    layout="wide",
    page_icon="☀️"
)

# --- 2. CUSTOM CSS (MODERN UI & FLOATING TITLE) ---
st.markdown("""
<style>
    /* 1. HERO BANNER: Background Gambar di Belakang Judul */
    .hero-banner {
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url('https://images.unsplash.com/photo-1509391366360-2e959784a276?q=80&w=2072');
        height: 300px;
        background-position: center;
        background-size: cover;
        border-radius: 15px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Teks Judul dalam Banner (Warna Putih Tetap) */
    .hero-banner h1 {
        color: #ffffff !important;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        margin-bottom: 10px;
    }
    
    /* Teks Sub-judul dalam Banner */
    .hero-banner p {
        color: #f0f0f0 !important;
        font-size: 1.1rem;
        font-weight: 400;
        max-width: 800px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }

    /* 2. CARD STYLING UNTUK METRICS */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* 3. INFO BOX WILAYAH */
    .info-box {
        padding: 15px;
        border-radius: 10px;
        background-color: rgba(33, 150, 243, 0.1);
        border-left: 5px solid #2196f3;
        margin-top: 20px;
    }
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
    """Format angka menjadi Rupiah untuk label grafik dan tampilan."""
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
            st.error("Data tidak valid. Pastikan kolom data Anda terisi angka.")
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# Panggil fungsi untuk memuat data
data_solar = load_data(FILE_DATA)
if data_solar.empty:
    st.stop()


# --- 5. HEADER (JUDUL MENGAMBANG DI BACKGROUND) ---
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

st.subheader("⚙️ Data Input dan Instalasi")
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    provinsi_pilihan = st.selectbox(
        "Pilih Lokasi (Provinsi):", 
        data_solar['Provinsi'].tolist(),
        key='provinsi_key' 
    )
    
    # Data Wilayah
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
    tagihan_input = st.number_input(
        "Tagihan Listrik per Bulan (Rp):", 
        min_value=10000, 
        value=st.session_state['tagihan_bulanan'], 
        step=50000,
        key='tagihan_bulanan' 
    )
    tagihan_bulanan = tagihan_input 

with col_input3:
    wp_pilihan = st.selectbox(
        "Pilih Kapasitas 1 Modul PV (Watt Peak/Wp):",
        WP_CHOICES, 
        index=WP_CHOICES.index(550),
        key='pv_module_watt'
    )
    
    jumlah_modul = st.number_input(
        "Jumlah Modul PV yang Dipasang:",
        min_value=MIN_PV_MODULES,
        max_value=MAX_PV_MODULES, 
        value=st.session_state['pv_module_count'],
        step=1,
        key='pv_module_count'
    )
    
    kapasitas_pv_wp = wp_pilihan * jumlah_modul
    kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
    
    st.markdown(f"Kapasitas Total PV Anda: **{kapasitas_pv_kwp:.2f} kWp**")


# --- BAGIAN 2: PROSES ALGORITMA ---

# B. Perhitungan Konsumsi & Produksi
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

# C. Hitung Output Kritis Bulanan
penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 
skor_kemandirian = (produksi_pv_bulanan / konsumsi_kwh) * 100
skor_kemandirian = min(skor_kemandirian, 100) 
tagihan_baru = tagihan_bulanan - penghematan_rp
if tagihan_baru < 0: tagihan_baru = 0

# D. Hitung Output Kritis Jangka Panjang (Payback Fix)
biaya_instalasi_pv = kapasitas_pv_wp * BIAYA_AWAL_PV_PER_Wp
biaya_kumulatif_tanpa_pv = []
biaya_kumulatif_dengan_pv = []

tagihan_bulanan_saat_ini = tagihan_bulanan
tagihan_baru_saat_ini = tagihan_baru

total_biaya_tanpa_pv = 0
total_biaya_dengan_pv = biaya_instalasi_pv 

payback_tahun = TAHUN_ANALISIS + 1 

for tahun in range(1, TAHUN_ANALISIS + 1):
    # Kenaikan Tarif Bulanan
    tagihan_bulanan_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)
    tagihan_baru_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)

    # 1. Update total biaya kumulatif
    total_biaya_tanpa_pv += tagihan_bulanan_saat_ini * 12
    total_biaya_dengan_pv += tagihan_baru_saat_ini * 12

    biaya_kumulatif_tanpa_pv.append(total_biaya_tanpa_pv)
    biaya_kumulatif_dengan_pv.append(total_biaya_dengan_pv)

    # 2. Cek Payback
    if total_biaya_dengan_pv <= total_biaya_tanpa_pv and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = tahun
    
emisi_total_ton = emisi_dicegah_total * 12 * TAHUN_ANALISIS / 1000 
df_proyeksi = pd.DataFrame({
    'Tahun': range(1, TAHUN_ANALISIS + 1),
    'Tanpa PV': biaya_kumulatif_tanpa_pv,
    'Dengan PV': biaya_kumulatif_dengan_pv
})

# E. VARIABEL KHUSUS UNTUK GRAFIK DONUT 
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- BAGIAN 3: OUTPUT DASHBOARD METRIC (Scorecards) ---

st.divider()
st.header(f"📊 Hasil Analisis Dampak untuk {provinsi_pilihan}")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "💰 Hemat Biaya Bulanan", 
        f"{format_rupiah(int(penghematan_rp))}", 
        delta=f"Tagihan Akhir: {format_rupiah(int(tagihan_baru))}"
    )

with m2:
    payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"
    st.metric(
        "⏳ Masa Balik Modal", 
        payback_display, 
        help=f"Total biaya sistem PV adalah {format_rupiah(biaya_instalasi_pv)}"
    )

with m3:
    st.metric(
        "🌱 Emisi CO₂ Dicegah (Bln)", 
        f"{emisi_dicegah_total:.1f} kg", 
        help=f"Total Emisi Dicegah selama {TAHUN_ANALISIS} tahun: {emisi_total_ton:.1f} ton CO₂"
    )

with m4:
    st.metric(
        "⚡ Skor Kemandirian Energi", 
        f"{skor_kemandirian:.1f}%", 
        help="Persentase kebutuhan listrik bulanan yang dipenuhi PV Anda."
    )

st.write("") 

# --- BAGIAN 4: VISUALISASI GRAFIK ---

# UPDATE: Menambahkan "☀️ Profil Produksi Energi" di Tab ke-3
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📉 Analisis Biaya", 
    "📈 Proyeksi ROI", 
    "☀️ Profil Produksi Energi", 
    "🌍 Lingkungan", 
    "ℹ️ Detail Teknis"
])

# GRAFIK 1: Analisis Biaya Bulanan
with tab1:
    st.subheader("Komparasi Tagihan Listrik Bulanan")
    
    data_biaya = pd.DataFrame({
        'Kategori': ['Tagihan Awal', 'Tagihan Akhir'],
        'Rupiah': [tagihan_bulanan, tagihan_baru],
        'Teks': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
    })
    
    fig_bar = px.bar(
        data_biaya, 
        x='Kategori', 
        y='Rupiah', 
        text='Teks', 
        color='Kategori',
        color_discrete_map={'Tagihan Awal': '#34495e', 'Tagihan Akhir': '#2ecc71'},
        title='Perbandingan Tagihan Listrik: Sebelum vs Sesudah PV'
    )
    
    fig_bar.update_layout(yaxis_title="", xaxis_title="", showlegend=False)
    
    if penghematan_rp > 0 and tagihan_baru < tagihan_bulanan:
        y_pos_annotasi = (tagihan_bulanan + tagihan_baru) / 2
        fig_bar.add_annotation(
            x=0.5, y=y_pos_annotasi, 
            text=f"Hemat: {format_rupiah(penghematan_rp)}",
            showarrow=False,
            font=dict(size=14, color="black"),
            bgcolor="rgba(255, 255, 0, 0.8)", 
            borderpad=4
        )
    
    st.plotly_chart(fig_bar, use_container_width=True) 
    
    st.markdown(f"**Tingkat Kemandirian Energi** dari PV Anda: **{skor_kemandirian:.1f}%**")
    st.progress(int(skor_kemandirian))

# GRAFIK 2: Proyeksi Jangka Panjang
with tab2:
    st.subheader(f"Proyeksi Biaya Listrik Kumulatif Selama {TAHUN_ANALISIS} Tahun")

    df_plot_longterm = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total Biaya Kumulatif')

    fig_proj = px.line(
        df_plot_longterm,
        x='Tahun',
        y='Total Biaya Kumulatif',
        color='Skenario',
        color_discrete_map={'Tanpa PV': '#e74c3c', 'Dengan PV': '#2ecc71'},
        title='Perbandingan Biaya Kumulatif Jangka Panjang',
        markers=True
    )
    
    fig_proj.update_layout(yaxis=dict(tickformat=",.0f", tickprefix="Rp "))

    if payback_tahun <= TAHUN_ANALISIS:
        payback_cost = df_proyeksi[df_proyeksi['Tahun'] == payback_tahun]['Dengan PV'].iloc[0]
        fig_proj.add_scatter(
            x=[payback_tahun], y=[payback_cost], 
            mode='markers', marker=dict(size=10, color='#3498db'),
            name='Masa Balik Modal', showlegend=False
        )
    
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown(f"""
    * **Asumsi:** Kenaikan tarif listrik sebesar {ASUMSI_INFLASI_LISTRIK*100}% per tahun.
    * **Total Hemat Setelah {TAHUN_ANALISIS} Tahun:** {format_rupiah(total_biaya_tanpa_pv - total_biaya_dengan_pv)}
    """)

# GRAFIK 3 (BARU): Profil Produksi Energi (Simulasi Musiman)

with tab3:
    st.subheader(f"Estimasi Produksi Energi Bulanan di {provinsi_pilihan}")
    
    # --- 1. LOGIKA ZONASI MUSIM (AGAR LEBIH REALISTIS) ---
    def get_pola_musim(nama_prov):
        nama = nama_prov.lower()
        
        # ZONA 1: TIPE MONSUN (Jawa, Bali, Nusa Tenggara)
        if any(x in nama for x in ['jawa', 'jakarta', 'banten', 'yogyakarta', 'bali', 'nusa']):
            st.caption("ℹ️ Pola Musim: Monsun (Puncak kemarau di pertengahan tahun).")
            return [0.80, 0.85, 0.90, 0.98, 1.05, 1.10, 1.15, 1.18, 1.12, 1.02, 0.90, 0.85]
            
        # ZONA 2: TIPE KHATULISTIWA (Sumatra, Kalimantan, Sulawesi, Papua, dll)
        else:
            st.caption("ℹ️ Pola Musim: Khatulistiwa (Cenderung stabil sepanjang tahun).")
            return [0.95, 0.98, 1.05, 1.02, 0.98, 0.96, 0.98, 1.02, 1.05, 1.02, 0.98, 0.96]

    faktor_musim = get_pola_musim(provinsi_pilihan)
    
    bulan_list = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    produksi_bulanan_simulasi = []
    
    for i in range(12):
        prod = produksi_pv_harian * days_in_month[i] * faktor_musim[i]
        produksi_bulanan_simulasi.append(prod)
        
    df_monthly = pd.DataFrame({
        'Bulan': bulan_list,
        'Produksi (kWh)': produksi_bulanan_simulasi
    })
    
    # --- 2. MEMBUAT GRAFIK (CLEAN LOOK) ---
    warna_bar = '#e74c3c' if max(faktor_musim) > 1.10 else '#f39c12'
    
    fig_monthly = px.bar(
        df_monthly, 
        x='Bulan', 
        y='Produksi (kWh)',
        text_auto='.0f', # Angka tetap ada di atas batang, tapi rapi
        title=f"Profil Energi Bulanan - {provinsi_pilihan}",
        color_discrete_sequence=[warna_bar]
    )
    
    fig_monthly.update_layout(
        yaxis_title="Energi (kWh)",
        xaxis_title="",
        bargap=0.3,
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified" # Hover effect yang elegan
    )
    

    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Ringkasan Bawah
    c1, c2 = st.columns(2)
    c1.metric("Total Produksi Setahun", f"{sum(produksi_bulanan_simulasi)/1000:.2f} MWh")
    c2.metric("Variabilitas Musim", "Tinggi (Monsun)" if max(faktor_musim) > 1.10 else "Stabil (Ekuatorial)")

# GRAFIK 4: Analisis Emisi (Donut)
with tab4:
    st.subheader("Total Pengurangan Jejak Karbon (CO₂)")
    
    c_don, c_txt = st.columns([1.5, 1])
    
    with c_don:
        labels = ['Dicegah (PV)', 'Sisa (PLN)']
        values = [emisi_dicegah_grafik, emisi_tersisa_pln]
        colors = ['#2ecc71', '#bdc3c7']
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.6, 
            marker_colors=colors,
            hoverinfo="label+value+percent",
            textinfo='percent'
        )])
        
        fig_donut.update_layout(
            annotations=[dict(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=20, showarrow=False)],
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with c_txt:
        st.info(f"Dengan PV, Anda berhasil mengurangi emisi sebesar **{emisi_dicegah_grafik:.1f} kg CO₂** dari konsumsi rumah Anda.")
        st.markdown(f"""
        **Setara dengan:**
        \n🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**
        \n🚗 Menghapus **{int(emisi_dicegah_total*5)} km** perjalanan mobil
        """)

# TAB 5: Detail Teknis
with tab5:
    col_tech1, col_tech2 = st.columns(2)
    
    with col_tech1:
        st.markdown("### ⚙️ Sistem & Energi")
        st.markdown("Ringkasan teknis instalasi dan produksi energi.")
        st.write("---")
        
        data_sistem = pd.DataFrame({
            "Keterangan": ["Kapasitas PV Total", "Jumlah Modul", "Kapasitas 1 Modul", "Produksi Energi Bulanan"],
            "Nilai": [f"{kapasitas_pv_kwp:.2f} kWp", f"{jumlah_modul} unit", f"{wp_pilihan} Wp", f"{produksi_pv_bulanan:.2f} kWh"]
        }).set_index('Keterangan')
        st.table(data_sistem)
        
    with col_tech2:
        st.markdown("### 💸 Finansial & Dampak")
        st.markdown("Rincian hitungan biaya dan manfaat lingkungan.")
        st.write("---")
        
        data_finansial = pd.DataFrame({
            "Keterangan": ["Biaya Instalasi Awal", "Tagihan Bulanan Baru", "Penghematan Bulanan", "Masa Balik Modal", f"Total Emisi Dicegah ({TAHUN_ANALISIS} Thn)"],
            "Nilai": [format_rupiah(biaya_instalasi_pv), format_rupiah(tagihan_baru), format_rupiah(penghematan_rp), payback_display, f"{emisi_total_ton:.1f} ton CO₂"]
        }).set_index('Keterangan')
        st.table(data_finansial)