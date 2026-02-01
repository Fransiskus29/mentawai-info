import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import os
import time

# 1. SETUP PAGE
st.set_page_config(
    page_title="Mentawai Smart Market", 
    page_icon="🌴", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS VISUAL ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .acuan-box {
        background-color: #0e1117;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 5px;
    }
    .harga-besar { font-size: 20px; font-weight: bold; color: #00CC96; }
    .label-kecil { font-size: 11px; color: #aaaaaa; text-transform: uppercase; margin-bottom: 5px;}
    
    .berita-box {
        background-color: #262730;
        border-left: 5px solid #FFA500;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .hasil-box { padding: 15px; border-radius: 8px; margin-top: 10px; color: white; font-weight: bold; text-align: center; }
    .danger {background-color: #FF4B4B;} 
    .warning {background-color: #FFA500; color: black;} 
    .success {background-color: #00CC96;} 
</style>
""", unsafe_allow_html=True)

# 2. KONEKSI DATABASE
@st.cache_resource
def get_db():
    try:
        if not firebase_admin._apps:
            if "textkey" in st.secrets:
                key_dict = json.loads(st.secrets["textkey"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
        return firestore.client()
    except: return None
db = get_db()

# --- SIDEBAR (LOGIC LOGIN DIPERBAIKI) ---
with st.sidebar:
    st.title("🌴 MENTAWAI MARKET")
    
    # Inisialisasi status login
    if 'is_admin_logged_in' not in st.session_state:
        st.session_state.is_admin_logged_in = False

    # === JIKA BELUM LOGIN ===
    if not st.session_state.is_admin_logged_in:
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga"])
        st.divider()
        
        st.write("🔐 **Admin Area**")
        pw = st.text_input("Masukkan Password:", type="password", key="login_pw")
        
        # TOMBOL LOGIN (BIAR LEBIH JELAS)
        if st.button("LOGIN ADMIN"):
            if "admin_password" in st.secrets:
                if pw == st.secrets["admin_password"]:
                    st.success("Login Berhasil! 🔓")
                    st.session_state.is_admin_logged_in = True
                    time.sleep(1) # Kasih waktu baca sukses dulu
                    st.rerun()
                else:
                    st.error("❌ Password Salah Bos! Coba lagi.")
            else:
                st.error("⚠️ Password belum disetting di Secrets!")

    # === JIKA SUDAH LOGIN ===
    else:
        st.success("👤 Mode Admin: AKTIF")
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga", "📢 Update Berita", "⚙️ Update Harga", "🗑️ Hapus Data"])
        
        st.divider()
        if st.button("Logout Keluar"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    st.divider()
    st.link_button("💬 Chat Admin (WA)", "https://wa.me/6281234567890") # GANTI NO WA
    st.caption("v7.1 - Login Fixed")

# --- HELPER DATA ---
def get_settings():
    if db:
        try:
            doc = db.collection('settings').document('general').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}

def get_harga_acuan():
    if db:
        try:
            doc = db.collection('settings').document('harga_padang').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}

settings_data = get_settings()
acuan_data = get_harga_acuan()

LIST_KOMODITAS = [
    "Cengkeh Super", "Cengkeh Biasa", "Gagang Cengkeh", "Minyak Cengkeh",
    "Kopra", "Pinang", "Kakao (Coklat)", "Sagu", "Nilam", "Gambir",
    "Gurita", "Lobster", "Kerapu", "Teripang", "Ikan Asin",
    "Sarang Walet", "Manau (Rotan)", "Madu Hutan"
]

# ================= MENU 1: DASHBOARD =================
if menu == "🏠 Dashboard":
    st.title("📡 Pusat Pantauan Harga")
    
    # BERITA
    if settings_data.get('berita'):
        st.markdown(f"""<div class="berita-box"><h3>📢 INFO: {settings_data.get('tanggal_berita', '-')}</h3><p>{settings_data.get('berita')}</p></div>""", unsafe_allow_html=True)
    
    # HARGA ACUAN
    st.markdown("### 🏙️ Harga Acuan (Gudang Padang/Ekspor)")
    tab1, tab2, tab3 = st.tabs(["🌱 HASIL TANI", "🐟 HASIL LAUT", "🦅 HASIL HUTAN"])
    
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">CENGKEH SUPER</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh Super', 0):,}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">CENGKEH BIASA</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh Biasa', 0):,}</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">KOPRA</div><div class="harga-besar">Rp {acuan_data.get('Kopra', 0):,}</div></div>""", unsafe_allow_html=True)
        with c4: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">PINANG</div><div class="harga-besar">Rp {acuan_data.get('Pinang', 0):,}</div></div>""", unsafe_allow_html=True)
    with tab2:
        l1, l2, l3, l4 = st.columns(4)
        with l1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">GURITA</div><div class="harga-besar">Rp {acuan_data.get('Gurita', 0):,}</div></div>""", unsafe_allow_html=True)
        with l2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">LOBSTER</div><div class="harga-besar">Rp {acuan_data.get('Lobster', 0):,}</div></div>""", unsafe_allow_html=True)
        with l3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">TERIPANG</div><div class="harga-besar">Rp {acuan_data.get('Teripang', 0):,}</div></div>""", unsafe_allow_html=True)
        with l4: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">KERAPU</div><div class="harga-besar">Rp {acuan_data.get('Kerapu', 0):,}</div></div>""", unsafe_allow_html=True)
    with tab3:
        h1, h2, h3 = st.columns(3)
        with h1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">SARANG WALET</div><div class="harga-besar">Rp {acuan_data.get('Sarang Walet', 0):,}</div></div>""", unsafe_allow_html=True)
        with h2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">MANAU (ROTAN)</div><div class="harga-besar">Rp {acuan_data.get('Manau (Rotan)', 0):,}</div></div>""", unsafe_allow_html=True)
        with h3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">MADU HUTAN</div><div class="harga-besar">Rp {acuan_data.get('Madu Hutan', 0):,}</div></div>""", unsafe_allow_html=True)

    st.divider()
    
    # GRAFIK TREN HARGA
    st.subheader("📈 Grafik Tren Harga (Real-
