import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import time

# ==========================================
# 1. CONFIGURATION & ASSETS
# ==========================================
st.set_page_config(
    page_title="Mentawai Smart Market",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# LIST DATA (CONSTANTS)
LIST_KOMODITAS = [
    "Cengkeh Super", "Cengkeh Biasa", "Gagang Cengkeh", "Minyak Cengkeh",
    "Kopra", "Pinang", "Kakao (Coklat)", "Sagu", "Nilam", "Gambir",
    "Gurita", "Lobster", "Kerapu", "Teripang", "Ikan Asin",
    "Sarang Walet", "Manau (Rotan)", "Madu Hutan"
]

# ==========================================
# 2. STYLING (FRONT-END ENGINE)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* GLOBAL RESET */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* MODERN CARD STYLE (Glassmorphism) */
        .card-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .card-container:hover {
            transform: translateY(-5px);
            border-color: #00CC96;
        }
        
        /* TYPOGRAPHY */
        .price-tag { font-size: 24px; font-weight: 800; color: #00CC96; }
        .label-small { font-size: 11px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
        .info-news { border-left: 4px solid #FFA500; background: #222; padding: 15px; border-radius: 4px; }
        
        /* ALERTS */
        .alert-success { background: rgba(0, 204, 150, 0.2); border: 1px solid #00CC96; padding: 10px; border-radius: 8px; text-align: center; }
        .alert-danger { background: rgba(255, 75, 75, 0.2); border: 1px solid #FF4B4B; padding: 10px; border-radius: 8px; text-align: center; }
        
        /* FOOTER */
        .footer-pro {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background: #0e1117; color: #666; text-align: center;
            padding: 8px; font-size: 11px; border-top: 1px solid #333; z-index: 999;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. BACK-END LOGIC (DATABASE & AUTH)
# ==========================================
@st.cache_resource
def get_db():
    """Connect to Firebase securely with caching."""
    try:
        if not firebase_admin._apps:
            if "textkey" in st.secrets:
                key_dict = json.loads(st.secrets["textkey"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else:
                return None
        return firestore.client()
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

db = get_db()

def get_document(collection, doc_id):
    """Helper to fetch single document safely."""
    if not db: return {}
    try:
        doc = db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else {}
    except: return {}

# Load Initial Data
settings_data = get_document('settings', 'general')
acuan_data = get_document('settings', 'harga_padang')

# ==========================================
# 4. PAGE FUNCTIONS (MODULAR UI)
# ==========================================

def render_dashboard():
    st.title("📡 Pusat Pantauan Harga")
    
    # News Section
    if settings_data.get('berita'):
        st.markdown(f"""
        <div class="info-news">
            <h4>📢 UPDATE PASAR ({settings_data.get('tanggal_berita', 'Hari Ini')})</h4>
            <p style="margin:0;">{settings_data.get('berita')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("") # Spacer

    # Pricing Grid
    st.subheader("🏙️ Harga Acuan (Gudang Padang)")
    
    tabs = st.tabs(["🌱 HASIL TANI", "🐟 HASIL LAUT", "🦅 HASIL HUTAN"])
    
    # Helper to render card
    def show_card(label, key):
        price = acuan_data.get(key, 0)
        st.markdown(f"""
        <div class="card-container">
            <div class="label-small">{label}</div>
            <div class="price-tag">Rp {price:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with tabs[0]: # Tani
        c1, c2, c3, c4 = st.columns(4)
        with c1: show_card("Cengkeh Super", "Cengkeh Super")
        with c2: show_card("Cengkeh Biasa", "Cengkeh Biasa")
        with c3: show_card("Kopra", "Kopra")
        with c4: show_card("Pinang", "Pinang")
    with tabs[1]: # Laut
        c1, c2, c3, c4 = st.columns(4)
        with c1: show_card("Gurita", "Gurita")
        with c2: show_card("Lobster", "Lobster")
        with c3: show_card("Teripang", "Teripang")
        with c4: show_card("Kerapu", "Kerapu")
    with tabs[2]: # Hutan
        c1, c2, c3 = st.columns(3)
        with c1: show_card("Sarang Walet", "Sarang Walet")
        with c2: show_card("Manau", "Manau (Rotan)")
        with c3: show_card("Madu", "Madu Hutan")

    # Chart Section
    st.divider()
    st.subheader("📈 Tren Pergerakan Harga")
    if db:
        with st.spinner("Memuat grafik..."):
            docs = db.collection('mentawai_v2').order_by('waktu').stream()
            data = [{"Barang": d.to_dict().get('item'), "Harga": d.to_dict().get('harga_angka'), "Waktu": d.to_dict().get('waktu')} for d in docs]
            df = pd.DataFrame(data)
            
            if not df.empty:
                choice = st.selectbox("Pilih Komoditas:", df['Barang'].unique())
                df_chart = df[df['Barang'] == choice]
                st.area_chart(df_chart, x="Waktu", y="Harga", color="#00CC96")
            else:
                st.info("Data grafik belum tersedia. Yuk lapor harga dulu!")

def render_directory():
    st.title("📞 Direktori Toke & Agen")
    search = st.text_input("🔍 Cari Lokasi (Desa/Kecamatan):", placeholder="Contoh: Sikakap")
    
    if db:
        docs = db.collection('agen_mentawai').stream()
        found = False
        for doc in docs:
            d = doc.to_dict()
            if not search or (search.lower() in d.get('lokasi', '').lower()):
                found = True
                wa_clean = d.get('wa', '').replace("08", "628").replace("-", "").strip()
                st.markdown(f"""
                <div class="card-container">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h3 style="margin:0;">👤 {d.get('nama')}</h3>
                            <div style="color:#888;">📍 {d.get('lokasi')} | 📦 {d.get('barang')}</div>
                        </div>
                        <a href="https://wa.me/{wa_clean}" target="_blank" style="text-decoration:none;">
                            <button style="background:#25D366; border:none; color:white; padding:8px 16px; border-radius:20px; cursor:pointer;">
                                💬 WhatsApp
                            </button>
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        if not found: st.warning("Tidak ditemukan agen di lokasi tersebut.")

def render_calculator():
    st.title("🧮 Kalkulator Cerdas")
    t1, t2, t3 = st.tabs(["🕵️ Anti-Tipu", "💰 Estimasi Panen", "⚖️ Basah vs Kering"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            item = st.selectbox("Komoditas", LIST_KOMODITAS)
            ref_price = acuan_data.get(item, 0)
            st.caption(f"Harga Pusat: Rp {ref_price:,}")
            offer = st.number_input("Tawaran Agen (Rp)", step=500)
        with c2:
            if offer > 0 and ref_price > 0:
                diff = ref_price - offer
                pct = (diff / ref_price) * 100
                st.metric("Selisih Harga", f"Rp {diff:,}")
                if pct < 20: st.markdown('<div class="alert-success">✅ HARGA BAGUS!</div>', unsafe_allow_html=True)
                elif pct < 40: st.markdown('<div class="alert-success" style="background:#FFA50033; border-color:orange;">👌 HARGA WAJAR</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="alert-danger">🛑 MENCEKIK / TERLALU MURAH</div>', unsafe_allow_html=True)

    with t2:
        w = st.number_input("Berat (Kg)", 1)
        p = st.number_input("Harga Deal (Rp)", 0, step=500)
        st.markdown(f"""<div class="card-container" style="text-align:center;"><h2>Total: Rp {w*p:,}</h2></div>""", unsafe_allow_html=True)

    with t3:
        st.info("Cek apakah untung jual basah atau kering?")
        colA, colB = st.columns(2)
        with colA:
            type_s = st.selectbox("Jenis", ["Cengkeh", "Pinang", "Kakao"])
            wet_w = st.number_input("Berat Basah (Kg)", 1.0)
            wet_p = st.number_input("Harga Jual Basah (Rp)", 0)
        with colB:
            # Logic Profesional Rendemen
            r_map = {"Cengkeh": 0.30, "Pinang": 0.25, "Kakao": 0.35}
            dry_w = wet_w * r_map[type_s]
            
            # Auto fetch dry price
            dry_p_db = 0
            if type_s == "Cengkeh": dry_p_db = acuan_data.get("Cengkeh Biasa", 0)
            elif type_s == "Pinang": dry_p_db = acuan_data.get("Pinang", 0)
            elif type_s == "Kakao": dry_p_db = acuan_data.get("Kakao (Coklat)", 0)
            
            dry_total = dry_w * dry_p_db
            wet_total = wet_w * wet_p
            
            st.write(f"📉 **Jadi Kering:** {dry_w:.1f} Kg")
            st.write(f"💰 **Potensi Kering:** Rp {dry_total:,}")
            st.write(f"💵 **Jual Basah:** Rp {wet_total:,}")
            
            if dry_total > wet_total:
                st.success(f"🔥 LEBIH UNTUNG JUAL KERING (+Rp {dry_total - wet_total:,})")
            else:
                st.warning("⚠️ LEBIH UNTUNG JUAL BASAH SAJA")

def render_admin_tools():
    st.title("🛠️ Panel Admin")
    
    tab_price, tab_news, tab_agent, tab_data = st.tabs(["⚙️ Update Harga", "📢 Berita", "👥 Agen", "📂 Data"])
    
    with tab_price:
        st.link_button("🔍 Cek Google Dulu", "https://www.google.com/search?q=harga+komoditas+sumbar+hari+ini")
        with st.form("price_update"):
            updates = {}
            # Loop otomatis biar kodenya pendek & rapi
            for item in LIST_KOMODITAS:
                updates[item] = st.number_input(item, value=acuan_data.get(item, 0))
            if st.form_submit_button("Simpan Perubahan"):
                db.collection('settings').document('harga_padang').set(updates, merge=True)
                st.toast("Harga berhasil diupdate!", icon="✅")
                time.sleep(1)
                st.rerun()

    with tab_news:
        cur_news = settings_data.get('berita', '')
        new_news = st.text_area("Berita Hari Ini", cur_news)
        if st.button("Publish Berita"):
            db.collection('settings').document('general').set({
                "berita": new_news, 
                "tanggal_berita": datetime.datetime.now().strftime("%d %b %Y")
            })
            st.success("Berita terbit.")
            st.rerun()

    with tab_agent:
        with st.form("add_agent"):
            c1, c2 = st.columns(2)
            nm = c1.text_input("Nama")
            lc = c2.text_input("Lokasi")
            wa = c1.text_input("WhatsApp")
            br = c2.text_input("Barang")
            if st.form_submit_button("Tambah Agen"):
                db.collection('agen_mentawai').add({"nama": nm, "lokasi": lc, "wa": wa, "barang": br})
                st.success("Agen ditambahkan.")
    
    with tab_data:
        if st.button("📥 Download Semua Laporan (CSV)"):
            docs = db.collection('mentawai_v2').stream()
            data = [{"Tanggal": d.to_dict().get('waktu'), "Item": d.to_dict().get('item'), "Harga": d.to_dict().get('harga_angka')} for d in docs]
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Klik untuk Download", csv, "data_mentawai.csv", "text/csv")

# ==========================================
# 5. MAIN APP CONTROLLER
# ==========================================
def main():
    inject_custom_css()
    
    # --- AUTHENTICATION CHECK ---
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.title("🌴 MENTAWAI MARKET")
        st.caption("Professional Commodity System")
        st.divider()
        
        # Smart Menu Logic
        if st.session_state.is_admin:
            st.success("👤 Admin Mode")
            nav = st.radio("Navigasi", ["Dashboard", "Kalkulator", "Direktori Agen", "Lapor Harga", "Admin Tools"])
            if st.button("Logout"):
                st.session_state.is_admin = False
                st.rerun()
        else:
            nav = st.radio("Navigasi", ["Dashboard", "Kalkulator", "Direktori Agen", "Lapor Harga"])
            st.divider()
            with st.expander("🔐 Login Admin"):
                pw = st.text_input("Password", type="password")
                if st.button("Masuk"):
                    if "admin_password" in st.secrets and pw.strip() == st.secrets["admin_password"]:
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("Password Salah")
        
        st.divider()
        st.caption("v11.0 | Professional Edition")

    # --- PAGE ROUTING ---
    if nav == "Dashboard": render_dashboard()
    elif nav == "Kalkulator": render_calculator()
    elif nav == "Direktori Agen": render_directory()
    elif nav == "Lapor Harga":
        st.title("📝 Lapor Harga")
        with st.form("lapor_public"):
            i = st.selectbox("Item", LIST_KOMODITAS)
            p = st.number_input("Harga", step=500)
            l = st.text_input("Lokasi")
            c = st.text_input("Catatan")
            if st.form_submit_button("Kirim Laporan"):
                db.collection('mentawai_v2').add({"item": i, "harga_angka": p, "lokasi": l, "catatan": c, "waktu": datetime.datetime.now()})
                st.success("Terima kasih laporannya!")
    elif nav == "Admin Tools": render_admin_tools()

    # Footer Injection
    st.markdown('<div class="footer-pro">Developed by <b>Mr. Ghost</b> & Tim IT Mentawai © 2026</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
