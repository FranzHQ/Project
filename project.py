import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px # Mengimpor Plotly untuk visualisasi interaktif

# --- PERBAIKAN STABILITAS MATPLOTLIB (FIX PENTING UNTUK CLOUD) ---
import matplotlib 
matplotlib.use('Agg') 
# -------------------------------------------------------------------

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Eco-Cost Analyzer", layout="wide")

# --- KONSTANTA PROYEK ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
WP_CHOICES = [300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000]
MIN_PV_MODULES = 1 
TAHUN_ANALISIS = 15 
ASUMSI_INFLASI_LISTRIK = 0.05 
BIAYA_AWAL_PV_PER_Wp = 15000 

# --- FUNGSI UTILITY ---
def format_rupiah(x):
    """Format angka menjadi Rupiah untuk label grafik dan tampilan."""
    if x >= 1e9:
        return f"Rp {x/1e9:,.2f} M"
    if x >= 1e6:
        return f"Rp {x/1e6:,.1f} Jt"
    return f"Rp {x:,.0f}"

@st.cache_data
def load_data(file_path):
    """Memuat data, mencoba kedua delimiter, dan mengonversi format desimal."""
    try:
        df = pd.read_csv(file_path, delimiter=',')
        if len(df.columns) <= 2:
            df = pd.read_csv(file_path, delimiter=';')

        if df.columns[0].lower() in ['no', 'no.']:
            df = df.iloc[:, 1:] 
            
        df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object: 
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
                df[col] = df[col].astype(str).str.replace(' kWh/kWp', '', regex=False) 
            
            df[col] = pd.to_numeric(col, errors='coerce') #BUG FIX: Pastikan col diganti dengan df[col]
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
if data_solar.empty:
    st.stop()


# --- BAGIAN HEADER & JUDUL ---
st.title("☀️ Analisis Penghematan Biaya dan Pengurangan Emisi Ketika Menggunakan PV Rumahan")
st.markdown("""
Aplikasi ini membantu Anda menghitung potensi **penghematan biaya listrik (Rp)** dan **dampak lingkungan (emisi CO2)**
dengan beralih ke energi surya mandiri.
""")
st.divider()

# --- BAGIAN 1: INPUT USER ---

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
        value=st.session_state['pv_module_count'],
        step=1,
        key='pv_module_count'
    )
    
    kapasitas_pv_wp = wp_pilihan * jumlah_modul
    kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
    
    st.markdown(f"Kapasitas Total PV Anda: **{kapasitas_pv_kwp:.2f} kWp**")


# --- BAGIAN 2: PROSES ALGORITMA (Perbaikan Payback Period) ---

# A. Lookup Data Spesifik Lokasi
data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
radiasi_harian = data_lokasi['Produksi_Harian_kWh']
faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']

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
    # Kenaikan Tarif dihitung SEBELUM akumulasi (Efek inflasi terjadi di awal tahun)
    tagihan_bulanan_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)
    tagihan_baru_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)

    # 1. Update total biaya kumulatif
    total_biaya_tanpa_pv += tagihan_bulanan_saat_ini * 12
    total_biaya_dengan_pv += tagihan_baru_saat_ini * 12 # Biaya dengan PV termasuk biaya instalasi awal

    biaya_kumulatif_tanpa_pv.append(total_biaya_tanpa_pv)
    biaya_kumulatif_dengan_pv.append(total_biaya_dengan_pv)

    # 2. Cek Payback (FIX UTAMA: total_biaya_dengan_pv sudah termasuk biaya instalasi)
    # Payback tercapai jika total biaya DENGAN PV (termasuk investasi) <= total biaya TANPA PV
    if total_biaya_dengan_pv <= total_biaya_tanpa_pv and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = tahun
    
    # KESIMPULAN FIX: Perulangan dan kondisi pengecekan payback telah disederhanakan
    # dan dipastikan menggunakan nilai kumulatif yang sudah benar.

# Hitungan Emisi Total Jangka Panjang untuk Tampilan
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

# 1. HEMAT BIAYA BULANAN
with m1:
    st.metric(
        "💰 Hemat Biaya Bulanan", 
        f"{format_rupiah(int(penghematan_rp))}", 
        delta=f"Tagihan Akhir: {format_rupiah(int(tagihan_baru))}"
    )

# 2. MASA BALIK MODAL
with m2:
    payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"
    st.metric(
        "⏳ Masa Balik Modal", 
        payback_display, 
        help=f"Total biaya sistem PV adalah {format_rupiah(biaya_instalasi_pv)}"
    )

# 3. EMISI DICEGAH BULANAN
with m3:
    st.metric(
        "🌱 Emisi CO₂ Dicegah (Bln)", 
        f"{emisi_dicegah_total:.1f} kg", 
        help=f"Total Emisi Dicegah selama {TAHUN_ANALISIS} tahun: {emisi_total_ton:.1f} ton CO₂"
    )

# 4. SKOR KEMANDIRIAN
with m4:
    st.metric(
        "⚡ Skor Kemandirian Energi", 
        f"{skor_kemandirian:.1f}%", 
        help="Persentase kebutuhan listrik bulanan yang dipenuhi PV Anda."
    )

st.write("") 

# --- BAGIAN 4: VISUALISASI GRAFIK ---

tab1, tab2, tab3, tab4 = st.tabs(["📉 Analisis Biaya Bulanan", "📈 Proyeksi Jangka Panjang", "🌍 Analisis Lingkungan (Emisi)", "ℹ️ Detail Teknis"])

# GRAFIK 1: Analisis Biaya Bulanan (PLOTLY BAR CHART BARU)
with tab1:
    st.subheader("Komparasi Tagihan Listrik Bulanan")
    
    data_biaya = pd.DataFrame({
        'Kategori': ['Tagihan Awal', 'Tagihan Akhir'],
        'Rupiah': [tagihan_bulanan, tagihan_baru],
        'Teks': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
    })
    
    # Menggunakan Plotly Express (Interaktif dan Modern)
    fig_bar = px.bar(
        data_biaya, 
        x='Kategori', 
        y='Rupiah', 
        text='Teks', # Menampilkan nilai rupiah di atas bar
        color='Kategori',
        color_discrete_map={'Tagihan Awal': '#34495e', 'Tagihan Akhir': '#2ecc71'},
        title='Perbandingan Tagihan Listrik: Sebelum vs Sesudah PV'
    )
    
    # Customisasi Teks (Menghapus Judul Y dan X)
    fig_bar.update_layout(
        yaxis_title="", 
        xaxis_title="", 
        showlegend=False
    )
    
    # Menambahkan anotasi Penghematan (Manual, karena Plotly tidak memiliki fungsi penghematan otomatis)
    if penghematan_rp > 0 and tagihan_baru < tagihan_bulanan:
        y_pos_annotasi = (tagihan_bulanan + tagihan_baru) / 2
        fig_bar.add_annotation(
            x=0.5, y=y_pos_annotasi, # Di tengah antara kedua bar
            text=f"Hemat: {format_rupiah(penghematan_rp)}",
            showarrow=False,
            font=dict(size=14, color="black"),
            bgcolor="rgba(255, 255, 0, 0.5)",
            borderpad=4
        )
    
    st.plotly_chart(fig_bar, use_container_width=True) 
    
    st.markdown(f"**Tingkat Kemandirian Energi** dari PV Anda: **{skor_kemandirian:.1f}%**")
    st.progress(int(skor_kemandirian))

# GRAFIK 2: Proyeksi Jangka Panjang (Line Chart)
with tab2:
    st.subheader(f"Proyeksi Biaya Listrik Kumulatif Selama {TAHUN_ANALISIS} Tahun")

    # Siapkan data untuk Plotly Line Chart
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
    
    # Customisasi format Y-axis menjadi Rupiah
    fig_proj.update_layout(
        yaxis=dict(
            tickformat=",.0f",
            tickprefix="Rp "
        )
    )

    # Menandai Titik Payback (Interaktif Plotly)
    if payback_tahun <= TAHUN_ANALISIS:
        payback_cost = df_proyeksi[df_proyeksi['Tahun'] == payback_tahun]['Dengan PV'].iloc[0]
        
        fig_proj.add_scatter(
            x=[payback_tahun], 
            y=[payback_cost], 
            mode='markers', 
            marker=dict(size=10, color='#3498db'),
            name='Masa Balik Modal',
            showlegend=False
        )
        fig_proj.add_annotation(
            x=payback_tahun, y=payback_cost,
            text=f'{payback_tahun} Tahun',
            showarrow=True,
            arrowhead=1,
            ax=-30, ay=-30
        )
    
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown(f"""
    * **Asumsi:** Kenaikan tarif listrik sebesar {ASUMSI_INFLASI_LISTRIK*100}% per tahun.
    * **Total Hemat Setelah {TAHUN_ANALISIS} Tahun:** {format_rupiah(total_biaya_tanpa_pv - total_biaya_dengan_pv)}
    """)

# GRAFIK 3: Analisis Emisi (Donut Chart) 
with tab3:
    st.subheader("Porsi Pengurangan Jejak Karbon (CO₂)")
    
    labels_donut = ['Emisi Dicegah (Oleh PV)', 'Emisi Tersisa (Dari PLN)']
    sizes_donut = [emisi_dicegah_grafik, emisi_tersisa_pln] 
    
    if emisi_awal_total == 0:
        sizes_donut = [0, 1]
    
    colors_donut = ['#3498db', '#f1c40f']

    fig2, ax2 = plt.subplots(figsize=(6, 6))
    
    def func_autopct(pct):
        val = pct * emisi_awal_total / 100
        if pct > 5: 
            return f'{pct:.1f}%\n({val:.1f} kg)'
        return ''
        
    wedges, texts, autotexts = ax2.pie(
        sizes_donut, 
        labels=labels_donut if emisi_awal_total > 0 else None, 
        colors=colors_donut, 
        autopct=func_autopct,
        startangle=90, 
        pctdistance=0.75, 
        wedgeprops=dict(width=0.3) 
    )
    
    centre_circle = plt.Circle((0,0),0.60,fc='white')
    fig2.gca().add_artist(centre_circle)
    ax2.axis('equal') 
    
    ax2.set_title(f'Total Jejak Karbon Awal: {emisi_awal_total:.1f} kg CO₂/Bulan', fontsize=14)
    st.pyplot(fig2)
    plt.close('all') 
    
    st.info(f"Dengan PV, Anda berhasil mengurangi emisi sebesar **{emisi_dicegah_grafik:.1f} kg CO₂** dari konsumsi rumah Anda.")

# TAB 4: Detail Teknis 
with tab4:
    col_tech1, col_tech2 = st.columns(2)
    
    # BOX 1: Sistem & Energi
    with col_tech1:
        st.markdown("### ⚙️ Sistem & Energi")
        st.markdown("Ringkasan teknis instalasi dan produksi energi.")
        st.write("---")
        
        data_sistem = pd.DataFrame({
            "Keterangan": [
                "Kapasitas PV Total",
                "Jumlah Modul",
                "Kapasitas 1 Modul",
                "Produksi Energi Bulanan"
            ],
            "Nilai": [
                f"{kapasitas_pv_kwp:.2f} kWp",
                f"{jumlah_modul} unit",
                f"{wp_pilihan} Wp",
                f"{produksi_pv_bulanan:.2f} kWh"
            ]
        }).set_index('Keterangan')
        st.table(data_sistem)
        
    # BOX 2: Finansial & Dampak
    with col_tech2:
        st.markdown("### 💸 Finansial & Dampak")
        st.markdown("Rincian hitungan biaya dan manfaat lingkungan.")
        st.write("---")
        
        data_finansial = pd.DataFrame({
            "Keterangan": [
                "Biaya Instalasi Awal",
                "Tagihan Bulanan Baru",
                "Penghematan Bulanan",
                "Masa Balik Modal",
                f"Total Emisi Dicegah ({TAHUN_ANALISIS} Thn)"
            ],
            "Nilai": [
                format_rupiah(biaya_instalasi_pv),
                format_rupiah(tagihan_baru),
                format_rupiah(penghematan_rp),
                payback_display,
                f"{emisi_total_ton:.1f} ton CO₂"
            ]
        }).set_index('Keterangan')
        st.table(data_finansial)