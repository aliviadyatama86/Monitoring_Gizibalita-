import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from gsheet_utils import client, SPREADSHEET_ID #

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard - Monitoring Gizi Balita",
    layout="wide"
)

# 2. Fungsi Load Data
def load_data():
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        # Ambil data dan bersihkan spasi nama kolom sekaligus
        df_balita = pd.DataFrame(sh.worksheet("Balita").get_all_records())
        df_balita.columns = df_balita.columns.str.strip()
        
        df_ukur = pd.DataFrame(sh.worksheet("Pengukuran").get_all_records())
        df_ukur.columns = df_ukur.columns.str.strip()
        
        return df_balita, df_ukur
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 3. Jalankan Load Data
df_balita, df_ukur = load_data()

# 4. Tampilan Dashboard
st.title("📊 Dashboard Monitoring Gizi Balita")

if not df_balita.empty:
    # --- METRIK UTAMA ---
    c1, c2 = st.columns(2)
    with c1:
        st.metric("👶 Total Balita", len(df_balita))
    with c2:
        # Gunakan nama kolom persis sesuai GSheet Anda
        kolom_status = "Status BB/TB"
        if kolom_status in df_ukur.columns:
            buruk = len(df_ukur[df_ukur[kolom_status] == "Gizi Buruk"])
            st.metric("⚠️ Balita Gizi Buruk", buruk)
        else:
            st.warning(f"Kolom '{kolom_status}' tidak ditemukan")

    st.divider()

    # --- GRAFIK TREN ---
    st.subheader("📈 Tren Kunjungan Balita per Tahun")
    kolom_tgl = "Tanggal Pengukuran" #
    
    if kolom_tgl in df_ukur.columns and not df_ukur.empty:
        # Konversi tanggal
        df_ukur[kolom_tgl] = pd.to_datetime(df_ukur[kolom_tgl], errors='coerce')
        df_ukur = df_ukur.dropna(subset=[kolom_tgl])
        
        # Hitung per tahun
        df_ukur["Tahun"] = df_ukur[kolom_tgl].dt.year
        df_tren = df_ukur.groupby("Tahun").size().reset_index(name="Jumlah")
        
        # Plotting
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df_tren["Tahun"].astype(str), df_tren["Jumlah"], marker='o', color='#1f77b4')
        ax.set_ylabel("Jumlah Kunjungan")
        ax.grid(True, linestyle='--', alpha=0.6)
        st.pyplot(fig)
    else:
        st.info("Data pengukuran belum tersedia untuk grafik.")
else:
    st.info("Menghubungkan ke Google Sheets...")

    # ==================================================
    # AGREGASI PER TAHUN
    # ==================================================
    df_ukur["Tahun"] = df_ukur[kolom_tgl].dt.year

    df_tren = (
        df_ukur
        .groupby("Tahun")
        .size()
        .reset_index(name="Jumlah Kunjungan")
        .sort_values("Tahun")
    )

    # ==================================================
    # VISUALISASI
    # ==================================================
    fig, ax = plt.subplots()
    ax.plot(
        df_tren["Tahun"],
        df_tren["Jumlah Kunjungan"],
        marker="o"
    )

    ax.set_xlabel("Tahun")
    ax.set_ylabel("Jumlah Kunjungan")
    ax.set_title("Tren Kunjungan Posyandu per Tahun")
    ax.grid(True)

    st.pyplot(fig)

else:
    st.info("Belum ada data pengukuran.")






