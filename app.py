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

# LIST KOMODITAS
LIST_KOMODITAS = [
    "Cengkeh Super (Kering)", "Cengkeh Biasa (Asalan)", "Gagang Cengkeh", "Minyak Cengkeh",
    "Kopra Gudang (Kering)", "Kopra Asalan (Basah)", "Kelapa Butir",
    "Pinang Kering (Biji)", "Pinang Basah (Kupas)",
    "Kakao (Coklat)", "Sagu", "Nilam", "Gambir",
    "Gurita", "Lobster", "Kerapu", "Teripang", "Ikan Asin",
    "Sarang Walet", "Manau (Rotan)", "Madu Hutan"
]

# DATA GAMBAR & EDUKASI
INFO_KOMODITAS = {
    "Cengkeh Super (Kering)": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Clove_in_white_background.jpg/640px-Clove_in_white_background.jpg",
        "desc": "Cengkeh kering sempurna, warna coklat tua/hitam, bersih. Kadar air rendah.",
        "guna": "Bahan rokok kretek premium, bumbu, dan minyak atsiri."
    },
    "Cengkeh Biasa (Asalan)": {
        "img": "https://asset.kompas.com/crops/O2yq2Gv7W2qQ9Z2q9Z2q9Z2q9Z2=/0x0:1000x667/750x500/data/photo/2020/05/12/5eba5a5a5a5a5.jpg",
        "desc": "Cengkeh agak basah/lembab, warna pudar. Sering tercampur gagang.",
        "guna": "Tetap laku tapi harga kena rafaksi (potongan) susut."
    },
    "Kopra Gudang (Kering)": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Coconut_meat.jpg/640px-Coconut_meat.jpg",
        "desc": "Daging kelapa kering (kadar air <5%), warna putih/abu bersih.",
        "guna": "Bahan baku minyak goreng (CCO) dan kosmetik."
    },
    "Kopra Asalan (Basah)": {
        "img": "https://awsimages.detik.net.id/community/media/visual/2022/04/18/kopra-putih-di-biak-numfor-papua-1.jpeg?w=700&q=90",
        "desc": "Kopra baru diasap/jemur sebentar. Kadar air tinggi.",
        "guna": "Minyak curah, pakan ternak. Harga fluktuatif."
    },
    "Pinang Kering (Biji)": {
        "img": "https://asset.kompas.com/crops/O2yq2Gv7W2qQ9Z2q9Z2q9Z2q9Z2=/0x0:1000x667/750x500/data/photo/2021/03/15/604f0a5a5a5a5.jpg",
        "desc": "Biji pinang belah kering keras (batu).",
        "guna": "Pewarna tekstil, permen, ekspor India."
    }
}
DEFAULT_IMG = "https://via.placeholder.com/300x200.png?text=Mentawai+Market"

# DAFTAR KAPAL
LIST_KAPAL = ["Mentawai Fast", "KMP Ambu-Ambu", "KMP Gambolo", "Sabuk Nusantara", "Kapal Perintis"]

# ==========================================
# 2. FRONT-END ENGINE (CSS PRO V19)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        #MainMenu {visibility: visible;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] { background-color: transparent; z-index: 1; }

        /* Running Text Style */
        .marquee-container {
            width: 100%;
            background-color: #222;
            color: #FFA500;
            padding: 10px;
            white-space: nowrap;
            overflow: hidden;
            box-sizing: border-box;
            border-bottom: 2px solid #FFA500;
            margin-bottom: 20px;
        }
        .marquee {
            display: inline-block;
            padding-left: 100%;
            animation: marquee 20s linear infinite;
            font-weight: bold;
            font-family: monospace;
            font-size: 16px;
        }
        @keyframes marquee {
            0%   { transform: translate(0, 0); }
            100% { transform: translate(-100%, 0); }
        }

        /* Card Style */
        .card-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .card-container:hover {
            transform: translateY(-3px);
            border-color: #00CC96;
            box-shadow: 0 4px 20px rgba(0, 204, 150, 0.15);
        }

        .price-tag { font-size: 22px; font-weight: 800; color: #00CC96; }
        .label-small { font-size: 11px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; }
        
        .trend-up { color: #00CC96; background: rgba(0, 204, 150, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .trend-down { color: #FF4B4B; background: rgba(255, 75, 75, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .trend-flat { color: #888; background: rgba(128, 128, 128, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }

        .info-title { color: #FFA500; font-weight: bold; font-size: 14px; margin-bottom: 5px; }
        
        /* Status Kapal Badges */
        .ship-ok { background: #00CC96; color: black; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .ship-bad { background: #FF4B4B; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .ship-warn { background: #FFA500; color: black; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        
        .footer-pro {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background: #0e1117; color: #666; text-align: center;
            padding: 6px; font-size: 11px; border-top: 1px solid #333; z-index: 999;
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
logistik_data = get_data_safe('settings', 'logistik') # DB BARU BUAT KAPAL

# ==========================================
# 4. MODULAR PAGES
# ==========================================

def render_dashboard():
    # 1. RUNNING TEXT (TV STYLE)
    berita_kilat = settings_data.get('berita', 'Selamat Datang di Mentawai Smart Market')
    st.markdown(f"""
    <div class="marquee-container">
        <div class="marquee">📢 INFO TERKINI: {berita_kilat} &nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp; 🚢 UPDATE LOGISTIK: Cek Status Kapal di bawah...</div>
    </div>
    """, unsafe_allow_html=True)

    st.title("📡 Pusat Pantauan Harga")
    
    # 2. PANEL STATUS KAPAL (BARU)
    with st.expander("🚢 STATUS KAPAL & LOGISTIK (Klik untuk Info)", expanded=True):
        cols = st.columns(len(LIST_KAPAL))
        for i, nama_kapal in enumerate(LIST_KAPAL):
            status = logistik_data.get(nama_kapal, "Jadwal Normal")
            warna_class = "ship-ok"
            if "Batal" in status or "Rusak" in status: warna_class = "ship-bad"
            elif "Docking" in status or "Tunda" in status: warna_class = "ship-warn"
            
            with cols[i]:
                st.markdown(f"""
                <div style="text-align:center; border:1px solid #444; padding:10px; border-radius:8px;">
                    <small>{nama_kapal}</small><br>
                    <span class="{warna_class}">{status}</span>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    
    # 3. HARGA KOMODITAS
    st.subheader("🏙️ Harga Acuan (Gudang Padang)")
    tabs = st.tabs(["🌱 TANI", "🐟 LAUT", "🦅 HUTAN"])
    
    def show_smart_card(label, key):
        price = acuan_data.get(key, 0)
        prev_price = acuan_data.get(f"{key}_prev", price)
        
        # Trend Logic
        trend_html = ""
        diff = price - prev_price
        if diff > 0: trend_html = f'<span class="trend-up">▲ +{diff:,}</span>'
        elif diff < 0: trend_html = f'<span class="trend-down">▼ -{abs(diff):,}</span>'
        else: trend_html = '<span class="trend-flat">= Stabil</span>'
            
        # Info Logic
        info = INFO_KOMODITAS.get(key, {})
        img_url = info.get("img", DEFAULT_IMG)
        
        with st.container():
            st.markdown(f"""
            <div class="card-container">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <div class="label-small">{label}</div>
                    {trend_html}
                </div>
                <div class="price-tag">Rp {price:,}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"ℹ️ Gambar & Info"):
                c_img, c_text = st.columns([1, 2])
                with c_img: st.image(img_url, use_container_width=True)
                with c_text:
                    st.caption(info.get("desc", "-"))
                    st.caption(f"**Kegunaan:** {info.get('guna', '-')}")
                    share_txt = f"Harga {label}: Rp {price:,}. Cek: https://pasarmentawai.streamlit.app"
                    st.markdown(f"""<a href="https://wa.me/?text={urllib.parse.quote(share_txt)}" target="_blank" style="color:#00CC96; font-size:12px;">📤 Share WA</a>""", unsafe_allow_html=True)

    with tabs[0]: 
        c1, c2, c3 = st.columns(3)
        with c1: 
            show_smart_card("Cengkeh Super", "Cengkeh Super (Kering)")
            show_smart_card("Kopra Gudang", "Kopra Gudang (Kering)")
        with c2: 
            show_smart_card("Cengkeh Asalan", "Cengkeh Biasa (Asalan)")
            show_smart_card("Pinang Kering", "Pinang Kering (Biji)")
        with c3:
            show_smart_card("Kelapa Butir", "Kelapa Butir")
            show_smart_card("Kakao", "Kakao (Coklat)")

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1: show_smart_card("Gurita", "Gurita"); show_smart_card("Lobster", "Lobster")
        with c2: show_smart_card("Teripang", "Teripang"); show_smart_card("Kerapu", "Kerapu")
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1: show_smart_card("Sarang Walet", "Sarang Walet"); show_smart_card("Manau", "Manau (Rotan)")

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
                st.markdown(f"""<div style="border-bottom:1px solid #333; padding:10px 0;"><small style="color:#00CC96;">{row['Waktu'].strftime('%d/%m %H:%M')}</small><br><b>{row['Barang']}</b>: Rp {row['Harga']:,}</div>""", unsafe_allow_html=True)
        else: st.caption("Belum ada laporan.")

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
                            <a href="https://wa.me/{wa}" target="_blank"><button style="background: linear-gradient(45deg, #25D366, #128C7E); border:none; color:white; padding:8px 16px; border-radius:20px; cursor:pointer;">Chat WA</button></a>
                        </div>
                    </div>""", unsafe_allow_html=True)
            if not found: st.info("Tidak ditemukan.")
        except: st.error("Error data.")

def render_calculator():
    st.title("🧮 Kalkulator Bisnis")
    t1, t2 = st.tabs(["💰 Hitung Cuan", "⚖️ Basah vs Kering"])
    with t1:
        c1, c2 = st.columns(2)
        with c1: w = st.number_input("Berat (Kg)", 1); p = st.number_input("Harga Deal (Rp)", 0, step=500)
        with c2: st.markdown(f"""<div class="card-container" style="text-align:center;"><h4 style="margin:0;">TOTAL</h4><h1 style="margin:0; color:#00CC96;">Rp {w*p:,}</h1></div>""", unsafe_allow_html=True)
    with t2:
        colA, colB = st.columns(2)
        with colA: ts = st.selectbox("Jenis", ["Cengkeh", "Kopra", "Pinang"]); ww = st.number_input("Berat Basah", 1.0); wp = st.number_input("Jual Basah", 0)
        with colB:
            r = {"Cengkeh": 0.30, "Kopra": 0.50, "Pinang": 0.25}
            dw = ww * r[ts]; dp = 0
            if ts == "Cengkeh": dp = acuan_data.get("Cengkeh Super (Kering)", 0)
            elif ts == "Kopra": dp = acuan_data.get("Kopra Gudang (Kering)", 0)
            elif ts == "Pinang": dp = acuan_data.get("Pinang Kering (Biji)", 0)
            dt = dw * dp; wt = ww * wp
            st.write(f"📉 Kering: {dw:.1f} Kg | Rp {dt:,}"); st.write(f"💵 Basah: Rp {wt:,}")
            if dt > wt: st.success(f"🔥 KERING UNTUNG +Rp {dt-wt:,}")
            else: st.warning("⚠️ JUAL BASAH SAJA")

def render_admin():
    st.title("🛠️ Panel Admin")
    # TAB BARU: LOGISTIK
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["⚙️ Harga", "🚢 Logistik", "👮‍♂️ Moderasi", "📢 Broadcast", "👥 Toke", "📰 Berita", "📂 Data"])
    
    with tab1:
        st.info("Harga otomatis menghitung tren.")
        with st.form("upd_price"):
            updates = {}
            for item in LIST_KOMODITAS:
                old = acuan_data.get(item, 0)
                new = st.number_input(item, value=old)
                updates[item] = new
                updates[f"{item}_prev"] = old
            if st.form_submit_button("Simpan"):
                db.collection('settings').document('harga_padang').set(updates, merge=True)
                st.toast("Disimpan!", icon="✅"); time.sleep(1); st.rerun()

    # FITUR UPDATE KAPAL
    with tab2:
        st.subheader("Update Status Kapal")
        with st.form("upd_kapal"):
            upd_logistik = {}
            for kpl in LIST_KAPAL:
                pilihan = ["Jadwal Normal", "Batal Berangkat", "Docking", "Tunda (Cuaca Buruk)", "Rusak"]
                curr_stat = logistik_data.get(kpl, "Jadwal Normal")
                # Cari index pilihan
                idx = pilihan.index(curr_stat) if curr_stat in pilihan else 0
                upd_logistik[kpl] = st.selectbox(f"Status {kpl}", pilihan, index=idx)
            
            if st.form_submit_button("Simpan Info Kapal"):
                db.collection('settings').document('logistik').set(upd_logistik, merge=True)
                st.success("Info Kapal Diupdate!")
                st.rerun()

    with tab3:
        if st.button("Hapus Laporan Spam"):
            if db:
                docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(1).stream()
                for d in docs: db.collection('mentawai_v2').document(d.id).delete()
                st.toast("Terhapus!")
    with tab4:
        pesan = f"*HARGA & LOGISTIK MENTAWAI MARKET*\nCek: https://pasarmentawai.streamlit.app"
        st.text_area("Copy:", pesan); st.link_button("Kirim WA", f"https://wa.me/?text={urllib.parse.quote(pesan)}")
    with tab5:
        with st.form("add_ag"):
            nm = st.text_input("Nama"); lc = st.text_input("Lokasi"); wa = st.text_input("WA"); br = st.text_input("Barang")
            if st.form_submit_button("Tambah"): db.collection('agen_mentawai').add({"nama": nm, "lokasi": lc, "wa": wa, "barang": br}); st.success("Ditambahkan.")
    with tab6:
        curr = settings_data.get('berita', '')
        news = st.text_area("Teks Berjalan (Running Text)", curr)
        if st.button("Terbitkan"): db.collection('settings').document('general').set({"berita": news, "tanggal_berita": datetime.datetime.now().strftime("%d %b")}); st.rerun()
    with tab7:
        if st.button("Download CSV"):
            if db:
                docs = db.collection('mentawai_v2').stream()
                data = [{"Tgl": d.to_dict().get('waktu'), "Item": d.to_dict().get('item'), "Harga": d.to_dict().get('harga_angka')} for d in docs]
                df = pd.DataFrame(data); csv = df.to_csv(index=False).encode('utf-8'); st.download_button("Download", csv, "data.csv", "text/csv")

def main():
    inject_custom_css()
    if 'is_admin' not in st.session_state: st.session_state.is_admin = False
    with st.sidebar:
        st.title("🌴 MENTAWAI MARKET")
        if st.session_state.is_admin:
            st.success("👤 ADMIN"); nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Panel Admin"]); 
            if st.button("Logout"): st.session_state.is_admin = False; st.rerun()
        else:
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Lapor Harga"])
            with st.expander("Login"):
                pw = st.text_input("Password", type="password")
                if st.button("Masuk"):
                    if "admin_password" in st.secrets and pw.strip() == st.secrets["admin_password"]: st.session_state.is_admin = True; st.rerun()
                    else: st.error("Salah")
        st.divider(); st.caption("v19.0 Logistic Intel")

    if nav == "Dashboard": render_dashboard()
    elif nav == "Kalkulator": render_calculator()
    elif nav == "Direktori Toke": render_directory()
    elif nav == "Lapor Harga":
        st.title("📝 Lapor Harga")
        with st.form("lapor"):
            i = st.selectbox("Item", LIST_KOMODITAS); p = st.number_input("Harga", step=500); l = st.text_input("Lokasi"); c = st.text_input("Catatan")
            if st.form_submit_button("Kirim"):
                if db: db.collection('mentawai_v2').add({"item": i, "harga_angka": p, "lokasi": l, "catatan": c, "waktu": datetime.datetime.now()}); st.toast("Terkirim!", icon="🚀")
    elif nav == "Panel Admin": render_admin()
    st.markdown('<div class="footer-pro">App by Mr. Ghost © 2026</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
