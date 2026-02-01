import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import os
import altair as alt

# 1. SETUP TAMPILAN BARU (SIDEBAR MODE)
st.set_page_config(
    page_title="Mentawai Market V2", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded" # Sidebar terbuka otomatis
)

# --- CSS BARU (TEMA MODERN) ---
st.markdown("""
<style>
    /* Hilangkan elemen bawaan */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Warna latar belakang sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
    }
    
    /* Judul Besar */
    h1 {
        color: #00CC96;
        font-weight: 700;
    }
    
    /* Tombol Lapor */
    .stButton button {
        background-color: #FF4B4B;
        color: white;
        border-radius: 10px;
        font-weight: bold;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi Waktu
def format_wib(waktu_utc):
    if waktu_utc:
        wib = waktu_utc + datetime.timedelta(hours=7)
        return wib.strftime("%d %b %H:%M")
    return "-"

# 2. KONEKSI KE DATABASE BARU (V2)
@st.cache_resource
def get_db():
    try:
        if not firebase_admin._apps:
            if "textkey" in st.secrets:
                key_dict = json.loads(st.secrets["textkey"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
        return firestore.client()
    except:
        return None

db = get_db()

# --- SIDEBAR NAVIGASI (DESAIN BARU) ---
with st.sidebar:
    st.title("🏝️ NAVIGASI")
    menu = st.radio("Pilih Menu:", ["📊 Dashboard Harga", "📝 Input Data Baru"])
    st.divider()
    st.info("💡 Versi Aplikasi: 2.0 (New Database)")
    st.caption("Data lama sudah tidak ditampilkan.")

# --- HALAMAN 1: DASHBOARD ---
if menu == "📊 Dashboard Harga":
    st.title("📈 Market Monitor V2")
    st.write("Pantauan harga real-time dengan tampilan baru.")
    
    if db:
        # PENTING: KITA GANTI NAMA COLLECTION JADI 'mentawai_v2' BIAR DATANYA NOL LAGI
        docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).stream()
        
        data = []
        for doc in docs:
            d = doc.to_dict()
            data.append({
                "Komoditas": d.get('item'),
                "Harga": d.get('harga_angka'),
                "Tampilan Harga": d.get('harga_teks'),
                "Lokasi": d.get('lokasi'),
                "Waktu": format_wib(d.get('waktu'))
            })
        
        df = pd.DataFrame(data)

        # STATISTIK RINGKAS
        col1, col2, col3 = st.columns(3)
        total_data = len(df)
        col1.metric("Total Laporan", f"{total_data} Data")
        
        if not df.empty:
            avg_price = df['Harga'].mean()
            col2.metric("Rata-Rata Global", f"Rp {avg_price:,.0f}".replace(",", "."))
            col3.metric("Update Terakhir", df.iloc[0]['Waktu'])
            
            st.divider()
            
            # Filter Cepat
            filter_item = st.multiselect("Filter Komoditas:", df['Komoditas'].unique())
            if filter_item:
                df = df[df['Komoditas'].isin(filter_item)]
            
            # Tabel Baru
            st.dataframe(
                df[['Komoditas', 'Tampilan Harga', 'Lokasi', 'Waktu']],
                use_container_width=True,
                hide_index=True
            )
        else:
            col2.metric("Rata-Rata", "-")
            col3.metric("Update", "-")
            st.divider()
            st.warning("⚠️ Database Masih Kosong (Fresh). Silakan input data pertama di menu sebelah kiri!")

# --- HALAMAN 2: INPUT DATA ---
elif menu == "📝 Input Data Baru":
    st.title("📝 Form Lapor V2")
    st.success("Data yang diinput di sini akan masuk ke database baru.")
    
    with st.form("form_v2"):
        c1, c2 = st.columns(2)
        with c1:
            in_item = st.selectbox("Komoditas", ["Kopra", "Cengkeh", "Pinang", "Gurita", "Kakao", "Sagu", "Lainnya"])
            in_price = st.number_input("Harga (Rp)",step=500, min_value=0)
        with c2:
            in_loc = st.text_input("Lokasi (Desa/Kecamatan)", placeholder="Cth: Taileleu")
            in_src = st.selectbox("Sumber", ["Petani", "Pengepul", "Masyarakat"])
            
        btn = st.form_submit_button("SIMPAN DATA BARU")
        
        if btn:
            if in_price > 0 and in_loc:
                # Simpan ke folder baru 'mentawai_v2'
                db.collection('mentawai_v2').add({
                    "item": in_item,
                    "harga_angka": in_price,
                    "harga_teks": f"Rp {in_price:,}".replace(",", "."),
                    "lokasi": in_loc,
                    "sumber": in_src,
                    "waktu": datetime.datetime.now()
                })
                st.toast("Data Berhasil Masuk!")
                st.success("✅ Terkirim ke Database V2!")
            else:
                st.error("Isi harga dan lokasi dulu bos!")
