import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import time

# ==========================================
# 1. SYSTEM CONFIGURATION (HARUS PALING ATAS)
# ==========================================
st.set_page_config(
    page_title="Mentawai Smart Market",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded" # Paksa sidebar terbuka di awal
)

# KONSTANTA DATA
LIST_KOMODITAS = [
    "Cengkeh Super", "Cengkeh Biasa", "Gagang Cengkeh", "Minyak Cengkeh",
    "Kopra", "Pinang", "Kakao (Coklat)", "Sagu", "Nilam", "Gambir",
    "Gurita", "Lobster", "Kerapu", "Teripang", "Ikan Asin",
    "Sarang Walet", "Manau (Rotan)", "Madu Hutan"
]

# ==========================================
# 2. FRONT-END ENGINE (CSS FIX SIDEBAR)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* 1. HIDE MENU BAWAAN TAPI JANGAN HIDE TOMBOL SIDEBAR */
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;}
        
        /* header {visibility: hidden;}  <-- INI BIANG KEROKNYA, KITA HAPUS BARIS INI */
        
        /* Ganti dengan ini: Sembunyikan garis pelangi, tapi Header tetap ada */
        header[data-testid="stHeader"] {
            background-color: rgba(0,0,0,0); /* Transparan */
            z-index: 1;
        }

        /* 2. CARD STYLE (Kaca Transparan) */
        .card-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .card-container:hover {
            transform: translateY(-5px);
            border-color: #00CC96;
            box-shadow: 0 4px 15px rgba(0, 204, 150, 0.2);
        }
        
        /* 3. TYPOGRAPHY & ALERTS */
        .price-tag { font-size: 24px; font-weight: 800; color: #00CC96; }
        .label-small { font-size: 11px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
        
        .alert-success { background: rgba(0, 204, 150, 0.15); border-left: 4px solid #00CC96; padding: 15px; border-radius: 4px; }
        .alert-warning { background: rgba(255, 165, 0, 0.15); border-left: 4px solid #FFA500; padding: 15px; border-radius: 4px; }
        
        /* 4. FOOTER */
        .footer-pro {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background: #0e1117; color: #666; text-align: center;
            padding: 8px; font-size: 11px; border-top: 1px solid #333; z-index: 999;
        }
        
        /* 5. RESPONSIVE TEXT */
        @media (max-width: 600px) {
            .price-tag { font-size: 20px; }
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. BACK-END LOGIC (ROBUST DATABASE)
# ==========================================
@st.cache_resource
def get_db():
    """Koneksi Database Aman (Anti-Crash)"""
    try:
        # Cek apakah Firebase sudah jalan
        if not firebase_admin._apps:
            if "textkey" in st.secrets:
                key_dict = json.loads(st.secrets["textkey"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else:
                return None
        return firestore.client()
    except Exception as e:
        # Jangan matikan app, cukup return None
        return None

db = get_db()

def get_data_safe(collection, doc_id):
    """Ambil data tanpa bikin error kalau null"""
    if db is None: return {}
    try:
        doc = db.collection(collection).document(doc_id).get()
        if doc.exists:
            return doc.to_dict()
        return {}
    except:
        return {}

# Load Data Awal (Dengan Fail-Safe)
settings_data = get_data_safe('settings', 'general')
acuan_data = get_data_safe('settings', 'harga_padang')

# ==========================================
# 4. MODULAR PAGES (FUNGSI TERPISAH)
# ==========================================

def render_dashboard():
    st.title("📡 Pusat Pantauan Harga")
    
    # Berita (Kondisional)
    if settings_data.get('berita'):
        st.markdown(f"""
        <div class="alert-warning">
            <h4 style="margin:0;">📢 UPDATE {settings_data.get('tanggal_berita', 'TERKINI')}</h4>
            <p style="margin:5px 0 0 0;">{settings_data.get('berita')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("") 

    # Grid Harga
    st.subheader("🏙️ Harga Acuan (Gudang Padang)")
    tabs = st.tabs(["🌱 TANI", "🐟 LAUT", "🦅 HUTAN"])
    
    def show_card(label, key):
        price = acuan_data.get(key, 0)
        st.markdown(f"""
        <div class="card-container">
            <div class="label-small">{label}</div>
            <div class="price-tag">Rp {price:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with tabs[0]: 
        c1, c2 = st.columns(2) # Di HP jadi 2 baris biar kebaca
        with c1: 
            show_card("Cengkeh Super", "Cengkeh Super")
            show_card("Kopra", "Kopra")
        with c2: 
            show_card("Cengkeh Biasa", "Cengkeh Biasa")
            show_card("Pinang", "Pinang")
            
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1: show_card("Gurita", "Gurita"); show_card("Lobster", "Lobster")
        with c2: show_card("Teripang", "Teripang"); show_card("Kerapu", "Kerapu")
        
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1: show_card("Walet", "Sarang Walet")
        with c2: show_card("Manau", "Manau (Rotan)")

    # Grafik (Dengan Loading State)
    st.divider()
    st.subheader("📈 Tren Harga")
    if db:
        try:
            with st.spinner("Sedang memuat grafik..."):
                docs = db.collection('mentawai_v2').order_by('waktu').stream()
                data = [{"Barang": d.to_dict().get('item'), "Harga": d.to_dict().get('harga_angka'), "Waktu": d.to_dict().get('waktu')} for d in docs]
                df = pd.DataFrame(data)
                
                if not df.empty:
                    choice = st.selectbox("Pilih Komoditas:", df['Barang'].unique())
                    df_chart = df[df['Barang'] == choice]
                    st.area_chart(df_chart, x="Waktu", y="Harga", color="#00CC96")
                else:
                    st.info("Data grafik belum cukup.")
        except:
            st.warning("Gagal memuat grafik. Cek koneksi internet.")

def render_directory():
    st.title("📞 Direktori Toke")
    search = st.text_input("🔍 Cari Desa/Kecamatan:", placeholder="Contoh: Sikakap")
    
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
                                <h3 style="margin:0;">👤 {d.get('nama')}</h3>
                                <div style="color:#aaa; font-size:12px;">📍 {d.get('lokasi')}</div>
                                <div style="color:#00CC96; font-size:12px;">📦 {d.get('barang')}</div>
                            </div>
                            <a href="https://wa.me/{wa}" target="_blank">
                                <button style="background:#25D366; border:none; color:white; padding:8px 12px; border-radius:20px; cursor:pointer;">
                                    Chat WA
                                </button>
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            if not found: st.info("Tidak ditemukan Toke di lokasi ini.")
        except:
            st.error("Gagal memuat data Toke.")

def render_calculator():
    st.title("🧮 Kalkulator Cerdas")
    t1, t2 = st.tabs(["💰 Hitung Panen", "⚖️ Basah vs Kering"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            w = st.number_input("Berat (Kg)", 1)
            p = st.number_input("Harga Deal (Rp)", 0, step=500)
        with c2:
            total = w * p
            st.markdown(f"""
            <div class="alert-success" style="text-align:center;">
                <h3 style="margin:0;">Total Duit:</h3>
                <h1 style="margin:0; color:#005f46;">Rp {total:,}</h1>
            </div>
            """, unsafe_allow_html=True)

    with t2:
        colA, colB = st.columns(2)
        with colA:
            type_s = st.selectbox("Jenis", ["Cengkeh", "Pinang", "Kakao"])
            wet_w = st.number_input("Berat Basah (Kg)", 1.0)
            wet_p = st.number_input("Jual Basah (Rp)", 0)
        with colB:
            r_map = {"Cengkeh": 0.30, "Pinang": 0.25, "Kakao": 0.35}
            dry_w = wet_w * r_map[type_s]
            
            # Auto fetch price
            dry_p_db = 0
            if type_s == "Cengkeh": dry_p_db = acuan_data.get("Cengkeh Biasa", 0)
            elif type_s == "Pinang": dry_p_db = acuan_data.get("Pinang", 0)
            elif type_s == "Kakao": dry_p_db = acuan_data.get("Kakao (Coklat)", 0)
            
            dry_total = dry_w * dry_p_db
            wet_total = wet_w * wet_p
            
            if dry_total > wet_total:
                st.success(f"🔥 JUAL KERING UNTUNG +Rp {dry_total - wet_total:,}")
            else:
                st.warning("⚠️ Mending Jual Basah Aja.")

def render_admin():
    st.title("🛠️ Admin Panel")
    tab1, tab2, tab3 = st.tabs(["Update Harga", "Tambah Toke", "Berita"])
    
    with tab1:
        with st.form("upd_price"):
            updates = {}
            for item in LIST_KOMODITAS:
                updates[item] = st.number_input(item, value=acuan_data.get(item, 0))
            if st.form_submit_button("Simpan Harga"):
                db.collection('settings').document('harga_padang').set(updates, merge=True)
                st.toast("Harga tersimpan!", icon="✅")
                time.sleep(1)
                st.rerun()
                
    with tab2:
        with st.form("add_ag"):
            nm = st.text_input("Nama"); lc = st.text_input("Lokasi")
            wa = st.text_input("WA"); br = st.text_input("Barang")
            if st.form_submit_button("Simpan Toke"):
                db.collection('agen_mentawai').add({"nama": nm, "lokasi": lc, "wa": wa, "barang": br})
                st.success("Toke ditambahkan.")

    with tab3:
        curr = settings_data.get('berita', '')
        news = st.text_area("Berita", curr)
        if st.button("Publish"):
            db.collection('settings').document('general').set({"berita": news, "tanggal_berita": datetime.datetime.now().strftime("%d %b")})
            st.rerun()

# ==========================================
# 5. MAIN APP CONTROLLER (NAVIGASI)
# ==========================================
def main():
    inject_custom_css()
    
    # Session State Init
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False

    # SIDEBAR
    with st.sidebar:
        st.title("🌴 MENTAWAI MARKET")
        
        # Menu Navigasi
        if st.session_state.is_admin:
            st.success("Admin Mode")
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Admin Tools"])
            if st.button("Logout"):
                st.session_state.is_admin = False
                st.rerun()
        else:
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Lapor Harga"])
            st.divider()
            with st.expander("Login Admin"):
                pw = st.text_input("Password", type="password")
                if st.button("Masuk"):
                    # LOGIN AMAN (STRIP SPASI)
                    if "admin_password" in st.secrets and pw.strip() == st.secrets["admin_password"]:
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("Salah password")

    # ROUTING HALAMAN
    try:
        if nav == "Dashboard": render_dashboard()
        elif nav == "Kalkulator": render_calculator()
        elif nav == "Direktori Toke": render_directory()
        elif nav == "Lapor Harga":
            st.title("📝 Lapor Harga")
            with st.form("lapor"):
                i = st.selectbox("Item", LIST_KOMODITAS)
                p = st.number_input("Harga", step=500)
                l = st.text_input("Lokasi"); c = st.text_input("Catatan")
                if st.form_submit_button("Kirim"):
                    if db:
                        db.collection('mentawai_v2').add({"item": i, "harga_angka": p, "lokasi": l, "catatan": c, "waktu": datetime.datetime.now()})
                        st.toast("Laporan terkirim!", icon="🚀")
                    else:
                        st.error("Database offline.")
        elif nav == "Admin Tools": render_admin()
    except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {e}")
        st.info("Cobalah refresh halaman.")

    # Footer
    st.markdown('<div class="footer-pro">Developed by Mr. Ghost © 2026</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
