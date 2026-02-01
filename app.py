import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import os
import altair as alt

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Info Harga Mentawai", 
    page_icon="🌴", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS BIAR RAPI ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div.stButton > button:first-child {
        background-color: #00CC96;
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi Waktu WIB
def format_wib(waktu_utc):
    if waktu_utc:
        wib = waktu_utc + datetime.timedelta(hours=7)
        return wib.strftime("%d %b %Y - %H:%M WIB")
    return "-"

# 2. KONEKSI DATABASE
@st.cache_resource
def get_db():
    try:
        if not firebase_admin._apps:
            # Cek Secrets (Cloud)
            if "textkey" in st.secrets:
                key_dict = json.loads(st.secrets["textkey"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else:
                return None
        return firestore.client()
    except Exception as e:
        return None

db = get_db()

# --- JUDUL ---
st.title("🌴 Pusat Informasi Harga Mentawai")
st.write("Pantau harga hasil bumi real-time dari Siberut sampai Pagai.")
st.divider()

if not db:
    st.error("⚠️ Database belum terkoneksi. Mohon setting 'Secrets' di Dashboard Streamlit.")
    st.stop()

# --- NAVIGASI TAB ---
tab1, tab2 = st.tabs(["📊 CEK HARGA", "📝 LAPOR HARGA"])

# === TAB 1: MONITOR ===
with tab1:
    # Filter
    c1, c2 = st.columns([1, 2])
    with c1:
        pilih_komoditas = st.selectbox("📦 Pilih Komoditas:", ["Semua", "Kopra Kering", "Cengkeh", "Pinang", "Gurita", "Kakao", "Sagu", "Lainnya"])
    with c2:
        cari_lokasi = st.text_input("📍 Cari Desa/Dusun:", placeholder="Ketik nama desa...")

    # Tarik Data
    docs = db.collection('harga_realtime').order_by('waktu_ambil', direction=firestore.Query.DESCENDING).limit(200).stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        lokasi_raw = d.get('lokasi', '-')
        data.append({
            "Komoditas": d.get('komoditas'),
            "Harga": d.get('harga_angka', 0),
            "Teks Harga": d.get('range_harga'),
            "Lokasi": lokasi_raw,
            "Sumber": d.get('sumber'),
            "Waktu": format_wib(d.get('waktu_ambil'))
        })
    
    df = pd.DataFrame(data)

    # Logika Filter
    if not df.empty:
        if pilih_komoditas != "Semua":
            df = df[df['Komoditas'] == pilih_komoditas]
        if cari_lokasi:
            df = df[df['Lokasi'].str.contains(cari_lokasi, case=False, na=False)]
        
        # Tampilkan Data
        if not df.empty:
            st.dataframe(df[['Komoditas', 'Teks Harga', 'Lokasi', 'Sumber', 'Waktu']], use_container_width=True, hide_index=True)
        else:
            st.warning("Data tidak ditemukan.")
    else:
        st.info("Belum ada data di database.")

    if st.button("🔄 Refresh"):
        st.rerun()

# === TAB 2: LAPOR ===
with tab2:
    st.write("Masukkan harga terbaru dari lapangan.")
    with st.form("form_lapor"):
        c1, c2 = st.columns(2)
        with c1:
            in_kom = st.selectbox("Komoditas", ["Kopra Kering", "Cengkeh", "Pinang", "Gurita", "Kakao", "Sagu", "Lainnya"])
            in_price = st.number_input("Harga (Rp)", min_value=0, step=500)
        with c2:
            in_dusun = st.text_input("Nama Dusun", placeholder="Cth: Taileleu")
            in_kec = st.selectbox("Kecamatan", ["Sikakap", "Pagai Utara", "Pagai Selatan", "Sipora Utara", "Sipora Selatan", "Siberut Selatan", "Siberut Barat", "Siberut Utara", "Siberut Tengah"])
        
        in_sumber = st.selectbox("Sumber", ["Petani", "Pengepul", "Masyarakat"])
        
        if st.form_submit_button("KIRIM DATA 🚀"):
            if in_price > 0 and in_dusun:
                lokasi_fix = f"{in_dusun}, {in_kec}"
                db.collection("harga_realtime").add({
                    "komoditas": in_kom,
                    "harga_angka": in_price,
                    "range_harga": f"Rp {in_price:,}".replace(",", "."),
                    "waktu_ambil": datetime.datetime.now(),
                    "lokasi": lokasi_fix,
                    "sumber": in_sumber
                })
                st.success("✅ Data berhasil masuk!")
                st.rerun()
            else:
                st.error("❌ Harga dan Dusun wajib diisi.")
