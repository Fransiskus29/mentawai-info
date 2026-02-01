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
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS FIX ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .acuan-box {
        background-color: #0e1117;
        border: 1px solid #00CC96;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .harga-besar {
        font-size: 32px;
        font-weight: bold;
        color: #00CC96;
    }
    .label-kecil {
        font-size: 14px;
        color: #aaaaaa;
    }
    .hasil-box {
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
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
    st.title("🏝️ NAVIGASI")
    
    # LOGIN ADMIN DULU BIAR MENU RAHASIA MUNCUL
    is_admin = False
    
    # Cek status login di session state (biar gak logout pas refresh)
    if 'is_admin_logged_in' not in st.session_state:
        st.session_state.is_admin_logged_in = False

    # Jika belum login, tampilkan input password
    if not st.session_state.is_admin_logged_in:
        menu_list = ["🏠 Dashboard Utama", "🧮 Cek Kejujuran Agen", "📝 Lapor Harga Desa"]
        menu = st.radio("Pilih Fitur:", menu_list)
        
        st.divider()
        pw_input = st.text_input("🔐 Admin Login", type="password")
        if "admin_password" in st.secrets:
            if pw_input == st.secrets["admin_password"]:
                st.session_state.is_admin_logged_in = True
                st.rerun() # Refresh biar menu admin muncul
    else:
        # JIKA SUDAH LOGIN ADMIN
        st.success("👤 Mode Admin: AKTIF")
        menu_list = ["🏠 Dashboard Utama", "🧮 Cek Kejujuran Agen", "📝 Lapor Harga Desa", "🗑️ Hapus Laporan Sampah"]
        menu = st.radio("Pilih Fitur:", menu_list)
        
        if st.button("Logout Admin"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    st.divider()
    with st.expander("📖 Panduan"):
        st.write("Gunakan menu Kalkulator untuk cek apakah harga agen wajar atau mencekik.")

# --- HELPER FUNCTIONS ---
def get_harga_acuan():
    if db:
        try:
            doc = db.collection('settings').document('harga_padang').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}

acuan_data = get_harga_acuan()

# ================= MENU 1: DASHBOARD =================
if menu == "🏠 Dashboard Utama":
    st.title("📡 Pusat Pantauan Harga")
    st.markdown("### 🏙️ Harga Acuan (Gudang Padang)")
    
    if acuan_data:
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">CENGKEH</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh', 0):,}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">KOPRA</div><div class="harga-besar">Rp {acuan_data.get('Kopra', 0):,}</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">PINANG</div><div class="harga-besar">Rp {acuan_data.get('Pinang', 0):,}</div></div>""", unsafe_allow_html=True)
    
    # UPDATE HARGA PADANG (ADMIN ONLY)
    if st.session_state.is_admin_logged_in:
        with st.form("update_pusat"):
            st.info("🛠️ Panel Update Harga Pusat")
            c_h1, c_h2, c_h3 = st.columns(3)
            h_cengkeh = c_h1.number_input("Cengkeh", value=acuan_data.get('Cengkeh', 0))
            h_kopra = c_h2.number_input("Kopra", value=acuan_data.get('Kopra', 0))
            h_pinang = c_h3.number_input("Pinang", value=acuan_data.get('Pinang', 0))
            if st.form_submit_button("Simpan Perubahan"):
                db.collection('settings').document('harga_padang').set({
                    "Cengkeh": h_cengkeh, "Kopra": h_kopra, "Pinang": h_pinang,
                    "updated_at": datetime.datetime.now()
                })
                st.rerun()

    st.divider()
    st.subheader("🏝️ Laporan Warga")
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(50).stream()
        data_table = []
        for d in docs:
            dt = d.to_dict()
            data_table.append({
                "Komoditas": dt.get('item'),
                "Harga": f"Rp {dt.get('harga_angka', 0):,}",
                "Lokasi": dt.get('lokasi'),
                "Catatan": dt.get('catatan', '-'),
                "Waktu": dt.get('waktu').strftime("%d/%m %H:%M") if dt.get('waktu') else "-"
            })
        st.dataframe(pd.DataFrame(data_table), use_container_width=True, hide_index=True)

# ================= MENU 2: KALKULATOR =================
elif menu == "🧮 Cek Kejujuran Agen":
    st.title("🧮 Kalkulator Anti-Tipu")
    col_kiri, col_kanan = st.columns([1,1])
    with col_kiri:
        kom = st.selectbox("Komoditas:", ["Cengkeh", "Kopra", "Pinang"])
        harga_pusat = acuan_data.get(kom, 0)
        st.info(f"Patokan Padang: **Rp {harga_pusat:,}**")
        tawaran = st.number_input("Tawaran Agen (Rp):", min_value=0, step=500)
    with col_kanan:
        if tawaran > 0 and harga_pusat > 0:
            selisih = harga_pusat - tawaran
            persen = (selisih / harga_pusat) * 100
            st.metric("Untung Agen/Ongkos", f"Rp {selisih:,} /kg")
            if persen < 25: st.markdown(f"""<div class="hasil-box success">✅ HARGA BAGUS!</div>""", unsafe_allow_html=True)
            elif persen < 45: st.markdown(f"""<div class="hasil-box warning">👌 HARGA WAJAR</div>""", unsafe_allow_html=True)
            else: st.markdown(f"""<div class="hasil-box danger">🛑 SADIS / MENCEKIK!</div>""", unsafe_allow_html=True)

# ================= MENU 3: INPUT DATA =================
elif menu == "📝 Lapor Harga Desa":
    st.title("📝 Input Laporan")
    with st.form("lapor"):
        c1, c2 = st.columns(2)
        with c1:
            in_item = st.selectbox("Item", ["Cengkeh", "Kopra", "Pinang", "Lainnya"])
            in_price = st.number_input("Harga (Rp)", min_value=0, step=500)
        with c2:
            in_loc = st.text_input("Lokasi", placeholder="Cth: Taileleu")
            in_note = st.text_input("Catatan", placeholder="Nama Agen")
        if st.form_submit_button("Kirim"):
            if in_price > 0 and in_loc:
                db.collection('mentawai_v2').add({
                    "item": in_item, "harga_angka": in_price, "lokasi": in_loc,
                    "catatan": in_note, "waktu": datetime.datetime.now()
                })
                st.success("Terkirim!")
                import time
                time.sleep(1)
                st.rerun()

# ================= MENU 4: ADMIN DELETE (BARU!) =================
elif menu == "🗑️ Hapus Laporan Sampah":
    st.title("🗑️ Area Bersih-Bersih Data")
    st.warning("Hati-hati! Data yang dihapus tidak bisa dikembalikan.")
    
    # Ambil data lengkap dengan ID dokumennya
    docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(20).stream()
    
    for doc in docs:
        d = doc.to_dict()
        doc_id = doc.id # Ini kunci buat menghapus
        
        # Tampilkan dalam kotak (Card) biar enak dilihat
        with st.container(border=True):
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"**{d.get('item')}** - Rp {d.get('harga_angka', 0):,}")
                st.caption(f"📍 {d.get('lokasi')} | 🕒 {d.get('waktu').strftime('%d %b %H:%M') if d.get('waktu') else '-'}")
                if d.get('catatan'):
                    st.caption(f"📝 *{d.get('catatan')}*")
            
            with cols[1]:
                # TOMBOL HAPUS
                if st.button("HAPUS ❌", key=doc_id):
                    db.collection('mentawai_v2').document(doc_id).delete()
                    st.toast("Data sampah berhasil dibakar! 🔥")
                    import time
                    time.sleep(1)
                    st.rerun()
