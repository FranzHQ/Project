import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- PERBAIKAN STABILITAS MATPLOTLIB (FIX PENTING UNTUK CLOUD) ---
# Memaksa Matplotlib menggunakan backend non-interaktif
import matplotlib 
matplotlib.use('Agg') 
# -------------------------------------------------------------------

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Eco-Cost Analyzer", layout="wide")

# --- KONSTANTA PROYEK ---
TARIF_PLN = 1400 # Rupiah per kWh (Tarif non-subsidi acuan)
FILE_DATA = 'produksi_emisi_provinsi.csv' # Pastikan nama file ini sudah benar
WP_CHOICES = [300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000] # Pilihan Wp umum
MIN_PV_MODULES = 1 # Jumlah minimum modul PV

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

        # Koreksi nama kolom yang diambil dari referensi file CSV:
        # Jika kolom pertama adalah 'No', hapus
        if df.columns[0].lower() in ['no', 'no.']:
            df = df.iloc[:, 1:] 
            
        # Penamaan ulang kolom yang tersisa (sesuai urutan di file data)
        df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        
        # 3. KOREKSI FORMAT ANGKA (Mengubah koma desimal ke titik desimal)
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object: 
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
                df[col] = df[col].astype(str).str.replace(' kWh/kWp', '', regex=False) # Hapus unit jika ada
            
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
st.title("☀️ Analisis Penghematan Biaya dan Pengurangan Emisi Ketika Menggunakan PV Rumahan")
st.markdown("""
Aplikasi ini membantu Anda menghitung potensi **penghematan biaya listrik (Rp)** dan **dampak lingkungan (emisi CO2)**
dengan beralih ke energi surya mandiri, disesuaikan dengan **lokasi provinsi** dan **konsumsi listrik** Anda.
Ini ditujukan agar **mudah dipahami** oleh siapa pun, termasuk non-teknis.
""")
st.divider()

# --- BAGIAN 1: INPUT USER (Menggunakan Session State untuk Interaktivitas) ---

# Inisialisasi Session State 
if 'tagihan_bulanan' not in st.session_state:
    st.session_state['tagihan_bulanan'] = 500000

if 'pv_module_watt' not in st.session_state:
    st.session_state['pv_module_watt'] = 550 # Default 550 Wp

if 'pv_module_count' not in st.session_state:
    st.session_state['pv_module_count'] = 4 # Default 4 modul

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
        key='tagihan_bulanan' 
    )
    tagihan_bulanan = st.session_state['tagihan_bulanan']

with col_input3:
    # INPUT 3a: Pilihan Wp Modul PV
    wp_pilihan = st.selectbox(
        "Pilih Kapasitas 1 Modul PV (Watt Peak/Wp):",
        WP_CHOICES,
        index=WP_CHOICES.index(550), # Default ke 550 Wp
        key='pv_module_watt'
    )
    
    # INPUT 3b: Jumlah Modul PV
    jumlah_modul = st.number_input(
        "Jumlah Modul PV yang Dipasang:",
        min_value=MIN_PV_MODULES,
        value=st.session_state['pv_module_count'],
        step=1,
        key='pv_module_count'
    )
    
    # Hitung Kapasitas PV (kWp) total
    kapasitas_pv_wp = wp_pilihan * jumlah_modul
    kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0 # Konversi Wp ke kWp
    
    st.markdown(f"Kapasitas Total PV Anda: **{kapasitas_pv_kwp:.2f} kWp**")


# --- BAGIAN 2: PROSES ALGORITMA ---

# A. Lookup Data Spesifik Lokasi
data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
radiasi_harian = data_lokasi['Produksi_Harian_kWh']
faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']

# B. Perhitungan Konsumsi & Produksi
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
# Gunakan kapasitas total kWp yang baru dihitung
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
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

# E. VARIABEL KHUSUS UNTUK GRAFIK DONUT 
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- BAGIAN 3: OUTPUT DASHBOARD ---

st.divider()
st.header(f"📊 Hasil Analisis Dampak untuk {provinsi_pilihan}")

# --- 3 METRIK UTAMA (Scorecards) ---
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
    pohon_setara = (emisi_tampil * 12) / 22 # Estimasi 1 pohon dewasa menyerap 22kg CO2/tahun
    
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

# --- BAGIAN 4: VISUALISASI GRAFIK (Untuk Non-Teknis) ---

tab1, tab2, tab3 = st.tabs(["📉 Analisis Biaya & Kemandirian", "🌍 Analisis Lingkungan (Emisi)", "ℹ️ Detail Teknis"])

# GRAFIK 1: Analisis Biaya dan Kemandirian (Stacked Bar Chart)
with tab1:
    st.subheader("Komparasi Struktur Biaya Listrik Bulanan")
    
    data_biaya = pd.DataFrame({
        'Kategori': ['Tagihan Awal', 'Tagihan Akhir (Dengan PV)'],
        'Dibayar ke PLN': [tagihan_bulanan, tagihan_baru],
        'Disuplai PV': [0, penghematan_rp]
    })
    
    fig, ax = plt.subplots(figsize=(9, 5))
    
    # Stacked Bar
    bar_pln = ax.bar(data_biaya['Kategori'], data_biaya['Dibayar ke PLN'], color=['#34495e', '#e74c3c'], label='Dibayar ke PLN')
    bar_pv = ax.bar(data_biaya['Kategori'][1], data_biaya['Disuplai PV'][1], bottom=data_biaya['Dibayar ke PLN'][1], color='#2ecc71', label='Disuplai PV (Penghematan)')
    
    # Menambahkan Label Angka di Atas Bar
    def format_rupiah(x):
        if x >= 1e6:
            return f"Rp {x/1e6:,.1f} Jt"
        return f"Rp {x:,.0f}"
        
    # --- PERBAIKAN ATTRIBUTE ERROR DIMULAI DI SINI ---
    # Kita menggunakan ax.bar_label pada objek container bar_pln,
    # dan menyediakan label untuk kedua bar di dalamnya.
    
    # Label untuk Tagihan Awal dan Tagihan Akhir (bagian PLN)
    # Gunakan bar_pln secara keseluruhan (container) dan pasangkan dengan kedua label Rupiah
    ax.bar_label(bar_pln, 
                 labels=[format_rupiah(data_biaya['Dibayar ke PLN'][0]), format_rupiah(data_biaya['Dibayar ke PLN'][1])], 
                 padding=5)
    
    total_akhir = tagihan_baru + penghematan_rp
    ax.text(data_biaya['Kategori'][1], total_akhir, format_rupiah(total_akhir), 
            ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')
    
    # --- PERBAIKAN ATTRIBUTE ERROR SELESAI DI SINI ---
    
    # Setting
    ax.set_title('Struktur Biaya Listrik Bulanan (Perbandingan)', fontsize=14, pad=15)
    ax.set_ylabel('Total Rupiah', fontsize=12)
    ax.ticklabel_format(style='plain', axis='y') 
    plt.yticks([]) # Sembunyikan tick y-axis agar fokus pada label di atas bar
    
    plt.legend(loc='upper left', bbox_to_anchor=(0.0, 1.0))
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    
    st.pyplot(fig)
    plt.close('all') # FIX: Ganti plt.close(fig) menjadi plt.close('all') untuk stabilitas ekstra
    
    st.markdown(f"**Tingkat Kemandirian Energi** dari PV Anda: **{skor_kemandirian:.1f}%**")
    st.progress(int(skor_kemandirian))
    

# GRAFIK 2: Analisis Emisi (Donut Chart)
with tab2:
    st.subheader("Porsi Pengurangan Jejak Karbon (CO₂)")
    
    labels_donut = ['Emisi Dicegah (Oleh PV)', 'Emisi Tersisa (Dari PLN)']
    sizes_donut = [emisi_dicegah_grafik, emisi_tersisa_pln] 
    
    # Jika salah satu porsi 0, gunakan 100% untuk yang lain agar grafik tidak kosong
    if emisi_dicegah_grafik == 0 and emisi_tersisa_pln == 0:
        sizes_donut = [0, 1]
    
    colors_donut = ['#3498db', '#f1c40f']

    fig2, ax2 = plt.subplots(figsize=(6, 6))
    
    # Custom autopct function untuk menampilkan % dan kg
    def func_autopct(pct):
        val = pct * emisi_awal_total / 100
        if pct > 5: # Hanya tampilkan label jika porsi cukup besar
            return f'{pct:.1f}%\n({val:.1f} kg)'
        return ''
        
    wedges, texts, autotexts = ax2.pie(
        sizes_donut, 
        labels=labels_donut if emisi_awal_total > 0 else None, 
        colors=colors_donut, 
        autopct=func_autopct,
        startangle=90, 
        pctdistance=0.75, 
        wedgeprops=dict(width=0.3) # Membuatnya menjadi Donut Chart
    )
    
    # Draw circle for donut effect
    centre_circle = plt.Circle((0,0),0.60,fc='white')
    fig2.gca().add_artist(centre_circle)
    ax2.axis('equal') # Memastikan Pie Chart berbentuk lingkaran
    
    ax2.set_title(f'Total Jejak Karbon Awal: {emisi_awal_total:.1f} kg CO₂/Bulan', fontsize=14)
    st.pyplot(fig2)
    plt.close('all') # FIX: Ganti plt.close(fig2) menjadi plt.close('all') untuk stabilitas ekstra
    
    st.info(f"Dengan PV, Anda berhasil mengurangi emisi sebesar **{emisi_dicegah_grafik:.1f} kg CO₂** dari konsumsi rumah Anda.")

# TAB 3: Detail Teknis
with tab3:
    st.subheader("Data Teknis dan Angka Kunci")
    
    st.markdown(f"**Tarif Dasar Listrik (TDL) Acuan:** Rp {TARIF_PLN:,.0f} / kWh")
    st.markdown(f"**Kapasitas PV Total Anda:** {kapasitas_pv_kwp:.2f} kWp")
    
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