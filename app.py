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
        border: 1px solid #444;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .harga-besar {
        font-size: 24px;
        font-weight: bold;
        color: #00CC96;
    }
    .label-kecil {
        font-size: 12px;
        color: #aaaaaa;
        text-transform: uppercase;
    }
    .kategori-badge {
        background-color: #333;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
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
        st.success("👤 Admin Mode")
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga", "⚙️ Update Harga Pusat", "🗑️ Hapus Data"])
        if st.button("Logout"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    st.divider()
    with st.expander("📖 Info Kategori"):
        st.markdown("""
        **Jenis Cengkeh:**
        * **Super/AB6:** Kering sempurna, gagang utuh, bersih.
        * **Standar:** Kering biasa, campur sedikit.
        * **Gagang:** Hanya tangkai/gagang.
        * **Bubuk:** Sisa ayakan/hancuran.
        """)

# --- HELPER DATA ---
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
    
    # BAGIAN 1: CENGKEH SERIES (DETAIL)
    st.markdown("### 🍂 Harga Cengkeh (Gudang Padang)")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">SUPER (Ekspor)</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Super', 0):,}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">STANDAR (Umum)</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Biasa', 0):,}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">GAGANG (Tangkai)</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Gagang', 0):,}</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">BUBUK/MINYAK</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh_Minyak', 0):,}</div></div>""", unsafe_allow_html=True)

    # BAGIAN 2: KOMODITAS LAIN
    st.markdown("### 🥥 Komoditas Lainnya")
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">KOPRA GUDANG</div><div class="harga-besar">Rp {acuan_data.get('Kopra', 0):,}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">PINANG KUPAS</div><div class="harga-besar">Rp {acuan_data.get('Pinang', 0):,}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">GAMBIR</div><div class="harga-besar">Rp {acuan_data.get('Gambir', 0):,}</div></div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("🏝️ Laporan Lapangan Terkini")
    
    # TABEL DENGAN FILTER CANGGIH
    filter_jenis = st.multiselect("Filter Jenis:", ["Cengkeh Super", "Cengkeh Biasa", "Kopra", "Pinang"], default=None)
    
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(50).stream()
        data_table = []
        for d in docs:
            dt = d.to_dict()
            item_name = dt.get('item')
            # Filter Logic
            if filter_jenis and item_name not in filter_jenis:
                continue
                
            data_table.append({
                "Komoditas": item_name,
                "Harga Tawaran": f"Rp {dt.get('harga_angka', 0):,}",
                "Lokasi": dt.get('lokasi'),
                "Catatan": dt.get('catatan', '-'),
                "Waktu": dt.get('waktu').strftime("%d/%m %H:%M") if dt.get('waktu') else "-"
            })
        
        if data_table:
            st.dataframe(pd.DataFrame(data_table), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada laporan yang cocok.")

# ================= MENU 2: KALKULATOR (DENGAN JENIS) =================
elif menu == "🧮 Cek Kejujuran":
    st.title("🧮 Kalkulator Cekik Agen")
    
    c_kiri, c_kanan = st.columns(2)
    with c_kiri:
        # Pilihan Detail
        kom = st.selectbox("Pilih Jenis Barang:", 
            ["Cengkeh Super (Kering Sempurna)", "Cengkeh Biasa (Campur)", "Gagang Cengkeh", "Kopra", "Pinang"])
        
        # Mapping nama ke key database
        key_map = {
            "Cengkeh Super (Kering Sempurna)": "Cengkeh_Super",
            "Cengkeh Biasa (Campur)": "Cengkeh_Biasa",
            "Gagang Cengkeh": "Cengkeh_Gagang",
            "Kopra": "Kopra",
            "Pinang": "Pinang"
        }
        
        db_key = key_map.get(kom)
        harga_pusat = acuan_data.get(db_key, 0)
        
        st.info(f"Patokan Padang ({kom}):\n**Rp {harga_pusat:,} /Kg**")
        tawaran = st.number_input("Tawaran Agen (Rp):", step=500)

    with c_kanan:
        st.write("### 📊 Analisa:")
        if tawaran > 0 and harga_pusat > 0:
            selisih = harga_pusat - tawaran
            persen = (selisih / harga_pusat) * 100
            
            st.metric("Margin/Potongan Agen", f"Rp {selisih:,} /kg")
            
            if persen < 20: 
                st.markdown(f"""<div class="hasil-box success">✅ HARGA ISTIMEWA!<br>Potongan {persen:.1f}%. Langsung lepas bos!</div>""", unsafe_allow_html=True)
            elif persen < 40: 
                st.markdown(f"""<div class="hasil-box warning">👌 HARGA WAJAR<br>Potongan {persen:.1f}%. Standar ongkos kirim.</div>""", unsafe_allow_html=True)
            else: 
                st.markdown(f"""<div class="hasil-box danger">🛑 HARGA MENCEKIK!<br>Potongan {persen:.1f}%.<br>Agen cari untung kelewatan.</div>""", unsafe_allow_html=True)

# ================= MENU 3: LAPOR =================
elif menu == "📝 Lapor Harga":
    st.title("📝 Lapor Harga Lapangan")
    with st.form("lapor"):
        item = st.selectbox("Jenis Barang", ["Cengkeh Super", "Cengkeh Biasa", "Gagang Cengkeh", "Kopra", "Pinang", "Lainnya"])
        price = st.number_input("Harga Tawaran (Rp)", step=500)
        loc = st.text_input("Lokasi", placeholder="Nama Desa")
        note = st.text_input("Catatan", placeholder="Nama Agen / Kondisi Barang")
        
        if st.form_submit_button("Kirim"):
            if price > 0 and loc:
                db.collection('mentawai_v2').add({
                    "item": item, "harga_angka": price, "lokasi": loc,
                    "catatan": note, "waktu": datetime.datetime.now()
                })
                st.success("Terkirim!")
                st.rerun()

# ================= MENU 4: ADMIN UPDATE (SEMI-AUTO) =================
elif menu == "⚙️ Update Harga Pusat":
    st.title("⚙️ Pusat Kontrol Admin")
    st.info("Gunakan tombol 'Cek Google' untuk melihat harga hari ini sebelum update.")
    
    # TOMBOL AJAIB (LINK PENCARIAN GOOGLE)
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        st.link_button("🔍 Cek Google: Harga Cengkeh Padang", "https://www.google.com/search?q=harga+cengkeh+kering+padang+hari+ini")
    with col_link2:
        st.link_button("🔍 Cek Google: Harga Kopra Sumbar", "https://www.google.com/search?q=harga+kopra+sumatera+barat+hari+ini")

    st.divider()
    
    with st.form("update_detail"):
        st.write("**Update Harga Cengkeh (Per Kg):**")
        c1, c2 = st.columns(
