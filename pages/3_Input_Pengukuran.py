import streamlit as st
import pandas as pd
from datetime import date
import gsheet_utils 
import time
from utils import (
    hitung_umur_bulan, load_lms, hitung_zscore, 
    hitung_z_bbtb, status_bbu, status_tbu, status_bbtb
)

# ================== CONFIG ==================
st.set_page_config(page_title="Input & Riwayat Pengukuran Balita", layout="wide")
st.title("📝 Input & Riwayat Pengukuran Balita")

@st.cache_data
def load_all_lms():
    return (load_lms("data/lms_bbu.csv"), load_lms("data/lms_tbu.csv"), load_lms("data/lms_bbtb.csv"))

lms_bbu, lms_tbu, lms_bbtb = load_all_lms()

def force_refresh():
    st.cache_data.clear()
    if "df_pengukuran" in st.session_state: del st.session_state.df_pengukuran
    if "df_balita" in st.session_state: del st.session_state.df_balita
    st.rerun()

# Load Data Terbaru
st.session_state.df_balita = gsheet_utils.load_balita()
st.session_state.df_pengukuran = gsheet_utils.load_pengukuran()

df_balita = st.session_state.df_balita
df_pengukuran = st.session_state.df_pengukuran

# ================== 1. FORM INPUT BARU & VALIDASI UMUR ==================
st.subheader("➕ Input Pengukuran Baru")

# 1. Gunakan .unique() agar nama balita tidak muncul berulang kali di dropdown
daftar_balita_unik = df_balita["Nama Anak"].unique().tolist()
balita_nama = st.selectbox(
    "Pilih Balita", 
    ["-- Pilih Balita --"] + sorted(daftar_balita_unik)
)

if balita_nama != "-- Pilih Balita --":
    # 2. Ambil data master balita (Jenis Kelamin & Tanggal Lahir)
    data_balita = df_balita[df_balita["Nama Anak"] == balita_nama].iloc[0]
    jk = str(data_balita["Jenis Kelamin"]).upper().strip()
    
    # 3. Konversi tanggal lahir dan hitung umur dalam bulan
    tl = pd.to_datetime(data_balita["Tanggal Lahir"], dayfirst=True, errors='coerce')
    u_bln = hitung_umur_bulan(tl)

    # --- VALIDASI UMUR DI ATAS 60 BULAN ---
    if u_bln > 60:
        st.error(f"⚠️ Balita **{balita_nama}** sudah berumur **{u_bln} bulan**. Input data hanya diperbolehkan untuk balita maksimal 60 bulan.")
    else:
        with st.form("form_input_baru"):
            st.info(f"👶 Nama: {balita_nama} | Umur: {u_bln} Bulan")
            c1, c2 = st.columns(2)
            in_bb = c1.number_input("Berat Badan (kg)", min_value=0.1, step=0.1)
            in_tb = c2.number_input("Tinggi Badan (cm)", min_value=1.0, step=0.1)
            btn_simpan = st.form_submit_button("💾 Simpan Pengukuran")

            if btn_simpan:
                try:
                    r_bbu = lms_bbu.query("umur==@u_bln and jenis_kelamin==@jk").iloc[0]
                    r_tbu = lms_tbu.query("umur==@u_bln and jenis_kelamin==@jk").iloc[0]

                    z_bbu = hitung_zscore(in_bb, r_bbu.L, r_bbu.M, r_bbu.S)
                    z_tbu = hitung_zscore(in_tb, r_tbu.L, r_tbu.M, r_tbu.S)
                    z_bbtb = hitung_z_bbtb(in_bb, in_tb, u_bln, jk, lms_bbtb)

                    # Simpan data dengan urutan kolom asli sheet Anda (A-L)
                    data_row = [
                        0, balita_nama, date.today().strftime("%d-%m-%Y"), int(u_bln),
                        float(in_bb), float(in_tb),
                        round(z_bbu, 2), status_bbu(z_bbu),
                        round(z_tbu, 2), status_tbu(z_tbu),
                        round(z_bbtb, 2), status_bbtb(z_bbtb)
                    ]
                    if gsheet_utils.insert_pengukuran(data_row):
                        st.success("✅ Berhasil Disimpan!")
                        time.sleep(1)
                        force_refresh()
                except Exception as e:
                    st.error(f"Gagal simpan atau data LMS tidak ditemukan: {e}")

# ================== 2. RIWAYAT INDIVIDU & FREKUENSI KUNJUNGAN ==================
if balita_nama != "-- Pilih Balita --":
    st.markdown("---")
    st.subheader(f"📌 Riwayat Kunjungan: {balita_nama}")
    df_ind = df_pengukuran[df_pengukuran["Nama Anak"] == balita_nama].copy()
    if not df_ind.empty:
        # Menambahkan Frekuensi Kunjungan
        df_ind.insert(0, "Kunjungan Ke-", range(1, len(df_ind) + 1))
        st.dataframe(df_ind, use_container_width=True, hide_index=True)

# ================== 3. TABEL SELURUH PENGUKURAN ==================
st.markdown("---")
st.subheader("📚 Tabel Riwayat Seluruh Pengukuran")
if not df_pengukuran.empty:
    st.dataframe(df_pengukuran, use_container_width=True, hide_index=True)

# ================== 4. CRUD (EDIT & HAPUS) ==================
st.divider()
st.subheader("✏️ Koreksi / Edit Data")

if not df_pengukuran.empty:
    # Jaminan terakhir: Pastikan kolom No adalah angka sebelum difilter
    df_pengukuran["No"] = pd.to_numeric(df_pengukuran["No"], errors='coerce').fillna(0)
    
    # Ambil data yang No-nya lebih dari 0
    df_crud = df_pengukuran[df_pengukuran["No"] > 0].copy()
    
    if not df_crud.empty:
        list_no = df_crud["No"].astype(int).tolist()
        sel_no = st.selectbox("Pilih No Data yang diperbaiki", list_no, key="select_crud")

        # Ambil baris data yang dipilih
        data_match = df_crud[df_crud["No"] == sel_no]
        
        if not data_match.empty:
            data_edit = data_match.iloc[0]
            no_id = int(data_edit["No"])
            nama_edit = str(data_edit["Nama Anak"])

            with st.form("form_edit_hapus"):
                st.warning(f"⚠️ Mengelola No: {no_id} ({nama_edit})")
                
                # Konversi BB dan TB ke float agar number_input tidak error
                bb_cur = float(pd.to_numeric(data_edit.get("BB", 0), errors='coerce') or 0.0)
                tb_cur = float(pd.to_numeric(data_edit.get("TB", 0), errors='coerce') or 0.0)

                ce1, ce2 = st.columns(2)
                upd_bb = ce1.number_input("Update BB (kg)", value=bb_cur, step=0.1)
                upd_tb = ce2.number_input("Update TB (cm)", value=tb_cur, step=0.1)
                
                c_btn1, c_btn2 = st.columns(2)
                btn_upd = c_btn1.form_submit_button("💾 Simpan Perubahan")
                btn_del = c_btn2.form_submit_button("🗑️ HAPUS DATA PERMANEN")

                if btn_upd:
                    try:
                        info_b = df_balita[df_balita["Nama Anak"] == nama_edit].iloc[0]
                        jk_e = str(info_b["Jenis Kelamin"]).upper().strip()
                        u_e = int(data_edit["Umur"])

                        # Ambil data LMS untuk hitung ulang
                        r_bbu_e = lms_bbu.query("umur==@u_e and jenis_kelamin==@jk_e").iloc[0]
                        r_tbu_e = lms_tbu.query("umur==@u_e and jenis_kelamin==@jk_e").iloc[0]
                        
                        z1 = hitung_zscore(upd_bb, r_bbu_e.L, r_bbu_e.M, r_bbu_e.S)
                        z2 = hitung_zscore(upd_tb, r_tbu_e.L, r_tbu_e.M, r_tbu_e.S)
                        z3 = hitung_z_bbtb(upd_bb, upd_tb, u_e, jk_e, lms_bbtb)

                        # Susun list update sesuai urutan sheet (A-L)
                        upd_list = [
                            no_id, nama_edit, data_edit["Tanggal Pengukuran"], u_e,
                            upd_bb, upd_tb, round(z1, 2), status_bbu(z1),
                            round(z2, 2), status_tbu(z2), round(z3, 2), status_bbtb(z3)
                        ]
                        
                        if gsheet_utils.update_pengukuran_by_id(no_id, upd_list):
                            st.success("✅ Berhasil Diperbarui!")
                            time.sleep(1)
                            force_refresh()
                    except Exception as e:
                        st.error(f"Gagal Update: {e}")

                if btn_del:
                    if gsheet_utils.delete_pengukuran_by_id(no_id):
                        st.success(f"✅ Data No {no_id} Berhasil Dihapus!")
                        time.sleep(1)
                        force_refresh()
                    else:
                        st.error("❌ Gagal menghapus data.")
    else:
        st.info("Tidak ada data pengukuran yang dapat diedit.")