# ======================================================
# IMPORT LIBRARY
# ======================================================
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# ======================================================
# KONFIGURASI HALAMAN
# ======================================================
st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "balita.db")

# ======================================================
# LOAD DATA
# ======================================================
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df_balita = pd.read_sql("SELECT * FROM balita", conn)
    df_ukur = pd.read_sql("SELECT * FROM pengukuran", conn)
    conn.close()
    return df_balita, df_ukur


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
