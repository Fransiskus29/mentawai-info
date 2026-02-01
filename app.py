import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import os

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

# --- SIDEBAR ---
with st.sidebar:
    st.title("🌴 MENTAWAI MARKET")
    
    if 'is_admin_logged_in' not in st.session_state:
        st.session_state.is_admin_logged_in = False

    if not st.session_state.is_admin_logged_in:
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga"])
        st.divider()
        pw = st.text_input("🔐 Admin Area", type="password")
        if "admin_password" in st.secrets:
            if pw == st.secrets["admin_password"]:
                st.session_state.is_admin_logged_in = True
                st.rerun()
    else:
        st.success("👤 Admin Mode")
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga", "📢 Update Berita", "⚙️ Update Harga", "🗑️ Hapus Data"])
        if st.button("Logout"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    st.divider()
    st.link_button("💬 Chat Admin (WA)", "https://wa.me/6281234567890") # GANTI NO WA DISINI
    st.caption("Pusat Info Harga Hasil Bumi Mentawai terlengkap.")

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

# LIST LENGKAP KOMODITAS (DARAT, LAUT, UDARA)
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
    
    st.markdown("### 🏙️ Harga Acuan (Gudang Padang/Ekspor)")
    
    # KITA PAKAI TABS BIAR RAPI
    tab1, tab2, tab3 = st.tabs(["🌱 HASIL TANI", "🐟 HASIL LAUT", "🦅 HASIL HUTAN"])
    
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">CENGKEH SUPER</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh Super', 0):,}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">CENGKEH BIASA</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh Biasa', 0):,}</div></div>""", unsafe_allow_html=
