# ======================================================
# IMPORT LIBRARY
# ======================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from gsheet_utils import client, SPREADSHEET_ID

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from gsheet_utils import client, SPREADSHEET_ID # Pemanggilan utils yang benar

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
        
        # Bersihkan spasi di nama kolom
        df_balita.columns = df_balita.columns.str.strip()
        df_ukur.columns = df_ukur.columns.str.strip()
        
        return df_balita, df_ukur
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Panggil fungsi agar variabel df_balita dan df_ukur tersedia
df_balita, df_ukur = load_data()

# ======================================================
# TAMPILAN DASHBOARD
# ======================================================
st.title("📊 Dashboard Monitoring Gizi Balita")

# Hanya jalankan jika data tidak kosong
if not df_balita.empty and not df_ukur.empty:
    # --- METRIC RINGKASAN ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👶 Total Balita", len(df_balita))

    with col2:
        kolom_status = "Status BB/TB" # Harus persis dengan GSheet
        if kolom_status in df_ukur.columns:
            gizi_buruk = df_ukur[df_ukur[kolom_status] == "Gizi Buruk"]
            st.metric("⚠️ Balita Gizi Buruk", len(gizi_buruk))

    st.divider()

    # --- GRAFIK TREN KUNJUNGAN ---
    st.subheader("📈 Tren Kunjungan Balita per Tahun")
    kolom_tgl = "Tanggal Pengukuran" # Harus persis dengan GSheet

    if kolom_tgl in df_ukur.columns:
        # Konversi ke datetime
        df_ukur[kolom_tgl] = pd.to_datetime(df_ukur[kolom_tgl], errors="coerce")
        df_ukur = df_ukur.dropna(subset=[kolom_tgl])
        
        # Agregasi per Tahun
        df_ukur["Tahun"] = df_ukur[kolom_tgl].dt.year
        df_tren = df_ukur.groupby("Tahun").size().reset_index(name="Jumlah")

        # Visualisasi
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df_tren["Tahun"], df_tren["Jumlah"], marker="o", color="blue")
        ax.set_xlabel("Tahun")
        ax.set_ylabel("Jumlah Kunjungan")
        st.pyplot(fig)
    else:
        st.warning(f"Kolom '{kolom_tgl}' tidak ditemukan.")
else:
    st.info("Menunggu data dari Google Sheets...")

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





