# =====================================================
# IMPORT & KONFIGURASI 
# =====================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import gsheet_utils 

st.set_page_config(page_title="Monitoring Gizi Balita (WHO)", layout="wide")
st.title("📊 Monitoring Perkembangan Balita")
st.caption("Berdasarkan Standar Antropometri WHO")

df_ukur = gsheet_utils.load_pengukuran()

if df_ukur.empty:
    st.warning("⚠️ Data pengukuran belum tersedia.")
    st.stop()

# =====================================================
# 1. PREPROCESSING (DIKONSOLIDASI AGAR TIDAK DOUBLE)
# =====================================================
# Gunakan errors="coerce" sejak awal agar lebih fleksibel membaca format 2023
df_ukur["Tanggal Pengukuran"] = pd.to_datetime(df_ukur["Tanggal Pengukuran"], errors="coerce")
df_ukur = df_ukur.dropna(subset=["Tanggal Pengukuran"])

# Filter Tahun
df_ukur = df_ukur[df_ukur["Tanggal Pengukuran"].dt.year >= 2021]

# Memastikan tipe data numerik
cols_z = ["Z-Score BB/U", "Z-Score TB/U", "Z-Score BB/TB"]
for col in cols_z:
    df_ukur[col] = pd.to_numeric(df_ukur[col], errors='coerce').fillna(0)

# Ambil data terakhir per bulan per anak (Sesuai konsep Anda)
df_ukur['Bulan_Tahun_Key'] = df_ukur['Tanggal Pengukuran'].dt.to_period('M')
df_filtered = df_ukur.sort_values("Tanggal Pengukuran").groupby(["Nama Anak", "Bulan_Tahun_Key"]).tail(1).copy()

# =====================================================
# 2. LOGIKA PILIHAN DATA (PINDAHKAN KE SINI)
# =====================================================
mode = st.radio("Mode Tampilan", ["Individu", "Seluruh Data"])

if mode == "Individu":
    daftar_nama = sorted(df_filtered["Nama Anak"].unique().tolist())
    nama_pilihan = st.selectbox("Pilih Balita", daftar_nama)
    df_plot = df_filtered[df_filtered["Nama Anak"] == nama_pilihan].copy()
    
    # --- RINGKASAN DETEKSI DINI (INDIVIDU) ---
    latest_data = df_plot.sort_values("Tanggal Pengukuran").iloc[-1]
    st.markdown("---")
    st.subheader(f"🔍 Interpretasi Hasil: {nama_pilihan}")
    
    # (Logika Interpretasi Anda tetap sama)
    s_bbu = latest_data["Status BB/U"]; s_tbu = latest_data["Status TB/U"]; s_bbtb = latest_data["Status BB/TB"]
    tgl_str = latest_data["Tanggal Pengukuran"].strftime('%d-%m-%Y')

    if "Gizi Buruk" in s_bbtb or "Sangat Pendek" in s_tbu:
        st.error(f"🚨 **Perlu Rujukan**: Hasil deteksi ({tgl_str}) menunjukkan indikasi masalah gizi kronis.")
    elif "Kurang" in s_bbu or "Pendek" in s_tbu or "Gizi Kurang" in s_bbtb:
        st.warning(f"⚠️ **Waspada**: Hasil deteksi ({tgl_str}) berada di zona waspada.")
    else:
        st.success(f"✅ **Baik**: Hingga ({tgl_str}), pertumbuhan sesuai kurva normal.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Status BB/U", s_bbu); c2.metric("Status TB/U", s_tbu); c3.metric("Status BB/TB", s_bbtb)
else:
    df_plot = df_filtered.copy()
    nama_pilihan = "Semua Balita"

# Sortir df_plot sebelum masuk ke loop grafik
df_plot = df_plot.sort_values("Tanggal Pengukuran")

# =====================================================
# 3. GRAFIK TREN (PERBAIKAN SUMBU X AGAR 2023 TERLIHAT)
# =====================================================
st.subheader(f"📈 Grafik Tren Z-Score: {nama_pilihan}")

metrics = [
    ("Z-Score BB/U", "Berat Badan menurut Umur (BB/U)"),
    ("Z-Score TB/U", "Tinggi Badan menurut Umur (TB/U)"),
    ("Z-Score BB/TB", "Berat Badan menurut Tinggi Badan (BB/TB)")
]

for col_name, label_text in metrics:
    fig, ax = plt.subplots(figsize=(11, 5))
    
    if mode == "Individu":
        ax.plot(df_plot['Tanggal Pengukuran'], df_plot[col_name], 
                marker="o", linestyle="-", color="#1f77b4", label="Nilai Z-Score")
    else:
        # Scatter dengan sebaran horizontal (sesuai keinginan Anda)
        ax.scatter(df_plot['Tanggal Pengukuran'], df_plot[col_name], 
                   color="#1f77b4", alpha=0.4, s=25, edgecolors='white', linewidth=0.3, label="Data Balita")
        
        # Garis Rata-rata: Kelompokkan per 3 bulan agar tren melewati area 2023 yang kosong
        avg_trend = df_plot.groupby(df_plot["Tanggal Pengukuran"].dt.to_period("3M"))[col_name].mean()
        ax.plot(avg_trend.index.to_timestamp(), avg_trend.values, 
                color="red", marker="D", markersize=4, linewidth=1.5, label="Rata-rata Populasi")

    # FORMAT SUMBU X: Paksa tampilkan Tahun
    ax.xaxis.set_major_locator(mdates.YearLocator()) 
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    ax.axhline(0, color="green", linestyle="-", alpha=0.3, label="Median")
    ax.axhline(-2, color="red", linestyle="--", alpha=0.5, label="-2 SD")
    ax.axhline(2, color="red", linestyle="--", alpha=0.5, label="+2 SD")
    
    if not df_plot.empty:
        ax.set_ylim(df_plot[col_name].min() - 1, df_plot[col_name].max() + 1)

    ax.set_ylabel(f"Nilai {col_name}") 
    ax.set_title(f"Sebaran Tren {label_text}")
    ax.legend(loc='upper left', fontsize='small', bbox_to_anchor=(1, 1))
    ax.grid(True, linestyle=':', alpha=0.4)
    st.pyplot(fig)

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









