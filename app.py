import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import os

# SETUP
st.set_page_config(page_title="Mentawai Smart Market", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")

# CSS KEREN
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .big-font {font-size:20px !important; font-weight: bold;}
    .stMetric {background-color: #262730; padding: 10px; border-radius: 10px; border: 1px solid #444;}
    .acuan-box {background-color: #00CC96; padding: 15px; border-radius: 10px; color: black; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# DATABASE
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

# --- SIDEBAR: NAVIGASI & ADMIN ---
with st.sidebar:
    st.title("⚖️ NAVIGASI")
    menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kewajaran Harga", "📝 Input Harga Desa"])
    
    st.divider()
    st.markdown("### 🔐 Area Admin")
    # Password simpel buat lu update harga Padang
    pw = st.text_input("Password Admin", type="password")
    is_admin = False
    if pw == "mentawai123": # Ganti password ini nanti
        is_admin = True
        st.success("Mode Admin Aktif")

# --- FUNGSI AMBIL HARGA ACUAN (PADANG) ---
def get_harga_acuan():
    try:
        doc = db.collection('settings').document('harga_padang').get()
        if doc.exists: return doc.to_dict()
        else: return {}
    except: return {}

acuan_data = get_harga_acuan()

# === HALAMAN 1: DASHBOARD ===
if menu == "🏠 Dashboard":
    st.title("📡 Pantauan Pasar")
    
    # TAMPILAN HARGA ACUAN (PADANG)
    st.markdown("### 🏙️ Harga Acuan (Padang/Eksportir)")
    st.caption("Ini harga di kota besar. Jadi patokan biar tidak ditipu terlalu jauh.")
    
    if acuan_data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Cengkeh (Padang)", f"Rp {acuan_data.get('Cengkeh', 0):,}")
        c2.metric("Kopra (Padang)", f"Rp {acuan_data.get('Kopra', 0):,}")
        c3.metric("Pinang (Padang)", f"Rp {acuan_data.get('Pinang', 0):,}")
    else:
        st.warning("Data harga Padang belum diupdate Admin.")

    st.divider()
    
    # TAMPILAN HARGA DESA (YANG DIINPUT WARGA)
    st.markdown("### 🏝️ Laporan Harga di Desa (Mentawai)")
    
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(50).stream()
        data = [{"Komoditas": d.to_dict().get('item'), "Harga Desa": d.to_dict().get('harga_angka'), "Lokasi": d.to_dict().get('lokasi'), "Ket": d.to_dict().get('catatan', '-')} for d in docs]
        
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("Belum ada laporan dari desa.")

    # FITUR KHUSUS ADMIN (UPDATE HARGA PADANG)
    if is_admin:
        st.divider()
        st.markdown("### 🛠️ Update Harga Padang (Admin Only)")
        with st.form("update_padang"):
            h_cengkeh = st.number_input("Harga Cengkeh (Padang)", value=acuan_data.get('Cengkeh', 0))
            h_kopra = st.number_input("Harga Kopra (Padang)", value=acuan_data.get('Kopra', 0))
            h_pinang = st.number_input("Harga Pinang (Padang)", value=acuan_data.get('Pinang', 0))
            
            if st.form_submit_button("Update Harga Acuan"):
                db.collection('settings').document('harga_padang').set({
                    "Cengkeh": h_cengkeh, "Kopra": h_kopra, "Pinang": h_pinang,
                    "updated_at": datetime.datetime.now()
                })
                st.success("Harga Acuan Diupdate!")
                st.rerun()

# === HALAMAN 2: KALKULATOR FAIRNESS ===
elif menu == "🧮 Cek Kewajaran Harga":
    st.title("🧮 Kalkulator 'Cekik' Agen")
    st.write("Cek apakah tawaran Pak Budi wajar atau sadis.")
    
    kom = st.selectbox("Komoditas", ["Cengkeh", "Kopra", "Pinang"])
    harga_padang = acuan_data.get(kom, 0)
    
    st.info(f"Harga di Padang saat ini: **Rp {harga_padang:,}**")
    
    tawaran = st.number_input("Berapa tawaran Pak Budi?", min_value=0, step=500)
    
    if tawaran > 0 and harga_padang > 0:
        selisih = harga_padang - tawaran
        persen_potongan = (selisih / harga_padang) * 100
        
        st.divider()
        st.write(f"💸 Selisih (Keuntungan Agen + Ongkos): **Rp {selisih:,} /kg**")
        st.write(f"✂️ Potongan: **{persen_potongan:.1f}%**")
        
        # LOGIKA KEWAJARAN (CONTOH KASAR)
        if persen_potongan < 20:
            st.success("✅ **SANGAT BAGUS!** Tawaran ini tinggi. Sikat bos!")
        elif persen_potongan < 35:
            st.info("👌 **WAJAR.** Mengingat ongkos kapal & buruh.")
        elif persen_potongan < 50:
            st.warning("⚠️ **AGAK RENDAH.** Coba tawar naik dikit.")
        else:
            st.error("🛑 **SADIS/MENCEKIK!** Potongannya lebih dari setengah harga. Awas tipu-tipu.")

# === HALAMAN 3: INPUT HARGA DESA ===
elif menu == "📝 Input Harga Desa":
    st.title("📝 Lapor Harga Pak Budi")
    with st.form("lapor_desa"):
        item = st.selectbox("Komoditas", ["Cengkeh", "Kopra", "Pinang", "Lainnya"])
        price = st.number_input("Tawaran Agen (Rp)", min_value=0)
        loc = st.text_input("Desa/Dusun", placeholder="Cth: Taileleu")
        note = st.text_input("Catatan (Opsional)", placeholder="Cth: Agen Pak Budi, belum deal")
        
        if st.form_submit_button("Kirim Laporan"):
            db.collection('mentawai_v2').add({
                "item": item, "harga_angka": price, "lokasi": loc, 
                "catatan": note, "waktu": datetime.datetime.now()
            })
            st.success("Laporan terkirim!")
