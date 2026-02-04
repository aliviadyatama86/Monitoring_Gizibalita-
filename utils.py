# ============================== utils.py ==============================

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import date

# ======================================================
# DATABASE
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "balita.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# ======================================================
# MAPPING POSYANDU BERDASARKAN RT & RW
# ======================================================
def map_posyandu(rt, rw):
    """
    Mapping RT/RW ke Posyandu di Desa Mlese.
    Jika kombinasi tidak ada, raise ValueError
    """
    try:
        rt = int(rt)
        rw = int(rw)
    except:
        raise ValueError("❌ RT dan RW harus berupa angka.")

    # Larasati 1: RT 1–3 / RW 6
    if rw == 6 and rt in [1, 2, 3]:
        return "Larasati 1"
    # Larasati 2: RT 1–2 / RW 4–5
    elif rw in [4, 5] and rt in [1, 2]:
        return "Larasati 2"
    # Larasati 3: RT 1–3 / RW 2–3
    elif rw in [2, 3] and rt in [1, 2, 3]:
        return "Larasati 3"
    # Larasati 4: RT 1–3 / RW 1
    elif rw == 1 and rt in [1, 2, 3]:
        return "Larasati 4"
    # Larasati 5: RT 1–3 / RW 7
    elif rw == 7 and rt in [1, 2, 3]:
        return "Larasati 5"
    else:
        # RT/RW tidak sesuai mapping → langsung error
        raise ValueError(f"❌ Kombinasi RT {rt} / RW {rw} tidak terdaftar di Posyandu Desa Mlese.")


# ======================================================
# HITUNG UMUR BULAN
# ======================================================
def hitung_umur_bulan(tanggal_lahir, tanggal_pengukuran=None):
    if tanggal_pengukuran is None:
        tanggal_pengukuran = date.today()

    tl = pd.to_datetime(tanggal_lahir)
    tp = pd.to_datetime(tanggal_pengukuran)

    umur = (tp.year - tl.year) * 12 + (tp.month - tl.month)
    if tp.day < tl.day:
        umur -= 1

    return max(int(umur), 0)


# ======================================================
# LOAD LMS
# ======================================================
def load_lms(path):
    df = pd.read_csv(path)

    # Normalisasi jenis kelamin
    if "jenis_kelamin" in df.columns:
        df["jenis_kelamin"] = df["jenis_kelamin"].str.upper().str.strip()

    # Konversi numerik umum LMS
    for col in ["panjang", "tinggi", "L", "M", "S"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

# ======================================================
# RUMUS Z-SCORE WHO
# ======================================================
# ================= Z-SCORE WHO =================
import numpy as np
# ======================================================
# RUMUS Z-SCORE WHO (LMS)
# ======================================================

def hitung_zscore(x, L, M, S):
    x = float(x)
    L = float(L)
    M = float(M)
    S = float(S)

    if L == 0:
        return np.log(x / M) / S
    return ((x / M) ** L - 1) / (L * S)


def hitung_z_bbtb(bb, tb, umur, jk, lms):
    jk = jk.upper()

    # WHO rounding 0.5 cm
    tb = round(tb * 2) / 2

    # Length or Height
    lorh = "L" if umur < 24 else "H"

    row = lms[
        (lms["tb"] == tb) &
        (lms["jenis_kelamin"] == jk) &
        (lms["lorh"] == lorh)
    ]

    if row.empty:
        raise ValueError(
            f"LMS BB/TB tidak ditemukan (tb={tb}, jk={jk}, lorh={lorh})"
        )

    row = row.iloc[0]
    return hitung_zscore(bb, row.L, row.M, row.S)

# ======================================================
# STATUS GIZI
# ======================================================
def status_bbu(z):
    if z < -3: return "Sangat Kurang"
    if z < -2: return "Kurang"
    if z <= 2: return "Normal"
    return "Risiko BB Lebih"

def status_tbu(z):
    if z < -3: return "Sangat Pendek"
    if z < -2: return "Pendek"
    if z <= 2: return "Normal"
    return "Tinggi"

def status_bbtb(z):
    if z < -3: return "Gizi Buruk"
    if z < -2: return "Gizi Kurang"
    if z <= 2: return "Gizi Baik"
    if z <= 3: return "Risiko Gizi Lebih"
    if z <= 5: return "Gizi Lebih"
    return "Obesitas"

# ======================================================
# ================= MODEL ML ===========================
# ======================================================
MODEL_PATH = os.path.join(BASE_DIR, "model", "model_rf_gizi_balita.sav")

def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)

def prediksi_frekuensi(X):
    model = load_model()
    if model is None:
        raise ValueError("Model ML belum tersedia")
    return model.predict(X)
