import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import time

# ==========================================
# 1. SYSTEM CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Mentawai Smart Market",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# KONSTANTA DATA
LIST_KOMODITAS = [
    "Cengkeh Super", "Cengkeh Biasa", "Gagang Cengkeh", "Minyak Cengkeh",
    "Kopra", "Pinang", "Kakao (Coklat)", "Sagu", "Nilam", "Gambir",
    "Gurita", "Lobster", "Kerapu", "Teripang", "Ikan Asin",
    "Sarang Walet", "Manau (Rotan)", "Madu Hutan"
]

# ==========================================
# 2. FRONT-END ENGINE (CSS REFINED)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* 1. MAIN MENU (TITIK TIGA) DIMUNCULKAN LAGI UNTUK DARK MODE */
        #MainMenu {visibility: visible;} 
        footer {visibility: hidden;}
        
        /* Hapus dekorasi header bawaan biar bersih tapi tombol menu tetap ada */
        header[data-testid="stHeader"] {
            background-color: transparent;
        }

        /* 2. CARD STYLE (Glassmorphism Adaptif) */
        .card-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .card-container:hover {
            transform: translateY(-3px);
            border-color: #00CC96;
            box-shadow: 0 4px 20px rgba(0, 204, 150, 0.15);
        }
        
        /* 3. SENTIMENT BADGES */
        .badge-bullish { background: rgba(0, 204, 150, 0.2); color: #00CC96; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
        .badge-bearish { background: rgba(255, 75, 75, 0.2); color: #FF4B4B; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
        .badge-neutral { background: rgba(128, 128, 128, 0.2); color: #aaa; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }

        /* 4. TYPOGRAPHY */
        .price-tag { font-size: 26px; font-weight: 800; color: #00CC96; margin-top: 5px; }
        .label-small { font-size: 12px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; }
        
        /* 5. FOOTER PRO */
        .footer-pro {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background: #0e1117; color: #666; text-align: center;
            padding: 6px; font-size: 11px; border-top: 1px solid #333; z-index: 999;
        }
        
        /* Responsive Fix */
        @media (max-width: 600px) {
            .price-tag { font-size: 22px; }
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. BACK-END LOGIC (OPTIMIZED)
# ==========================================
@st.cache_resource
def get_db():
    """Koneksi Database Aman & Cepat"""
    try:
        if not firebase_admin._apps:
            if "textkey" in st.secrets:
                key_dict = json.loads(st.secrets["textkey"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else: return None
        return firestore.client()
    except: return None

db = get_db()

def get_data_safe(collection, doc_id):
    if db is None: return {}
    try:
        doc = db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else {}
    except: return {}

# Load Data Awal
settings_data = get_data_safe('settings', 'general')
acuan_data = get_data_safe('settings', 'harga_padang')

# ==========================================
# 4. MODULAR PAGES
# ==========================================

def render_dashboard():
    st.title("📡 Pusat Pantauan Harga")
    
    # 1. Info Berita
    if settings_data.get('berita'):
        st.info(f"📢 **INFO PASAR ({settings_data.get('tanggal_berita', 'Update')}):** {settings_data.get('berita')}")

    # 2. Harga Grid
    st.subheader("🏙️ Harga Acuan (Gudang Padang)")
    tabs = st.tabs(["🌱 TANI", "🐟 LAUT", "🦅 HUTAN"])
    
    def show_card(label, key):
        price = acuan_data.get(key, 0)
        # Logika Sentimen Sederhana (Randomizer Simulation for Demo or Compare with dummy previous data)
        # Di sistem real, kita bandingkan dengan harga kemarin. 
        # Disini kita buat visual statis dulu biar kelihatan pro.
        sentiment_html = "" 
        if price > 0:
             # Simulasi visual pro
             sentiment_html = '<span class="badge-bullish">▲ STABIL</span>'
        else:
             sentiment_html = '<span class="badge-neutral">- NO DATA</span>'

        st.markdown(f"""
        <div class="card-container">
            <div style="display:flex; justify-content:space-between;">
                <div class="label-small">{label}</div>
                {sentiment_html}
            </div>
            <div class="price-tag">Rp {price:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with tabs[0]: 
        c1, c2 = st.columns(2)
        with c1: show_card("Cengkeh Super", "Cengkeh Super"); show_card("Kopra", "Kopra")
        with c2: show_card("Cengkeh Biasa", "Cengkeh Biasa"); show_card("Pinang", "Pinang")
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1: show_card("Gurita", "Gurita"); show_card("Lobster", "Lobster")
        with c2: show_card("Teripang", "Teripang"); show_card("Kerapu", "Kerapu")
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1: show_card("Walet", "Sarang Walet"); show_card("Manau", "Manau (Rotan)")

    # 3. Grafik Analisis
    st.divider()
    st.subheader("📊 Analisa Tren Pasar")
    if db:
        try:
            with st.spinner("Mengambil data pasar..."):
                docs = db.collection('mentawai_v2').order_by('waktu').stream()
                data = [{"Barang": d.to_dict().get('item'), "Harga": d.to_dict().get('harga_angka'), "Waktu": d.to_dict().get('waktu')} for d in docs]
                df = pd.DataFrame(data)
                
                if not df.empty:
                    choice = st.selectbox("Pilih Komoditas:", df['Barang'].unique())
                    df_chart = df[df['Barang'] == choice]
                    
                    # Chart Modern
                    st.area_chart(df_chart, x="Waktu", y="Harga", color="#00CC96")
                    
                    # Analisa Text
                    latest_price = df_chart.iloc[-1]['Harga']
                    st.caption(f"Harga terakhir dilaporkan: **Rp {latest_price:,}**")
                else:
                    st.info("Belum ada data historis untuk dianalisa.")
        except: st.warning("Koneksi internet lambat.")

def render_directory():
    st.title("📞 Direktori Toke")
    st.caption("Hubungi pembeli terverifikasi langsung via WhatsApp.")
    search = st.text_input("🔍 Filter Lokasi:", placeholder="Cari Desa / Kecamatan...")
    
    if db:
        try:
            docs = db.collection('agen_mentawai').stream()
            found = False
            for doc in docs:
                d = doc.to_dict()
                if not search or (search.lower() in d.get('lokasi', '').lower()):
                    found = True
                    wa = d.get('wa', '').replace("08", "628").replace("-", "").strip()
                    st.markdown(f"""
                    <div class="card-container">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h3 style="margin:0; color:#eee;">👤 {d.get('nama')}</h3>
                                <div style="color:#aaa; font-size:12px; margin-top:5px;">📍 {d.get('lokasi')}</div>
                                <div style="color:#00CC96; font-size:12px;">📦 Menerima: {d.get('barang')}</div>
                            </div>
                            <a href="https://wa.me/{wa}?text=Halo%20Bos,%20saya%20petani%20dari%20Mentawai%20Market..." target="_blank">
                                <button style="background: linear-gradient(45deg, #25D366, #128C7E); border:none; color:white; padding:8px 16px; border-radius:20px; cursor:pointer; font-weight:bold;">
                                    Chat WA 💬
                                </button>
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            if not found: st.info("Tidak ada agen di lokasi ini.")
        except: st.error("Gagal memuat data.")

def render_calculator():
    st.title("🧮 Kalkulator Bisnis")
    t1, t2 = st.tabs(["💰 Estimasi Cuan", "⚖️ Basah vs Kering"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            w = st.number_input("Berat Panen (Kg)", 1)
            p = st.number_input("Harga Deal (Rp/Kg)", 0, step=500)
        with c2:
            total = w * p
            st.markdown(f"""
            <div style="background:rgba(0, 204, 150, 0.1); border:1px solid #00CC96; padding:20px; border-radius:10px; text-align:center;">
                <div style="color:#aaa; font-size:12px;">ESTIMASI PENDAPATAN</div>
                <h1 style="margin:0; color:#00CC96;">Rp {total:,}</h1>
            </div>
            """, unsafe_allow_html=True)

    with t2:
        colA, colB = st.columns(2)
        with colA:
            type_s = st.selectbox("Komoditas", ["Cengkeh", "Pinang", "Kakao"])
            wet_w = st.number_input("Berat Basah (Kg)", 1.0)
            wet_p = st.number_input("Harga Jual Basah (Rp)", 0, step=500)
        with colB:
            # Logic Rendemen
            r_map = {"Cengkeh": 0.30, "Pinang": 0.25, "Kakao": 0.35}
            dry_w = wet_w * r_map[type_s]
            
            dry_p_db = 0
            if type_s == "Cengkeh": dry_p_db = acuan_data.get("Cengkeh Biasa", 0)
            elif type_s == "Pinang": dry_p_db = acuan_data.get("Pinang", 0)
            elif type_s == "Kakao": dry_p_db = acuan_data.get("Kakao (Coklat)", 0)
            
            dry_total = dry_w * dry_p_db
            wet_total = wet_w * wet_p
            
            st.write(f"📉 **Susut Jadi:** {dry_w:.1f} Kg")
            st.write(f"💵 **Jual Basah:** Rp {wet_total:,}")
            st.write(f"💎 **Jual Kering:** Rp {dry_total:,}")
            
            if dry_total > wet_total:
                st.success(f"🔥 UNTUNG JUAL KERING (+Rp {dry_total - wet_total:,})")
            else:
                st.warning("⚠️ MENDING JUAL BASAH")

def render_admin():
    st.title("🛠️ Panel Kendali")
    tab1, tab2, tab3 = st.tabs(["⚙️ Harga Pusat", "👥 Database Toke", "📢 Berita"])
    
    with tab1:
        st.caption("Update harga acuan berdasarkan data terbaru.")
        with st.form("upd_price"):
            updates = {}
            for item in LIST_KOMODITAS:
                updates[item] = st.number_input(item, value=acuan_data.get(item, 0))
            if st.form_submit_button("Simpan Perubahan"):
                db.collection('settings').document('harga_padang').set(updates, merge=True)
                st.toast("Database diperbarui!", icon="✅")
                time.sleep(1)
                st.rerun()
                
    with tab2:
        with st.form("add_ag"):
            c1, c2 = st.columns(2)
            nm = c1.text_input("Nama"); lc = c2.text_input("Lokasi")
            wa = c1.text_input("WhatsApp"); br = c2.text_input("Barang")
            if st.form_submit_button("Tambah Toke"):
                db.collection('agen_mentawai').add({"nama": nm, "lokasi": lc, "wa": wa, "barang": br})
                st.success("Data tersimpan.")

    with tab3:
        curr = settings_data.get('berita', '')
        news = st.text_area("Tulis Pengumuman", curr)
        if st.button("Terbitkan Berita"):
            db.collection('settings').document('general').set({"berita": news, "tanggal_berita": datetime.datetime.now().strftime("%d %b")})
            st.rerun()

# ==========================================
# 5. MAIN NAVIGASI
# ==========================================
def main():
    inject_custom_css()
    
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False

    with st.sidebar:
        st.title("🌴 MENTAWAI MARKET")
        st.caption("Sistem Informasi Harga Komoditas")
        
        # Menu Selection
        if st.session_state.is_admin:
            st.success("👤 Mode Admin")
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Panel Admin"])
            if st.button("Logout", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
        else:
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Lapor Harga"])
            st.divider()
            with st.expander("🔐 Login Pengelola"):
                pw = st.text_input("Password", type="password")
                if st.button("Masuk"):
                    if "admin_password" in st.secrets and pw.strip() == st.secrets["admin_password"]:
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("Akses Ditolak")
        
        st.divider()
        st.markdown("**Tips:**\nKlik tombol titik tiga (⋮) di pojok kanan atas untuk ganti tema Gelap/Terang.")

    # Routing
    if nav == "Dashboard": render_dashboard()
    elif nav == "Kalkulator": render_calculator()
    elif nav == "Direktori Toke": render_directory()
    elif nav == "Lapor Harga":
        st.title("📝 Lapor Harga")
        with st.form("lapor"):
            i = st.selectbox("Item", LIST_KOMODITAS)
            p = st.number_input("Harga", step=500)
            l = st.text_input("Lokasi"); c = st.text_input("Catatan")
            if st.form_submit_button("Kirim Laporan"):
                if db:
                    db.collection('mentawai_v2').add({"item": i, "harga_angka": p, "lokasi": l, "catatan": c, "waktu": datetime.datetime.now()})
                    st.toast("Laporan diterima!", icon="🙏")
                else: st.error("Database offline.")
    elif nav == "Panel Admin": render_admin()

    st.markdown('<div class="footer-pro">App by Mr. Ghost © 2026</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
