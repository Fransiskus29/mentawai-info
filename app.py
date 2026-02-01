import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import os

# 1. SETUP PAGE (Sidebar Wajib Expanded)
st.set_page_config(
    page_title="Mentawai Smart Market", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS FIX (HEADER TIDAK DI-HIDE BIAR TOMBOL SIDEBAR MUNCUL) ---
st.markdown("""
<style>
    /* Kita cuma hide footer & menu pojok kanan, Header JANGAN di-hide */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Style Kotak Harga Acuan */
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
    
    /* Style Hasil Kalkulator */
    .hasil-box {
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .danger {background-color: #FF4B4B;} /* Merah */
    .warning {background-color: #FFA500; color: black;} /* Oranye */
    .success {background-color: #00CC96;} /* Hijau */
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

# --- SIDEBAR: NAVIGASI & PANDUAN ---
with st.sidebar:
    st.title("🏝️ NAVIGASI")
    menu = st.radio("Pilih Fitur:", 
        ["🏠 Dashboard Utama", "🧮 Cek Kejujuran Agen", "📝 Lapor Harga Desa"])
    
    st.divider()
    
    # PANDUAN SINGKAT
    with st.expander("📖 Panduan Pemula"):
        st.markdown("""
        **1. Jangan Langsung Jual!**
        Cek dulu harga acuan di Padang lewat menu **Dashboard**.
        
        **2. Pakai Kalkulator!**
        Masuk ke menu **Cek Kejujuran**, masukkan tawaran agen. Kalau hasilnya MERAH, cari agen lain!
        
        **3. Bantu Sesama!**
        Kalau sudah dapat harga fix, lapor di menu **Input Harga** biar warga lain tahu.
        """)

    st.divider()
    
    # LOGIN ADMIN
    pw_input = st.text_input("🔐 Admin Login", type="password", placeholder="Password khusus...")
    is_admin = False
    
    # Cek password dari Secrets
    if "admin_password" in st.secrets:
        if pw_input == st.secrets["admin_password"]:
            is_admin = True
            st.success("Mode Admin: AKTIF")
    
    st.caption("v3.1 - Fixed Sidebar")

# --- FUNGSI BANTUAN ---
def get_harga_acuan():
    if db:
        try:
            doc = db.collection('settings').document('harga_padang').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}

acuan_data = get_harga_acuan()

# ================= MENU 1: DASHBOARD UTAMA =================
if menu == "🏠 Dashboard Utama":
    st.title("📡 Pusat Pantauan Harga")
    st.markdown("Bandingkan harga desa dengan harga pusat (Padang) untuk menghindari penipuan.")
    
    # TAMPILAN HARGA PADANG (ACUAN)
    st.markdown("### 🏙️ Harga Acuan (Gudang Padang)")
    
    if acuan_data:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="acuan-box">
                <div class="label-kecil">CENGKEH (Kering)</div>
                <div class="harga-besar">Rp {acuan_data.get('Cengkeh', 0):,}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="acuan-box">
                <div class="label-kecil">KOPRA (Gudang)</div>
                <div class="harga-besar">Rp {acuan_data.get('Kopra', 0):,}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="acuan-box">
                <div class="label-kecil">PINANG (Kupas)</div>
                <div class="harga-besar">Rp {acuan_data.get('Pinang', 0):,}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Data Harga Padang belum diupdate Admin.")

    # AREA ADMIN: UPDATE HARGA PADANG
    if is_admin:
        with st.form("update_pusat"):
            st.markdown("#### 🛠️ Update Harga Pusat (Admin Only)")
            c_h1, c_h2, c_h3 = st.columns(3)
            h_cengkeh = c_h1.number_input("Cengkeh", value=acuan_data.get('Cengkeh', 0))
            h_kopra = c_h2.number_input("Kopra", value=acuan_data.get('Kopra', 0))
            h_pinang = c_h3.number_input("Pinang", value=acuan_data.get('Pinang', 0))
            
            if st.form_submit_button("Update Database Pusat"):
                db.collection('settings').document('harga_padang').set({
                    "Cengkeh": h_cengkeh, "Kopra": h_kopra, "Pinang": h_pinang,
                    "updated_at": datetime.datetime.now()
                })
                st.toast("Harga Pusat Berhasil Diupdate!")
                st.rerun()

    st.divider()
    
    # TABEL LAPORAN DESA
    st.subheader("🏝️ Laporan Warga (Real-Time)")
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(50).stream()
        data_table = []
        for d in docs:
            dt = d.to_dict()
            waktu_str = dt.get('waktu').strftime("%d/%m %H:%M") if dt.get('waktu') else "-"
            data_table.append({
                "Komoditas": dt.get('item'),
                "Harga Tawaran": f"Rp {dt.get('harga_angka', 0):,}",
                "Lokasi": dt.get('lokasi'),
                "Catatan": dt.get('catatan', '-'),
                "Waktu": waktu_str
            })
            
        if data_table:
            st.dataframe(pd.DataFrame(data_table), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada laporan masuk. Jadilah yang pertama melapor!")

# ================= MENU 2: KALKULATOR FAIRNESS =================
elif menu == "🧮 Cek Kejujuran Agen":
    st.title("🧮 Kalkulator Anti-Tipu")
    st.write("Masukkan harga tawaran agen, sistem akan menghitung apakah itu wajar atau sadis.")
    
    col_kiri, col_kanan = st.columns([1,1])
    
    with col_kiri:
        kom = st.selectbox("Pilih Komoditas:", ["Cengkeh", "Kopra", "Pinang"])
        harga_pusat = acuan_data.get(kom, 0)
        
        st.info(f"Harga Patokan di Padang: **Rp {harga_pusat:,}**")
        
        tawaran = st.number_input("Tawaran Agen (Rp/Kg):", min_value=0, step=500)
    
    with col_kanan:
        st.write("### 📊 Analisa Sistem:")
        if tawaran > 0 and harga_pusat > 0:
            selisih = harga_pusat - tawaran
            persen = (selisih / harga_pusat) * 100
            
            st.metric("Keuntungan Agen + Ongkos", f"Rp {selisih:,} /kg")
            
            # LOGIKA VISUALISASI HASIL
            if persen < 25:
                st.markdown(f"""<div class="hasil-box success">✅ HARGA BAGUS!<br>Potongan cuma {persen:.1f}%.<br>Sikat Bos, ini tawaran tinggi!</div>""", unsafe_allow_html=True)
            elif persen < 45:
                st.markdown(f"""<div class="hasil-box warning">👌 HARGA WAJAR<br>Potongan {persen:.1f}%.<br>Masuk akal untuk ongkos & laba.</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="hasil-box danger">🛑 HARGA SADIS / MENCEKIK!<br>Potongan {persen:.1f}%.<br>Agen ambil untung kegedean. Tawar lagi atau cari agen lain!</div>""", unsafe_allow_html=True)
        else:
            st.write("Waiting for input...")

# ================= MENU 3: INPUT HARGA DESA =================
elif menu == "📝 Lapor Harga Desa":
    st.title("📝 Lapor Situasi Lapangan")
    st.write("Bantu petani lain dengan melaporkan harga tawaran agen di tempatmu.")
    
    with st.form("form_lapor"):
        c1, c2 = st.columns(2)
        with c1:
            in_item = st.selectbox("Komoditas", ["Cengkeh", "Kopra", "Pinang", "Lainnya"])
            in_price = st.number_input("Harga Tawaran (Rp)", min_value=0, step=500)
        with c2:
            in_loc = st.text_input("Lokasi (Dusun/Desa)", placeholder="Cth: Taileleu")
            in_note = st.text_input("Catatan (Nama Agen/Info Lain)", placeholder="Cth: Agen Pak Budi")
            
        if st.form_submit_button("Kirim Laporan 🚀"):
            if in_price > 0 and in_loc:
                db.collection('mentawai_v2').add({
                    "item": in_item, 
                    "harga_angka": in_price, 
                    "lokasi": in_loc, 
                    "catatan": in_note, 
                    "waktu": datetime.datetime.now()
                })
                st.success("Laporan berhasil dikirim! Terima kasih sudah berkontribusi.")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Mohon isi Harga dan Lokasi.")
