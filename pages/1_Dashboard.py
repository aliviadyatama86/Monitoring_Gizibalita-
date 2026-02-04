# ======================================================
# IMPORT LIBRARY
# ======================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from gsheet_utils import client, SPREADSHEET_ID

# ======================================================
# KONFIGURASI HALAMAN
# ======================================================
st.set_page_config(
    page_title="Dashboard - Monitoring Gizi Balita",
    layout="wide"
)

# ======================================================
# LOAD DATA DARI GOOGLE SHEETS
# ======================================================
def load_data():
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        df_balita = pd.DataFrame(sh.worksheet("Balita").get_all_records())
        df_ukur = pd.DataFrame(sh.worksheet("Pengukuran").get_all_records())
        
        # TAMBAHKAN DUA BARIS INI:
        df_balita.columns = df_balita.columns.str.strip()
        df_ukur.columns = df_ukur.columns.str.strip()
        
        return df_balita, df_ukur
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ======================================================
# JUDUL DASHBOARD
# ======================================================
st.title("📊 Dashboard Monitoring Gizi Balita")

# ======================================================
# METRIC RINGKASAN
# ======================================================
col1, col2 = st.columns(2)

with col1:
    st.metric("👶 Total Balita", len(df_balita))

with col2:
    # Menggunakan nama kolom yang sesuai dengan Google Sheets
    kolom_status = "Status BB/TB" 
    if kolom_status in df_ukur.columns:
        gizi_buruk = df_ukur[df_ukur[kolom_status] == "Gizi Buruk"]
        st.metric("⚠️ Balita Gizi Buruk", len(gizi_buruk))
    else:
        st.error(f"Kolom '{kolom_status}' tidak ditemukan!")

# ======================================================
# GRAFIK TREN KUNJUNGAN (PER TAHUN)
# ======================================================
st.subheader("📈 Tren Kunjungan Balita per Tahun")

if not df_ukur.empty:
    # 1. Definisikan nama kolom sesuai Google Sheets
    kolom_tgl = "Tanggal Pengukuran" 

    if kolom_tgl in df_ukur.columns:
        # 2. Konversi tanggal menggunakan nama kolom yang benar
        df_ukur[kolom_tgl] = pd.to_datetime(
            df_ukur[kolom_tgl],
            errors="coerce"
        )

        # 3. Buang data dengan tanggal tidak valid
        df_ukur = df_ukur.dropna(subset=[kolom_tgl])
        
        # Lanjutkan ke proses pembuatan grafik Anda...
    else:
        st.error(f"Kolom '{kolom_tgl}' tidak ditemukan di Google Sheets Anda.")

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




