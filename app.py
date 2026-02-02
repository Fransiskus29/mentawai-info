import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import time
import urllib.parse

# ==========================================
# 1. SYSTEM CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Mentawai Smart Market",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DAFTAR KOMODITAS (SUDAH DIPISAH BASAH/KERING)
LIST_KOMODITAS = [
    # CENGKEH
    "Cengkeh Super (Kering)", "Cengkeh Biasa (Asalan)", "Gagang Cengkeh", "Minyak Cengkeh",
    # KELAPA & TURUNAN
    "Kopra Gudang (Kering)", "Kopra Asalan (Basah)", "Kelapa Butir",
    # PINANG & LAINNYA
    "Pinang Kering (Biji)", "Pinang Basah (Kupas)",
    "Kakao (Coklat)", "Sagu", "Nilam", "Gambir",
    # HASIL LAUT
    "Gurita", "Lobster", "Kerapu", "Teripang", "Ikan Asin",
    # HASIL HUTAN
    "Sarang Walet", "Manau (Rotan)", "Madu Hutan"
]

# ==========================================
# 2. FRONT-END ENGINE (CSS PRO)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        #MainMenu {visibility: visible;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] { background-color: transparent; z-index: 1; }

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

        .price-tag { font-size: 26px; font-weight: 800; color: #00CC96; margin-top: 5px; }
        .label-small { font-size: 11px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; }
        
        .alert-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; }
        .success { background: rgba(0, 204, 150, 0.15); border-left: 4px solid #00CC96; }
        .warning { background: rgba(255, 165, 0, 0.15); border-left: 4px solid #FFA500; }
        
        .footer-pro {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background: #0e1117; color: #666; text-align: center;
            padding: 6px; font-size: 11px; border-top: 1px solid #333; z-index: 999;
        }
        
        @media (max-width: 600px) {
            .price-tag { font-size: 22px; }
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. BACK-END LOGIC
# ==========================================
@st.cache_resource
def get_db():
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

settings_data = get_data_safe('settings', 'general')
acuan_data = get_data_safe('settings', 'harga_padang')

# ==========================================
# 4. MODULAR PAGES
# ==========================================

def render_dashboard():
    st.title("📡 Pusat Pantauan Harga")
    
    if settings_data.get('berita'):
        st.markdown(f"""
        <div class="alert-box warning">
            <h4 style="margin:0;">📢 INFO PASAR ({settings_data.get('tanggal_berita', '-')})</h4>
            <p style="margin:5px 0 0 0;">{settings_data.get('berita')}</p>
        </div>
        """, unsafe_allow_html=True)

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
        c1, c2, c3 = st.columns(3)
        with c1: 
            show_card("Cengkeh Super", "Cengkeh Super (Kering)")
            show_card("Kopra Gudang", "Kopra Gudang (Kering)")
            show_card("Pinang Kering", "Pinang Kering (Biji)")
        with c2: 
            show_card("Cengkeh Asalan", "Cengkeh Biasa (Asalan)")
            show_card("Kopra Basah", "Kopra Asalan (Basah)")
            show_card("Pinang Basah", "Pinang Basah (Kupas)")
        with c3:
            show_card("Kelapa Butir", "Kelapa Butir")
            show_card("Gagang Cengkeh", "Gagang Cengkeh")
            show_card("Kakao", "Kakao (Coklat)")

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1: show_card("Gurita", "Gurita"); show_card("Lobster", "Lobster")
        with c2: show_card("Teripang", "Teripang"); show_card("Kerapu", "Kerapu")
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1: show_card("Sarang Walet", "Sarang Walet"); show_card("Manau", "Manau (Rotan)")

    st.divider()
    c_grafik, c_tabel = st.columns([2, 1])
    
    with c_grafik:
        st.subheader("📈 Tren Harga")
        if db:
            try:
                docs = db.collection('mentawai_v2').order_by('waktu').stream()
                data = [{"Barang": d.to_dict().get('item'), "Harga": d.to_dict().get('harga_angka'), "Waktu": d.to_dict().get('waktu')} for d in docs]
                df = pd.DataFrame(data)
                if not df.empty:
                    choice = st.selectbox("Pilih Komoditas:", df['Barang'].unique())
                    df_chart = df[df['Barang'] == choice]
                    st.area_chart(df_chart, x="Waktu", y="Harga", color="#00CC96")
                else: st.info("Belum ada data grafik.")
            except: st.warning("Koneksi lambat.")
            
    with c_tabel:
        st.subheader("📋 Laporan Warga")
        if 'df' in locals() and not df.empty:
            df_display = df.sort_values(by="Waktu", ascending=False).head(5)
            for index, row in df_display.iterrows():
                st.markdown(f"""
                <div style="border-bottom:1px solid #333; padding:10px 0;">
                    <small style="color:#00CC96;">{row['Waktu'].strftime('%d/%m %H:%M')}</small><br>
                    <b>{row['Barang']}</b>: Rp {row['Harga']:,}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Belum ada laporan masuk.")

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
                                <button style="background: linear-gradient(45deg, #25D366, #128C7E); border:none; color:white; padding:8px 16px; border-radius:20px; cursor:pointer;">Chat WA</button>
                            </a>
                        </div>
                    </div>""", unsafe_allow_html=True)
            if not found: st.info("Tidak ditemukan.")
        except: st.error("Error memuat data.")

def render_calculator():
    st.title("🧮 Kalkulator Bisnis")
    t1, t2 = st.tabs(["💰 Hitung Cuan", "⚖️ Basah vs Kering"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            w = st.number_input("Berat (Kg)", 1)
            p = st.number_input("Harga Deal (Rp)", 0, step=500)
        with c2:
            total = w * p
            st.markdown(f"""<div class="alert-box success" style="text-align:center;"><h4 style="margin:0;">TOTAL</h4><h1 style="margin:0; color:#00CC96;">Rp {total:,}</h1></div>""", unsafe_allow_html=True)
    with t2:
        colA, colB = st.columns(2)
        with colA:
            ts = st.selectbox("Jenis", ["Cengkeh", "Kopra", "Pinang"])
            ww = st.number_input("Berat Basah (Kg)", 1.0); wp = st.number_input("Jual Basah (Rp)", 0)
        with colB:
            # Logic Rendemen
            r = {"Cengkeh": 0.30, "Kopra": 0.50, "Pinang": 0.25} # Kopra sekitar 50% dari kelapa basah/asalan
            dw = ww * r[ts]
            
            # Auto fetch price kering
            dp = 0
            if ts == "Cengkeh": dp = acuan_data.get("Cengkeh Super (Kering)", 0)
            elif ts == "Kopra": dp = acuan_data.get("Kopra Gudang (Kering)", 0)
            elif ts == "Pinang": dp = acuan_data.get("Pinang Kering (Biji)", 0)
            
            dt = dw * dp; wt = ww * wp
            st.write(f"📉 Jadi Kering: {dw:.1f} Kg")
            st.write(f"💵 Kalau Jual Basah: Rp {wt:,}")
            st.write(f"💎 Kalau Jual Kering: Rp {dt:,}")
            if dt > wt: st.success(f"🔥 KERING LEBIH UNTUNG (+Rp {dt-wt:,})")
            else: st.warning("⚠️ JUAL BASAH SAJA")

def render_admin():
    st.title("🛠️ Panel Admin")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚙️ Harga", "📢 Promosi WA", "👥 Toke", "📰 Berita", "📂 Data"])
    
    with tab1:
        with st.form("upd_price"):
            updates = {}
            st.write("Update harga sesuai kategori:")
            for item in LIST_KOMODITAS:
                updates[item] = st.number_input(item, value=acuan_data.get(item, 0))
            if st.form_submit_button("Simpan Harga"):
                db.collection('settings').document('harga_padang').set(updates, merge=True)
                st.toast("Harga tersimpan!", icon="✅"); time.sleep(1); st.rerun()

    # GENERATOR WA YANG SUDAH DISESUAIKAN
    with tab2:
        st.subheader("📢 Broadcast WA")
        tgl_skrg = datetime.datetime.now().strftime("%d %B %Y")
        pesan_wa = f"""*INFO HARGA MENTAWAI MARKET* 🌴
🗓️ *{tgl_skrg}*

💎 *Cengkeh Super (Kering):* Rp {acuan_data.get('Cengkeh Super (Kering)', 0):,}
🍂 *Cengkeh Asalan:* Rp {acuan_data.get('Cengkeh Biasa (Asalan)', 0):,}

🥥 *Kopra Gudang (Kering):* Rp {acuan_data.get('Kopra Gudang (Kering)', 0):,}
💧 *Kopra Basah:* Rp {acuan_data.get('Kopra Asalan (Basah)', 0):,}

🌰 *Pinang Kering:* Rp {acuan_data.get('Pinang Kering (Biji)', 0):,}

_Cek selengkapnya di:_
👉 https://pasarmentawai.streamlit.app"""
        
        st.text_area("Copy Teks:", value=pesan_wa, height=300)
        encoded_wa = urllib.parse.quote(pesan_wa)
        st.link_button("📤 Kirim WA", f"https://wa.me/?text={encoded_wa}")

    with tab3:
        with st.form("add_ag"):
            nm = st.text_input("Nama"); lc = st.text_input("Lokasi")
            wa = st.text_input("WA"); br = st.text_input("Barang")
            if st.form_submit_button("Tambah"):
                db.collection('agen_mentawai').add({"nama": nm, "lokasi": lc, "wa": wa, "barang": br})
                st.success("Toke ditambahkan.")

    with tab4:
        curr = settings_data.get('berita', '')
        news = st.text_area("Berita", curr)
        if st.button("Terbitkan"):
            db.collection('settings').document('general').set({"berita": news, "tanggal_berita": datetime.datetime.now().strftime("%d %b")})
            st.rerun()
            
    with tab5:
        if st.button("📥 Download CSV"):
            if db:
                docs = db.collection('mentawai_v2').stream()
                data = [{"Tgl": d.to_dict().get('waktu'), "Item": d.to_dict().get('item'), "Harga": d.to_dict().get('harga_angka')} for d in docs]
                df = pd.DataFrame(data)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download", csv, "data.csv", "text/csv")

# ==========================================
# 5. MAIN NAVIGASI
# ==========================================
def main():
    inject_custom_css()
    if 'is_admin' not in st.session_state: st.session_state.is_admin = False

    with st.sidebar:
        st.title("🌴 MENTAWAI MARKET")
        if st.session_state.is_admin:
            st.success("👤 ADMIN")
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Panel Admin"])
            if st.button("Logout"): st.session_state.is_admin = False; st.rerun()
        else:
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Lapor Harga"])
            st.divider()
            with st.expander("Login Admin"):
                pw = st.text_input("Password", type="password")
                if st.button("Masuk"):
                    if "admin_password" in st.secrets and pw.strip() == st.secrets["admin_password"]:
                        st.session_state.is_admin = True; st.rerun()
                    else: st.error("Salah password")
        st.divider(); st.caption("v15.1 - Detail List")

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
                    st.toast("Terkirim!", icon="🚀")
                else: st.error("DB Error")
    elif nav == "Panel Admin": render_admin()

    st.markdown('<div class="footer-pro">App by Mr. Ghost © 2026</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
