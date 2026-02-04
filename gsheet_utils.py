import pandas as pd
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from utils import map_posyandu

# ==========================
# GOOGLE SHEET CONFIG
# ==========================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_ID = "13wTe-OdWVgDDmLGIrRI50FQN_6_AlS0OMrv96nIVRFw"
BALITA_SHEET_NAME = "Balita"

# Mengambil kredensial dari Streamlit Secrets
creds_dict = st.secrets["gizi_secrets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

# Menghubungkan ke Google Sheets
client = gspread.authorize(creds)
sheet_balita = client.open_by_key(SPREADSHEET_ID).worksheet(BALITA_SHEET_NAME)

def load_balita():
    """Load data balita dari Google Sheet sebagai DataFrame"""
    data = sheet_balita.get_all_records()
    df = pd.DataFrame(data)
    
    # Kolom sesuai urutan di Google Sheet kamu (Tanpa No)
    expected_cols = ["Nama Anak", "Tanggal Lahir", "Jenis Kelamin", "Nama Ibu",
                     "Desa", "Dusun", "Alamat", "RT", "RW", "Posyandu"]
    
    if df.empty:
        return pd.DataFrame(columns=expected_cols)

    # Pastikan kolom tersedia
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""
            
    # Konversi tipe data agar tidak error saat perhitungan
    df["RT"] = pd.to_numeric(df["RT"], errors="coerce").fillna(1).astype(int)
    df["RW"] = pd.to_numeric(df["RW"], errors="coerce").fillna(1).astype(int)
    
    return df

def insert_balita(data_list):
    """
    Fungsi untuk memasukkan data ke Google Sheets.
    data_list: berisi list data [Nama, Ibu, Tgl Lahir, JK, Desa, Dusun, Alamat, RT, RW, Posyandu]
    """
    # Pastikan koneksi ke sheet sudah didefinisikan (contoh: sheet_balita)
    # Gunakan append_row langsung untuk memasukkan list tersebut
    try:
        sheet_balita.append_row(data_list)
        return True
    except Exception as e:
        print(f"Error saat insert data: {e}")
        return False
    """Tambahkan balita baru ke Google Sheet (Kolom A s/d J)"""
    # Menghapus logika ID otomatis/No, fokus pada data mentah
    row = [
        data.get("Nama Anak", "").upper(),
        data.get("Tanggal Lahir", ""),
        data.get("Jenis Kelamin", ""),
        data.get("Nama Ibu", "").upper(),
        data.get("Desa", "MLESE"),
        data.get("Dusun", "").upper(),
        data.get("Alamat", ""),
        int(data.get("RT", 1)),
        int(data.get("RW", 1)),
        data.get("Posyandu", "")
    ]
    sheet_balita.append_row(row)

def update_balita_by_index(row_index, data_list):
    """Update berdasarkan urutan baris di Google Sheet menggunakan List data"""
    # row_index adalah index dataframe (dimulai dari 0)
    # +2 karena baris 1 adalah header di GSheet
    row_number = row_index + 2 
    
    # Update Range A sampai J dengan data_list yang dikirim dari Page 2
    # Kita bungkus data_list dalam list ganda [[]] sesuai aturan library gspread
    range_label = f"A{row_number}:J{row_number}"
    sheet_balita.update(range_label, [data_list])

def delete_balita_by_index(row_index):
    """Hapus baris berdasarkan urutan di Google Sheet"""
    row_number = row_index + 2
    sheet_balita.delete_rows(row_number)

import pandas as pd
from datetime import date

# ==========================
# KONFIGURASI SHEET PENGUKURAN
# ==========================
PENGUKURAN_SHEET_NAME = "Pengukuran" 
sheet_pengukuran = client.open_by_key(SPREADSHEET_ID).worksheet(PENGUKURAN_SHEET_NAME)

def load_pengukuran():
    try:
        data = sheet_pengukuran.get_all_records()
        df = pd.DataFrame(data)
        
        # 1. Bersihkan nama kolom dari spasi
        df.columns = df.columns.str.strip()
        
        # 2. Hapus baris yang benar-benar kosong
        df = df.dropna(how='all').reset_index(drop=True)
        
        if df.empty:
            return pd.DataFrame(columns=["No", "Nama Anak", "Tanggal Pengukuran", "Umur", "BB", "TB", 
                                       "Z-Score BB/U", "Status BB/U", "Z-Score TB/U", "Status TB/U", 
                                       "Z-Score BB/TB", "Status BB/TB"])

        # 3. PAKSA kolom 'No' menjadi numerik (agar tidak error str vs int)
        if "No" in df.columns:
            df['No'] = pd.to_numeric(df['No'], errors='coerce').fillna(0).astype(int)
        else:
            df.insert(0, "No", range(1, len(df) + 1))
            
        return df
    except Exception as e:
        print(f"Error load: {e}")
        return pd.DataFrame()

def insert_pengukuran(data_list):
    try:
        # data_list[0] adalah kolom 'No' di GSheet. 
        # Kita isi dengan nomor baris berikutnya
        all_vals = sheet_pengukuran.get_all_values()
        data_list[0] = len(all_vals) 
        sheet_pengukuran.append_row(data_list, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        print(f"Error insert: {e}")
        return False

def update_pengukuran_by_id(no_id, data_list):
    try:
        # no_id + 1 karena baris 1 adalah header
        row_num = int(no_id) + 1
        range_label = f"A{row_num}:L{row_num}"
        sheet_pengukuran.update(range_label, [data_list], value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        print(f"Gagal update: {e}")
        return False

def delete_pengukuran_by_id(no_id):
    try:
        row_num = int(no_id) + 1
        sheet_pengukuran.delete_rows(row_num)
        return True
    except Exception as e:
        print(f"Gagal hapus: {e}")

        return False


