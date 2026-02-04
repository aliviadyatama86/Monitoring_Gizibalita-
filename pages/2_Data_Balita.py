import streamlit as st
import pandas as pd
from datetime import date
from utils import map_posyandu
import gsheet_utils

# ==========================
# CONFIG STREAMLIT
# ==========================
st.set_page_config(page_title="Data Balita", layout="wide")
st.title("🧒 Data Balita")

if "df_view" not in st.session_state:
    st.session_state.df_view = gsheet_utils.load_balita()

def refresh_data():
    st.session_state.df_view = gsheet_utils.load_balita()

# ==========================
# FORM INPUT BALITA BARU
# ==========================
with st.form("form_balita"):
    st.subheader("➕ Input Balita Baru")
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama Anak")
        tgl_lahir = st.date_input("Tanggal Lahir", date.today())
        jk = st.selectbox("Jenis Kelamin", ["L", "P"])
        ibu = st.text_input("Nama Ibu")
    with col2:
        dusun = st.text_input("Dusun")
        alamat = st.text_area("Alamat")
        rt_input = st.number_input("RT", min_value=1, step=1)
        rw_input = st.number_input("RW", min_value=1, step=1)
    
    submit_input = st.form_submit_button("💾 Simpan Data Balita")

if submit_input:
    if not nama.strip() or not ibu.strip():
        st.error("❌ Nama Anak dan Nama Ibu wajib diisi.")
    else:
        try:
            posyandu_hasil = map_posyandu(rt_input, rw_input)
            df_all = st.session_state.df_view
            
            # CEK DUPLIKAT
            duplikat = df_all[
                (df_all["Nama Anak"].str.upper() == nama.upper()) & 
                (df_all["Nama Ibu"].str.upper() == ibu.upper()) &
                (df_all["Tanggal Lahir"] == tgl_lahir.strftime("%d-%m-%Y"))
            ]
            
            if duplikat.empty:
                # ==========================================================
                # REVISI FINAL: MENGGUNAKAN LIST AGAR KOLOM TIDAK BERGESER
                # Urutan sesuai Tabel GSheet: Nama, Ibu, Tgl, JK, Desa, Dusun, Alamat, RT, RW, Posyandu
                # ==========================================================
                data_list_final = [
                    nama.upper(),                   # Kolom A
                    ibu.upper(),                    # Kolom B
                    tgl_lahir.strftime("%d-%m-%Y"), # Kolom C
                    jk,                             # Kolom D
                    "MLESE",                        # Kolom E
                    dusun.upper(),                  # Kolom F
                    alamat,                         # Kolom G
                    int(rt_input),                  # Kolom H
                    int(rw_input),                  # Kolom I
                    posyandu_hasil                  # Kolom J
                ]
                
                # Kirim list ke gsheet_utils
                gsheet_utils.insert_balita(data_list_final)
                
                st.success(f"✅ Berhasil disimpan! Kelompok: {posyandu_hasil}")
                refresh_data()
                st.rerun() 
            else:
                st.warning(f"⚠ Balita ini sudah terdaftar sebelumnya.")
                
        except ValueError as e:
            st.error(f"⚠️ {str(e)}")

# ==========================
# TABEL DATA BALITA
# ==========================
st.subheader("📋 Data Balita Terdaftar")
df_display = st.session_state.df_view.copy()

if not df_display.empty:
    def apply_mapping(row):
        try: return map_posyandu(row['RT'], row['RW'])
        except: return "Tidak Terdaftar"

    df_display['Posyandu'] = df_display.apply(apply_mapping, axis=1)

    df_unique = df_display.drop_duplicates(
        subset=["Nama Anak", "Nama Ibu", "Tanggal Lahir"], 
        keep="first"
    ).sort_values("Nama Anak").reset_index(drop=True)
    
    df_unique.insert(0, 'No.', range(1, len(df_unique) + 1))
    
    # Tampilkan kolom sesuai urutan visual yang diinginkan
    kolom_tampil = ["No.", "Nama Anak", "Nama Ibu", "Tanggal Lahir", "Jenis Kelamin", "Posyandu", "Dusun", "Alamat"]
    
    st.dataframe(df_unique[kolom_tampil], use_container_width=True, height=400, hide_index=True)
else:
    st.info("Belum ada data balita.")

# ==========================
# FORM EDIT / HAPUS (Pastikan Indentasi Rapi)
# ==========================
st.divider()
st.subheader("✏️ Edit / Hapus Data Balita")

if not df_display.empty:
    list_pilihan = df_unique.index.tolist()
    selected_idx = st.selectbox(
        "Pilih Balita yang ingin dikelola",
        list_pilihan,
        format_func=lambda i: f"{df_unique.loc[i, 'Nama Anak']} (Ibu: {df_unique.loc[i, 'Nama Ibu']})"
    )
    
    balita_sel = df_unique.loc[selected_idx]
    
    try:
        # Mencari index asli di df_display (GSheet)
        original_index = df_display[
            (df_display["Nama Anak"] == balita_sel["Nama Anak"]) & 
            (df_display["Nama Ibu"] == balita_sel["Nama Ibu"]) &
            (df_display["Tanggal Lahir"] == balita_sel["Tanggal Lahir"])
        ].index[0]
    except IndexError:
        st.error("Data tidak ditemukan.")
        st.stop()

    with st.form("form_edit_balita"):
        c_e1, c_e2 = st.columns(2)
        with c_e1:
            enama = st.text_input("Nama Anak", balita_sel["Nama Anak"])
            eibu = st.text_input("Nama Ibu", balita_sel["Nama Ibu"])
            ert = st.number_input("RT Edit", value=int(balita_sel["RT"]), min_value=1)
        with c_e2:
            erw = st.number_input("RW Edit", value=int(balita_sel["RW"]), min_value=1)
            edusun = st.text_input("Dusun", balita_sel["Dusun"])
            ealamat = st.text_area("Alamat", balita_sel["Alamat"])
            
        btn_col1, btn_col2 = st.columns(2)
        update_clicked = btn_col1.form_submit_button("💾 Update Data")
        delete_clicked = btn_col2.form_submit_button("🗑️ Hapus Balita")

    # PERBAIKAN INDENTASI DI SINI:
    if update_clicked:
        try:
            eposyandu = map_posyandu(ert, erw)
            
            # Gunakan LIST agar urutan kolom di GSheet aman (A-J)
            data_upd_list = [
                enama.upper(),                  # A: Nama Anak
                eibu.upper(),                   # B: Nama Ibu
                balita_sel["Tanggal Lahir"],    # C: Tgl Lahir
                balita_sel["Jenis Kelamin"],    # D: JK
                "MLESE",                        # E: Desa
                edusun.upper(),                 # F: Dusun
                ealamat,                        # G: Alamat
                int(ert),                       # H: RT
                int(erw),                       # I: RW
                eposyandu                       # J: Posyandu
            ]
            
            # Panggil fungsi yang baru kita ganti di gsheet_utils
            gsheet_utils.update_balita_by_index(int(original_index), data_upd_list)
            
            st.success(f"✅ Berhasil diupdate!")
            refresh_data()
            st.rerun()
        except Exception as e:
            st.error(f"⚠️ Update Gagal: {str(e)}")

    if delete_clicked:
        try:
            gsheet_utils.delete_balita_by_index(int(original_index))
            st.warning("🗑️ Data dihapus!")
            refresh_data()
            st.rerun()
        except Exception as e:
            st.error(f"⚠️ Gagal menghapus: {e}")