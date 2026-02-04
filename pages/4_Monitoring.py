# =====================================================
# IMPORT
# =====================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import gsheet_utils 

# =====================================================
# KONFIGURASI & LOAD DATA
# =====================================================
st.set_page_config(page_title="Monitoring Gizi Balita (WHO)", layout="wide")

st.title("📊 Monitoring Perkembangan Balita")
st.caption("Berdasarkan Standar Antropometri WHO")

df_ukur = gsheet_utils.load_pengukuran()

if df_ukur.empty:
    st.warning("⚠️ Data pengukuran belum tersedia.")
    st.stop()

# --- Preprocessing ---
df_ukur["Tanggal Pengukuran"] = pd.to_datetime(df_ukur["Tanggal Pengukuran"], dayfirst=True, errors="coerce")
df_ukur = df_ukur.dropna(subset=["Tanggal Pengukuran"])

# Filter 5 Tahun Terakhir (2021 - 2026)
df_ukur = df_ukur[df_ukur["Tanggal Pengukuran"].dt.year >= 2021]

# Memastikan tipe data numerik
cols_z = ["Z-Score BB/U", "Z-Score TB/U", "Z-Score BB/TB"]
for col in cols_z:
    df_ukur[col] = pd.to_numeric(df_ukur[col], errors='coerce').fillna(0)

# =====================================================
# LOGIKA: AMBIL PENGUKURAN TERAKHIR DI SETIAP BULAN
# =====================================================
df_ukur['Bulan_Tahun_Key'] = df_ukur['Tanggal Pengukuran'].dt.to_period('M')
df_filtered = df_ukur.sort_values("Tanggal Pengukuran").groupby(["Nama Anak", "Bulan_Tahun_Key"]).tail(1).copy()

# =====================================================
# MODE TAMPILAN & PENGATURAN SUMBU X
# =====================================================
mode = st.radio("Mode Tampilan", ["Individu", "Seluruh Data"])

if mode == "Individu":
    daftar_nama = sorted(df_filtered["Nama Anak"].unique().tolist())
    nama_pilihan = st.selectbox("Pilih Balita", daftar_nama)
    df_plot = df_filtered[df_filtered["Nama Anak"] == nama_pilihan].copy()
    
    # Pengaturan Khusus Individu: Format m-y (02-23)
    x_format = '%m-%y'
    locator = mdates.MonthLocator(interval=1)
    x_rotation = 45  # Dimiringkan agar muat
    x_ha = 'right'
else:
    df_plot = df_filtered.copy()
    nama_pilihan = "Semua Balita"
    
    # Pengaturan Seluruh Data: Tetap Tahun saja (Sudah Sesuai)
    x_format = '%Y'
    locator = mdates.YearLocator()
    x_rotation = 0   # Tahun tidak perlu miring
    x_ha = 'center'
    
df_plot = df_plot.sort_values("Tanggal Pengukuran")

# --- GRAFIK TREN ---
st.subheader(f"📈 Grafik Tren Z-Score (Data Bulanan): {nama_pilihan}")

metrics = [
    ("Z-Score BB/U", "Berat Badan menurut Umur (BB/U)"),
    ("Z-Score TB/U", "Tinggi Badan menurut Umur (TB/U)"),
    ("Z-Score BB/TB", "Berat Badan menurut Tinggi Badan (BB/TB)")
]

# Pastikan data terurut kronologis
df_plot = df_plot.sort_values("Tanggal Pengukuran")

for col_name, label_text in metrics:
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # PERBAIKAN UTAMA:
    # Menggunakan string sebagai sumbu X agar tahun yang kosong tidak direpresentasikan (categorical)
    if mode == "Individu":
        x_labels = df_plot["Tanggal Pengukuran"].dt.strftime('%m-%y')
        rotation = 45
        alignment = 'right'
    else:
        # Untuk data keseluruhan, jika ingin tetap ringkas tampilkan tahun saja
        x_labels = df_plot["Tanggal Pengukuran"].dt.strftime('%Y')
        rotation = 0
        alignment = 'center'

    # Plot menggunakan label string sebagai sumbu X
    ax.plot(x_labels, df_plot[col_name], marker="o", linestyle="-", color="#1f77b4", label="Nilai Z-Score", alpha=0.7)
    
    # Garis ambang batas WHO
    ax.axhline(0, color="green", linestyle="--", alpha=0.5, label="Median")
    ax.axhline(-2, color="red", linestyle="--", alpha=0.5, label="-2 SD")
    ax.axhline(2, color="red", linestyle="--", alpha=0.5, label="+2 SD")
    
    ax.set_ylabel(f"Nilai {col_name}") 
    ax.set_title(f"Tren {label_text}")
    
    # Terapkan rotasi
    plt.xticks(rotation=rotation, ha=alignment) 
    
    ax.legend(loc='upper left', fontsize='small')
    ax.grid(True, linestyle=':', alpha=0.6)
    st.pyplot(fig)

# =====================================================
# ANALISIS STATUS GIZI TERAKHIR (PIE CHART OPTIMAL)
# =====================================================
st.divider()
st.subheader("📋 Analisis Status Gizi Terakhir (BB/TB)")

# Ambil data terbaru per anak
df_latest_status = df_plot.sort_values("Tanggal Pengukuran").groupby("Nama Anak").tail(1).copy()

col_chart, col_table = st.columns([1.3, 1])

with col_chart:
    # Mengambil hitungan tiap status gizi
    summary = df_latest_status["Status BB/TB"].value_counts()
    
    # Setup Figure
    fig_pie, ax_pie = plt.subplots(figsize=(8, 8))
    
    # Mapping 6 Warna Target WHO
    colors_map = {
        "Gizi Baik": "#2ecc71", 
        "Resiko Gizi Lbh": "#3498db", 
        "Gizi Kurang": "#f1c40f", 
        "Obesitas": "#e67e22",
        "Gizi Lebih": "#9b59b6", 
        "Gizi Buruk": "#e74c3c"
    }
    pie_colors = [colors_map.get(label, "#95a5a6") for label in summary.index]
    
    # Efek Explode: memberi jarak pada potongan agar kategori kecil (Gizi Buruk dll) terlihat
    explode_values = [0.06] * len(summary) 

    # Plotting
    wedges, texts, autotexts = ax_pie.pie(
        summary, 
        autopct=lambda p: f'{p:.1f}%' if p > 2 else '', # Hanya tampilkan teks jika > 2% agar tidak tumpang tindih
        startangle=140, 
        colors=pie_colors,
        pctdistance=0.82, 
        explode=explode_values,
        textprops={'fontsize': 10, 'weight': 'bold', 'color': 'black'}
    )
    
    # Tambahkan Lingkaran di Tengah (Donut Chart) agar lebih modern dan bersih
    centre_circle = plt.Circle((0,0), 0.65, fc='white')
    fig_pie.gca().add_artist(centre_circle)

    # Legenda Kustom dengan Jumlah Anak
    # Ini solusi agar Nama Status dan Jumlah Anak terbaca sangat jelas
    legend_labels = [f'{l} : {summary[l]} Anak' for l in summary.index]
    
    ax_pie.legend(
        wedges, 
        legend_labels, 
        title="Status Gizi & Populasi", 
        loc="center left", 
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=10,
        frameon=False
    )
    
    ax_pie.set_title("Distribusi Status Gizi (BB/TB)", pad=20, fontsize=14, weight='bold')
    st.pyplot(fig_pie)

with col_table:
    st.write("**Riwayat Pengukuran Terakhir:**")
    df_table = df_plot.copy()
    # Format Tanggal Sesuai Permintaan (Bulan-Tahun untuk Individu)
    if mode == "Individu":
        df_table["Tanggal"] = df_table["Tanggal Pengukuran"].dt.strftime('%m-%y')
    else:
        df_table["Tanggal"] = df_table["Tanggal Pengukuran"].dt.strftime('%d-%m-%Y')  
    display_cols = ["Nama Anak", "Tanggal", "Status BB/U", "Status TB/U", "Status BB/TB"]
    st.dataframe(df_table[display_cols], use_container_width=True, hide_index=True)
# =====================================================
# EDUKASI
# =====================================================
st.markdown("### 🏥 Panduan Tindakan Tenaga Kesehatan (WHO)")
c1, c2, c3 = st.columns(3)

with c1:
    st.success("✅ **Gizi Baik / Normal (Hijau)**")
    st.write("- Pertahankan asupan nutrisi seimbang.\n- Lanjutkan pemantauan rutin di Posyandu setiap bulan.")

with c2:
    st.error("🚨 **Gizi Buruk / Kurang (Merah/Kuning)**")
    st.write("- Segera berikan PMT (Pemberian Makanan Tambahan) selama 90 hari.\n- Lakukan pelacakan penyebab dan rujukan medis jika perlu.")

with c3:
    st.warning("⚠️ **Gizi Lebih / Obesitas (Biru/Ungu)**")
    st.write("- Evaluasi pola asuh makan (batasi gula & lemak).\n- Tingkatkan aktivitas fisik dan stimulasi motorik.")