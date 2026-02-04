import streamlit as st

# ==============================
# KONFIGURASI HALAMAN
# ==============================
st.set_page_config(
    page_title="Monitoring Gizi Balita",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# CUSTOM DARK SIDEBAR
# ==============================
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #0e1117;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# HALAMAN UTAMA
# ==============================
st.title("📊 Monitoring Gizi Balita Desa Mlese")

st.markdown("""
Aplikasi ini berfungsi untuk memantau pertumbuhan dan status gizi balita usia 0–60 bulan berdasarkan standar WHO / Permenkes RI No. 2 Tahun 2020. Sistem membantu pencatatan data balita, evaluasi status gizi, serta deteksi dini masalah gizi sebagai dasar pengambilan keputusan kesehatan.

📌 **Fitur utama:**
- Dashboard ringkasan
- Pendataan balita
- Input pengukuran rutin
- Monitoring grafik & prediksi kunjungan
""")

st.info("⬅️ Gunakan menu di sidebar untuk berpindah halaman")
