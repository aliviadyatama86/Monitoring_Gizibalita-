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
# REVISI: Pastikan tanggal bersih tanpa jam sejak awal
df_ukur["Tanggal Pengukuran"] = pd.to_datetime(df_ukur["Tanggal Pengukuran"], dayfirst=True, errors="coerce")
df_ukur = df_ukur.dropna(subset=["Tanggal Pengukuran"])

# Filter 5 Tahun Terakhir
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
# MODE TAMPILAN
# =====================================================
mode = st.radio("Mode Tampilan", ["Individu", "Seluruh Data"])

if mode == "Individu":
    daftar_nama = sorted(df_filtered["Nama Anak"].unique().tolist())
    nama_pilihan = st.selectbox("Pilih Balita", daftar_nama)
    df_plot = df_filtered[df_filtered["Nama Anak"] == nama_pilihan].copy()
    
    # --- TAMBAHAN: RINGKASAN DETEKSI DINI (INDIVIDU) ---
    latest_data = df_plot.sort_values("Tanggal Pengukuran").iloc[-1]
    
    st.markdown("---")
    st.subheader(f"🔍 Interpretasi Hasil: {nama_pilihan}")
    
    s_bbu = latest_data["Status BB/U"]
    s_tbu = latest_data["Status TB/U"]
    s_bbtb = latest_data["Status BB/TB"]

    # REVISI: Narasi menggunakan tanggal tanpa jam
    tgl_str = latest_data["Tanggal Pengukuran"].strftime('%d-%m-%Y')

    if "Gizi Buruk" in s_bbtb or "Sangat Pendek" in s_tbu:
        msg_color = "error"
        kesimpulan = "🚨 Perlu Rujukan / Intervensi Segera"
        narasi = f"Hasil deteksi ({tgl_str}) menunjukkan indikasi masalah gizi kronis. Segera lakukan rujukan medis."
    elif "Kurang" in s_bbu or "Pendek" in s_tbu or "Gizi Kurang" in s_bbtb:
        msg_color = "warning"
        kesimpulan = "⚠️ Perlu Pemantauan Intensif"
        narasi = f"Hasil deteksi ({tgl_str}) berada di zona waspada. Perlu evaluasi pola makan segera."
    else:
        msg_color = "success"
        kesimpulan = "✅ Perkembangan Baik"
        narasi = f"Hingga ({tgl_str}), pertumbuhan anak sesuai kurva normal WHO. Pertahankan nutrisi seimbang."

    c1, c2, c3 = st.columns(3)
    c1.metric("Status BB/U", s_bbu)
    c2.metric("Status TB/U", s_tbu)
    c3.metric("Status BB/TB", s_bbtb)
    
    if msg_color == "success": st.success(f"**{kesimpulan}**: {narasi}")
    elif msg_color == "warning": st.warning(f"**{kesimpulan}**: {narasi}")
    else: st.error(f"**{kesimpulan}**: {narasi}")

else:
    df_plot = df_filtered.copy()
    nama_pilihan = "Semua Balita"

df_plot = df_plot.sort_values("Tanggal Pengukuran")

# --- GRAFIK TREN Z-SCORE ---
st.subheader(f"📈 Grafik Tren Z-Score (Data Bulanan): {nama_pilihan}")

metrics = [
    ("Z-Score BB/U", "Berat Badan menurut Umur (BB/U)"),
    ("Z-Score TB/U", "Tinggi Badan menurut Umur (TB/U)"),
    ("Z-Score BB/TB", "Berat Badan menurut Tinggi Badan (BB/TB)")
]

for col_name, label_text in metrics:
    fig, ax = plt.subplots(figsize=(10, 4))
    
    if mode == "Individu":
        x_labels = df_plot["Tanggal Pengukuran"].dt.strftime('%m-%y')
        ax.plot(x_labels, df_plot[col_name], marker="o", linestyle="-", color="#1f77b4", label="Nilai Z-Score")
        rotation, alignment = 45, 'right'
    else:
        # Grafik Seluruh Data (Scatter + Mean Line)
        df_plot['Tahun'] = df_plot["Tanggal Pengukuran"].dt.strftime('%Y')
        x_labels = df_plot['Tahun']
        ax.scatter(x_labels, df_plot[col_name], color="#1f77b4", alpha=0.3, s=30, label="Sebaran Data Anak")
        avg_trend = df_plot.groupby('Tahun')[col_name].mean()
        ax.plot(avg_trend.index, avg_trend.values, color="blue", marker="D", linewidth=2, label="Rata-rata Tren Desa")
        rotation, alignment = 0, 'center'

    ax.axhline(0, color="green", linestyle="--", alpha=0.5, label="Median")
    ax.axhline(-2, color="red", linestyle="--", alpha=0.5, label="-2 SD")
    ax.axhline(2, color="red", linestyle="--", alpha=0.5, label="+2 SD")
    
    ax.set_ylabel(f"Nilai {col_name}") 
    ax.set_title(f"Tren {label_text}")
    plt.xticks(rotation=rotation, ha=alignment) 
    ax.legend(loc='upper left', fontsize='small')
    ax.grid(True, linestyle=':', alpha=0.6)
    st.pyplot(fig)

# =====================================================
# ANALISIS STATUS GIZI TERAKHIR
# =====================================================
st.divider()
st.subheader("📋 Analisis Status Gizi Terakhir (BB/TB)")

df_latest_status = df_plot.sort_values("Tanggal Pengukuran").groupby("Nama Anak").tail(1).copy()

col_chart, col_table = st.columns([1.3, 1])

# REVISI: Mapping warna dan kategori sesuai standar target
colors_map = {
    "Gizi Baik": "#2ecc71", "Resiko Gizi Lbh": "#3498db", 
    "Gizi Kurang": "#f1c40f", "Obesitas": "#e67e22",
    "Gizi Lebih": "#9b59b6", "Gizi Buruk": "#e74c3c"
}

with col_chart:
    summary = df_latest_status["Status BB/TB"].value_counts()
    fig_pie, ax_pie = plt.subplots(figsize=(8, 8))
    
    pie_colors = [colors_map.get(label, "#95a5a6") for label in summary.index]
    explode_values = [0.06] * len(summary) 

    wedges, texts, autotexts = ax_pie.pie(
        summary, autopct=lambda p: f'{p:.1f}%' if p > 2 else '', 
        startangle=140, colors=pie_colors, pctdistance=0.82, 
        explode=explode_values, textprops={'fontsize': 10, 'weight': 'bold'}
    )
    
    centre_circle = plt.Circle((0,0), 0.65, fc='white')
    fig_pie.gca().add_artist(centre_circle)

    legend_labels = [f'{l} : {summary[l]} Anak' for l in summary.index]
    ax_pie.legend(wedges, legend_labels, title="Status Gizi & Populasi", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    ax_pie.set_title("Distribusi Status Gizi (BB/TB)", pad=20, fontsize=14, weight='bold')
    st.pyplot(fig_pie)

with col_table:
    if mode == "Seluruh Data":
        st.write("**🔍 Filter Detail Kelompok Gizi:**")
        
        # REVISI: Dropdown mengikuti nama target yang diinginkan
        target_options = ["Gizi Buruk", "Gizi Kurang", "Gizi Baik", "Resiko Gizi Lbh", "Gizi Lebih", "Obesitas"]
        available_options = [opt for opt in target_options if opt in df_latest_status["Status BB/TB"].unique()]
        
        pilihan_filter = st.selectbox("Pilih Kategori Gizi:", available_options)
        
        df_detail = df_latest_status[df_latest_status["Status BB/TB"] == pilihan_filter].copy()
        
        # REVISI: Tanggal bersih tanpa jam
        df_detail["Tanggal"] = df_detail["Tanggal Pengukuran"].dt.strftime('%d-%m-%Y')
        
        # REVISI: Menampilkan Nama Ibu dan Posyandu
        show_cols = ["Nama Anak", "Tanggal", "Nama Ibu", "Posyandu", "Status BB/TB"]
        actual_cols = [c for c in show_cols if c in df_detail.columns]
        
        st.dataframe(df_detail[actual_cols], use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(df_detail)} anak dalam kategori {pilihan_filter}")
    else:
        st.write("**Riwayat Pengukuran:**")
        df_table = df_plot.copy()
        df_table["Tanggal"] = df_table["Tanggal Pengukuran"].dt.strftime('%m-%y')
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
