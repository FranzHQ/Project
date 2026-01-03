
             SOLAR ANALYZER - PANDUAN LENGKAP

Selamat datang di Solar Analyzer!
Aplikasi ini membantu Anda menghitung potensi penghematan listrik dan 
dampak lingkungan dari penggunaan Panel Surya (PV) di rumah Anda.

Dokumen ini berisi:
1. PANDUAN INSTALASI (Cara menjalankan aplikasi di komputer sendiri)
2. PANDUAN PENGGUNAAN (Cara memakai fitur-fitur website)


BAGIAN 1: PANDUAN INSTALASI (Untuk Pengguna Windows)

Ikuti langkah-langkah ini jika Anda ingin menjalankan aplikasi ini di 
laptop atau komputer Anda secara offline (Localhost).

LANGKAH 1: PERSIAPAN FILE
Pastikan Anda memiliki folder proyek dengan susunan file seperti ini:

    NamaFolderProyek/
    ├── project.py                    (File kode program utama)
    ├── produksi_emisi_provinsi.csv   (File data provinsi, matahari & emisi)
    ├── README.txt                    (File panduan)
    └── .streamlit/                   (Folder khusus pengaturan tampilan)
          
    PENTING: Jangan mengubah nama file agar program berjalan lancar.


LANGKAH 2: INSTAL PYTHON
Pastikan komputer Anda sudah terinstal Python.
1. Cek apakah sudah ada dengan membuka Terminal/CMD lalu ketik: python --version
2. Jika belum ada, download dan instal Anaconda

LANGKAH 3: INSTAL PUSTAKA TAMBAHAN (LIBRARY)
Aplikasi ini butuh beberapa alat bantu agar bisa berjalan.
1. Buka "Command Prompt" (CMD) atau "PowerShell" di komputer Anda.
2. Ketik perintah di bawah ini, lalu tekan ENTER:

   pip install streamlit pandas plotly numpy

3. Tunggu hingga proses download dan instalasi selesai (muncul tulisan Successfully installed).


LANGKAH 4: MENJALANKAN APLIKASI
1. Di dalam CMD/Terminal, masuk ke folder tempat Anda menyimpan file proyek.
   Contoh: cd Documents/NamaFolderProyek
2. Ketik perintah berikut untuk menyalakan website:

   streamlit run project.py

3. Website akan otomatis terbuka di browser Anda (Chrome/Edge).
   Jika tidak terbuka otomatis, ketik alamat alamat yang tertera di browser


LANGKAH 5: MEMATIKAN APLIKASI
Jika sudah selesai, kembali ke layar hitam (CMD/Terminal) tadi.
Tekan tombol "Ctrl" + "C" secara bersamaan di keyboard untuk berhenti.


BAGIAN 2: PANDUAN PENGGUNAAN WEBSITE


Setelah website terbuka, berikut cara menggunakannya untuk menganalisis 
penghematan listrik rumah Anda.

A. MENU PENGATURAN (PANEL KIRI)
Di sini Anda memasukkan data kondisi rumah Anda saat ini.

1. Pilih Lokasi (Provinsi)
   - Klik kotak pilihan dan cari provinsi tempat tinggal Anda.
   - Aplikasi akan otomatis mengambil data intensitas matahari dan 
     faktor emisi (polusi) listrik di daerah tersebut.

2. Tagihan Listrik per Bulan
   - Masukkan rata-rata biaya listrik yang Anda bayar ke PLN setiap bulan.
   - Contoh: Ketik 500000 untuk lima ratus ribu rupiah.

3. Kapasitas 1 Modul PV (Wp)
   - Pilih spesifikasi panel surya yang ingin digunakan.
   - Standar saat ini biasanya 450 Wp atau 550 Wp.

4. Jumlah Modul PV
   - Tentukan berapa lembar panel surya yang ingin dipasang di atap.
   - Semakin banyak panel, semakin besar penghematan (tapi modal awal juga lebih besar).


B. DASHBOARD ANALISIS (LAYAR KANAN)
Hasil perhitungan akan muncul secara otomatis dan berubah setiap kali Anda 
mengganti input.

1. Kartu Skor (Bagian Atas)
   - Hemat Biaya Bulanan: Estimasi uang yang bisa anda hemat per bulannya.
   - Masa Balik Modal (ROI): Perkiraan berapa tahun uang penghematan listrik 
     bisa menutupi biaya pembelian alat panel surya.
   - Emisi CO2 Dicegah: Kontribusi Anda dalam mengurangi polusi udara per bulan.
   - Skor Kemandirian: Persentase kebutuhan listrik rumah yang berhasil dipenuhi 
     oleh panel surya sendiri (tanpa PLN).

2. Grafik Visual (Tab Menu)
   - Tab 1 (Analisis Biaya): Grafik batang perbandingan tagihan "Sebelum" vs "Sesudah".
   - Tab 2 (Proyeksi Jangka Panjang): Garis grafik keuntungan finansial Anda selama 15 tahun ke depan.
   - Tab 3 (Estimasi Energi Bulanan): Grafik batang untuk menganalisis energi yang dihasilkan setiap bulan, dan perbandingan musim.
   - Tab 4 (Dampak Lingkungan): Diagram donat yang menunjukkan seberapa "Hijau" energi rumah Anda.
   - Tab 5 (Detail Teknis): Tabel rincian angka lengkap untuk keperluan teknis.


CATATAN TAMBAHAN

- Akurasi: Perhitungan didasarkan pada data rata-rata historis radiasi 
  matahari. Hasil aktual di lapangan bisa sedikit berbeda tergantung cuaca.
- Tampilan: Website ini mendukung mode layar Terang (Light Mode) agar nyaman dilihat.


Dibuat menggunakan Python & Streamlit
