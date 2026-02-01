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

# --- CSS VISUAL ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Style Kotak Harga */
    .acuan-box {
        background-color: #0e1117;
        border: 1px solid #444;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .harga-besar { font-size: 24px; font-weight: bold; color: #00CC96; }
    .label-kecil { font-size: 12px; color: #aaaaaa; text-transform: uppercase; }
    
    /* Style Berita */
    .berita-box {
        background-color: #262730;
        border-left: 5px solid #FFA500;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    
    /* Style Kalkulator */
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
    st.title("🏝️ NAVIGASI")
    
    # LOGIC LOGIN ADMIN
    if 'is_admin_logged_in' not in st.session_state:
        st.session_state.is_admin_logged_in = False

    if not st.session_state.is_admin_logged_in:
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga"])
        st.divider()
        pw = st.text_input("🔐 Admin", type="password")
        if "admin_password" in st.secrets:
            if pw == st.secrets["admin_password"]:
                st.session_state.is_admin_logged_in = True
                st.rerun()
    else:
        st.success("👤 Admin Mode Aktif")
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga", "📢 Update Berita", "⚙️ Update Harga", "🗑️ Hapus Data"])
        if st.button("Logout"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    st.divider()
    # Ganti No WA ini dengan nomor lu!
    st.link_button("💬 Chat Admin (WA)", "https://wa.me/6282170713871?text=Halo%20Admin%20Mentawai%20Market,%20saya%20mau%20tanya...")
    st.caption("Butuh bantuan? Chat kami.")

# --- HELPER DATA ---
def get_settings():
    if db:
        try:
            doc = db.collection('settings').document('general').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}

settings_data = get_settings()
# Kalau data kosong, kasih default biar gak error
if not settings_data:
    settings_data = {"berita": "Selamat datang di Mentawai Smart Market!", "tanggal_berita": "-"}

def get_harga_acuan():
    if db:
        try:
            doc = db.collection('settings').document('harga_padang').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}
acuan_data = get_harga_acuan()

# ================= MENU 1: DASHBOARD =================
if menu == "🏠 Dashboard":
    st.title("📡 Pusat Pantauan Harga")
    
    # 📢 FITUR BARU: PAPAN PENGUMUMAN
    if settings_data.get('berita'):
        st.markdown(f"""
        <div class="berita-box">
            <h3>📢 KABAR PASAR ({settings_data.get('tanggal_berita', '-')})</h3>
            <p style="font-size: 18px;">{settings_data.get('berita')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # HARGA CENGKEH DETAIL
    st.markdown("### 🍂 Harga Cengkeh (Gudang Padang)")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">SUPER (Ekspor)</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Super', 0):,}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">STANDAR</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Biasa', 0):,}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">GAGANG</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Gagang', 0):,}</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">MINYAK/BUBUK</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Minyak', 0):,}</div></div>""", unsafe_allow_html=True)

    # KOMODITAS LAIN
    st.markdown("### 🥥 Komoditas Lainnya")
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">KOPRA</div><div class="harga-besar">Rp {acuan_data.get('Kopra', 0):,}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">PINANG</div><div class="harga-besar">Rp {acuan_data.get('Pinang', 0):,}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">GAMBIR</div><div class="harga-besar">Rp {acuan_data.get('Gambir', 0):,}</div></div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("🏝️ Laporan Warga")
    
    # TABEL LAPORAN
    filter_jenis = st.multiselect("Filter Jenis:", ["Cengkeh Super", "Cengkeh Biasa", "Kopra", "Pinang"])
    
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(50).stream()
        data_table = []
        for d in docs:
            dt = d.to_dict()
            item_name = dt.get('item')
            if filter_jenis and item_name not in filter_jenis: continue
                
            data_table.append({
                "Barang": item_name,
                "Harga": f"Rp {dt.get('harga_angka', 0):,}",
                "Lokasi": dt.get('lokasi'),
                "Catatan": dt.get('catatan', '-'),
                "Waktu": dt.get('waktu').strftime("%d/%m %H:%M") if dt.get('waktu') else "-"
            })
        st.dataframe(pd.DataFrame(data_table), use_container_width=True, hide_index=True)

# ================= MENU 2: KALKULATOR =================
elif menu == "🧮 Cek Kejujuran":
    st.title("🧮 Kalkulator Cekik Agen")
    c_kiri, c_kanan = st.columns(2)
    with c_kiri:
        kom = st.selectbox("Jenis Barang:", ["Cengkeh Super", "Cengkeh Biasa", "Gagang Cengkeh", "Kopra", "Pinang"])
        key_map = {"Cengkeh Super": "Cengkeh_Super", "Cengkeh Biasa": "Cengkeh_Biasa", "Gagang Cengkeh": "Cengkeh_Gagang", "Kopra": "Kopra", "Pinang": "Pinang"}
        db_key = key_map.get(kom, "Kopra")
        harga_pusat = acuan_data.get(db_key, 0)
        
        st.info(f"Patokan Padang: **Rp {harga_pusat:,}**")
        tawaran = st.number_input("Tawaran Agen (Rp):", step=500)

    with c_kanan:
        st.write("### 📊 Analisa:")
        if tawaran > 0 and harga_pusat > 0:
            selisih = harga_pusat - tawaran
            persen = (selisih / harga_pusat) * 100
            st.metric("Potongan Agen", f"Rp {selisih:,} /kg")
            if persen < 20: st.markdown(f"""<div class="hasil-box success">✅ HARGA ISTIMEWA!</div>""", unsafe_allow_html=True)
            elif persen < 40: st.markdown(f"""<div class="hasil-box warning">👌 HARGA WAJAR</div>""", unsafe_allow_html=True)
            else: st.markdown(f"""<div class="hasil-box danger">🛑 HARGA MENCEKIK!</div>""", unsafe_allow_html=True)

# ================= MENU 3: LAPOR =================
elif menu == "📝 Lapor Harga":
    st.title("📝 Lapor Harga Lapangan")
    with st.form("lapor"):
        item = st.selectbox("Barang", ["Cengkeh Super", "Cengkeh Biasa", "Gagang", "Kopra", "Pinang"])
        price = st.number_input("Harga (Rp)", step=500)
        loc = st.text_input("Lokasi", placeholder="Nama Desa")
        note = st.text_input("Catatan", placeholder="Nama Agen / Info")
        if st.form_submit_button("Kirim"):
            if price > 0:
                db.collection('mentawai_v2').add({"item": item, "harga_angka": price, "lokasi": loc, "catatan": note, "waktu": datetime.datetime.now()})
                st.success("Terkirim!")
                st.rerun()

# ================= MENU 4: UPDATE BERITA (BARU!) =================
elif menu == "📢 Update Berita":
    st.title("📢 Update Kabar Pasar")
    st.info("Tulis alasan kenapa harga naik/turun di sini. Info ini akan muncul di halaman depan.")
    
    current_news = settings_data.get('berita', '')
    
    with st.form("news_form"):
        news_text = st.text_area("Isi Berita/Pengumuman:", value=current_news, height=150)
        if st.form_submit_button("Terbitkan Berita 🚀"):
            db.collection('settings').document('general').set({
                "berita": news_text,
                "tanggal_berita": datetime.datetime.now().strftime("%d %b %Y")
            })
            st.success("Berita berhasil diterbitkan!")
            st.rerun()

# ================= MENU 5: UPDATE HARGA =================
elif menu == "⚙️ Update Harga":
    st.title("⚙️ Update Harga Pusat")
    st.link_button("🔍 Cek Google Cengkeh", "https://www.google.com/search?q=harga+cengkeh+padang+hari+ini")
    
    with st.form("update_detail"):
        c1, c2 = st.columns(2)
        h_super = c1.number_input("Super", value=acuan_data.get('Cengkeh_Super', 0))
        h_biasa = c2.number_input("Biasa", value=acuan_data.get('Cengkeh_Biasa', 0))
        c3, c4 = st.columns(2)
        h_gagang = c3.number_input("Gagang", value=acuan_data.get('Cengkeh_Gagang', 0))
        h_minyak = c4.number_input("Minyak/Bubuk", value=acuan_data.get('Cengkeh_Minyak', 0))
        st.divider()
        h_kopra = st.number_input("Kopra", value=acuan_data.get('Kopra', 0))
        h_pinang = st.number_input("Pinang", value=acuan_data.get('Pinang', 0))
        h_gambir = st.number_input("Gambir", value=acuan_data.get('Gambir', 0))
        
        if st.form_submit_button("Simpan Harga"):
            db.collection('settings').document('harga_padang').set({
                "Cengkeh_Super": h_super, "Cengkeh_Biasa": h_biasa, "Cengkeh_Gagang": h_gagang, 
                "Cengkeh_Minyak": h_minyak, "Kopra": h_kopra, "Pinang": h_pinang, "Gambir": h_gambir
            }, merge=True)
            st.success("Tersimpan!")
            st.rerun()

# ================= MENU 6: HAPUS DATA =================
elif menu == "🗑️ Hapus Data":
    st.title("🗑️ Hapus Laporan")
    docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(20).stream()
    for doc in docs:
        d = doc.to_dict()
        with st.container(border=True):
            c1, c2 = st.columns([4,1])
            with c1: st.write(f"**{d.get('item')}** - Rp {d.get('harga_angka', 0):,} ({d.get('lokasi')})")
            with c2: 
                if st.button("Hapus", key=doc.id):
                    db.collection('mentawai_v2').document(doc.id).delete()
                    st.rerun()
