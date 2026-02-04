# ======================================================
# IMPORT LIBRARY
# ======================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from gsheet_utils import sheet_balita

import streamlit as st
import pandas as pd
# Import client gspread dan spreadsheet dari utils Anda
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
        # Buka spreadsheet utama
        sh = client.open_by_key(SPREADSHEET_ID)
        
        # Ambil data dari sheet 'Balita'
        sheet_balita = sh.worksheet("Balita")
        df_balita = pd.DataFrame(sheet_balita.get_all_records())
        
        # Ambil data dari sheet 'Pengukuran' (Pastikan nama sheet sesuai di GSheets Anda)
        sheet_ukur = sh.worksheet("Pengukuran")
        df_ukur = pd.DataFrame(sheet_ukur.get_all_records())
        
        return df_balita, df_ukur
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Panggil fungsi load_data
df_balita, df_ukur = load_data()

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
    gizi_buruk = df_ukur[df_ukur["status_bbtb"] == "Gizi Buruk"]
    st.metric("⚠️ Balita Gizi Buruk", len(gizi_buruk))

st.divider()

# ======================================================
# GRAFIK TREN KUNJUNGAN (PER TAHUN)
# ======================================================
st.subheader("📈 Tren Kunjungan Balita per Tahun")

if not df_ukur.empty:

    # ==================================================
    # KONVERSI TANGGAL (ISO ONLY – WAJIB)
    # ==================================================
    df_ukur["tanggal_pengukuran"] = pd.to_datetime(
        df_ukur["tanggal_pengukuran"],
        errors="coerce"
    )

    # Buang data dengan tanggal tidak valid
    df_ukur = df_ukur.dropna(subset=["tanggal_pengukuran"])

    # ==================================================
    # AGREGASI PER TAHUN
    # ==================================================
    df_ukur["Tahun"] = df_ukur["tanggal_pengukuran"].dt.year

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

