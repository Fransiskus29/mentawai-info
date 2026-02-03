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

# ==========================================
# DATABASE GAMBAR CURATED V23.0 (FINAL STABLE)
# ==========================================
INFO_KOMODITAS = {
    # --- CENGKEH ---
    "Cengkeh Super (Kering)": {
        "img": "https://i.imgur.com/Q9W21sK.jpg",
        "desc": "Cengkeh kering sempurna, warna hitam mengkilap, bersih, tidak patah, kadar air rendah.",
        "guna": "Rokok Kretek Premium & Ekspor."
    },
    "Cengkeh Biasa (Asalan)": {
        "img": "https://i.imgur.com/y8R31bC.jpg",
        "desc": "Cengkeh yang warnanya pudar atau kemerahan, kadar air masih agak tinggi, kadang campur gagang.",
        "guna": "Campuran rokok (Harga kena potongan/rafaksi)."
    },
    "Gagang Cengkeh": {
        "img": "https://i.imgur.com/6z0y4cQ.jpg",
        "desc": "Tangkai bunga cengkeh yang sudah dipisahkan dan dikeringkan.",
        "guna": "Minyak Atsiri & Campuran Tembakau."
    },
    "Minyak Cengkeh": {
        "img": "https://i.imgur.com/6a2g8mJ.jpg",
        "desc": "Minyak hasil penyulingan daun/gagang cengkeh. Wangi menyengat.",
        "guna": "Obat Sakit Gigi & Aromaterapi."
    },

    # --- KELAPA ---
    "Kopra Gudang (Kering)": {
        "img": "https://i.imgur.com/6dG8s2L.jpg",
        "desc": "Daging kelapa kering (kadar air <5%), putih bersih, tidak berjamur.",
        "guna": "Minyak Goreng Kualitas Tinggi (Bimoli dll)."
    },
    "Kopra Asalan (Basah)": {
        "img": "https://i.imgur.com/1wY5k3d.jpg",
        "desc": "Kopra yang dijemur seadanya atau diasap. Warna kecoklatan/hitam.",
        "guna": "Minyak Curah & Pakan Ternak."
    },
    "Kelapa Butir": {
        "img": "https://i.imgur.com/3pC19fE.jpg",
        "desc": "Kelapa tua utuh yang belum dicungkil (bulat).",
        "guna": "Pasar tradisional & Pabrik Santan."
    },

    # --- PINANG & LAINNYA ---
    "Pinang Kering (Biji)": {
        "img": "https://i.imgur.com/2zJ7v1a.jpg",
        "desc": "Biji pinang belah kering keras (batu).",
        "guna": "Ekspor India, Pewarna, Permen."
    },
    "Pinang Basah (Kupas)": {
        "img": "https://i.imgur.com/8fX0m4s.jpg",
        "desc": "Pinang segar yang baru dikupas kulitnya.",
        "guna": "Harus segera dijemur agar tidak busuk."
    },
    "Kakao (Coklat)": {
        "img": "https://i.imgur.com/9mD4a1s.jpg",
        "desc": "Biji kakao fermentasi kering.",
        "guna": "Bahan baku Coklat."
    },
    "Sagu": {
        "img": "https://i.imgur.com/4vQ2b8d.jpg",
        "desc": "Tepung pati batang rumbia (basah/kering).",
        "guna": "Makanan Pokok (Kapurut/Sagu Bakar)."
    },
    "Nilam": {
        "img": "https://i.imgur.com/5cZ9b2e.jpg",
        "desc": "Daun nilam kering atau minyak atsiri nilam.",
        "guna": "Pengikat Parfum (Fixative)."
    },
    "Gambir": {
        "img": "https://i.imgur.com/7xY1d3f.jpg",
        "desc": "Ekstrak daun gambir kering (bentuk koin/blok).",
        "guna": "Menyirih & Farmasi."
    },

    # --- HASIL LAUT & HUTAN ---
    "Gurita": {
        "img": "https://i.imgur.com/2aB4c6d.jpg",
        "desc": "Gurita laut segar/beku.",
        "guna": "Ekspor Jepang/Korea."
    },
    "Lobster": {
        "img": "https://i.imgur.com/1eF5g8h.jpg",
        "desc": "Udang karang/barong (Mutiara/Pasir).",
        "guna": "Restoran Mewah."
    },
    "Kerapu": {
        "img": "https://i.imgur.com/3hG6j9k.jpg",
        "desc": "Ikan kerapu hidup/segar (Macan, Bebek, dll).",
        "guna": "Ekspor Hongkong."
    },
    "Teripang": {
        "img": "https://i.imgur.com/4iJ5k1l.jpg",
        "desc": "Timun laut kering (asap/jemur).",
        "guna": "Obat Cina & Makanan Mahal."
    },
    "Ikan Asin": {
        "img": "https://i.imgur.com/5lM6n7o.jpg",
        "desc": "Ikan laut diawetkan garam dan dijemur.",
        "guna": "Lauk pauk tahan lama."
    },
    "Sarang Walet": {
        "img": "https://i.imgur.com/6mN7o8p.jpg",
        "desc": "Sarang burung walet murni (mangkok/sudut).",
        "guna": "Kesehatan & Sup Mahal."
    },
    "Manau (Rotan)": {
        "img": "https://i.imgur.com/7oP8q9r.jpg",
        "desc": "Batang rotan diameter besar.",
        "guna": "Furniture (Kursi/Meja)."
    },
    "Madu Hutan": {
        "img": "https://i.imgur.com/8qR9s0t.jpg",
        "desc": "Madu lebah liar asli hutan.",
        "guna": "Obat & Stamina."
    }
}
DEFAULT_IMG = "https://placehold.co/600x400/png?text=Mentawai+Market"
LIST_KAPAL = ["Mentawai Fast", "KMP Ambu-Ambu", "KMP Gambolo", "Sabuk Nusantara", "Kapal Perintis"]

# ==========================================
# 2. FRONT-END ENGINE (CSS PRO V23)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        #MainMenu {visibility: visible;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] { background-color: transparent; z-index: 1; }
        .marquee-container { width: 100%; background-color: #222; color: #FFA500; padding: 10px; white-space: nowrap; overflow: hidden; box-sizing: border-box; border-bottom: 2px solid #FFA500; margin-bottom: 20px; }
        .marquee { display: inline-block; padding-left: 100%; animation: marquee 25s linear infinite; font-weight: bold; font-family: monospace; }
        @keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
        .card-container { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 15px; margin-bottom: 15px; transition: all 0.3s ease; }
        .card-container:hover { transform: translateY(-3px); border-color: #00CC96; box-shadow: 0 4px 20px rgba(0, 204, 150, 0.15); }
        .price-tag { font-size: 22px; font-weight: 800; color: #00CC96; }
        .label-small { font-size: 11px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; }
        .trend-up { color: #00CC96; background: rgba(0, 204, 150, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .trend-down { color: #FF4B4B; background: rgba(255, 75, 75, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .trend-flat { color: #888; background: rgba(128, 128, 128, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .ship-ok { background: #00CC96; color: black; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .ship-bad { background: #FF4B4B; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .ship-warn { background: #FFA500; color: black; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .footer-pro { position: fixed; left: 0; bottom: 0; width: 100%; background: #0e1117; color: #666; text-align: center; padding: 6px; font-size: 11px; border-top: 1px solid #333; z-index: 999; }
        @media (max-width: 600px) { .price-tag { font-size: 20px; } }
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
logistik_data = get_data_safe('settings', 'logistik')

# ==========================================
# 4. MODULAR PAGES
# ==========================================

def render_dashboard():
    berita = settings_data.get('berita', 'Selamat Datang di Mentawai Smart Market')
    st.markdown(f"""<div class="marquee-container"><div class="marquee">📢 INFO PASAR: {berita} &nbsp;&nbsp;|&nbsp;&nbsp; 🚢 UPDATE: Cek Status Kapal di bawah...</div></div>""", unsafe_allow_html=True)
    st.title("📡 Pusat Pantauan Harga")
    with st.expander("🚢 STATUS LOGISTIK & KAPAL", expanded=True):
        cols = st.columns(len(LIST_KAPAL))
        for i, nama_kapal in enumerate(LIST_KAPAL):
            status = logistik_data.get(nama_kapal, "Jadwal Normal")
            wc = "ship-ok"
            if "Batal" in status or "Rusak" in status: wc = "ship-bad"
            elif "Docking" in status or "Tunda" in status: wc = "ship-warn"
            with cols[i]: st.markdown(f"""<div style="text-align:center; border:1px solid #444; padding:8px; border-radius:8px;"><small>{nama_kapal}</small><br><span class="{wc}">{status}</span></div>""", unsafe_allow_html=True)
    st.divider()
    st.subheader("🏙️ Harga Acuan (Gudang Padang)")
    tabs = st.tabs(["🌱 TANI", "🐟 LAUT", "🦅 HUTAN"])
    
    def show_smart_card(label, key):
        price = acuan_data.get(key, 0)
        prev = acuan_data.get(f"{key}_prev", price)
        diff = price - prev
        th = '<span class="trend-flat">= Stabil</span>'
        if diff > 0: th = f'<span class="trend-up">▲ +{diff:,}</span>'
        elif diff < 0: th = f'<span class="trend-down">▼ -{abs(diff):,}</span>'
        info = INFO_KOMODITAS.get(key, {})
        img_url = info.get("img", DEFAULT_IMG)
        with st.container():
            st.markdown(f"""
            <div class="card-container">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <div class="label-small">{label}</div> {th}
                </div>
                <div class="price-tag">Rp {price:,}</div>
            </div>""", unsafe_allow_html=True)
            with st.expander("📸 Gambar & Info"):
                c1, c2 = st.columns([1, 2])
                with c1: st.image(img_url, use_container_width=True)
                with c2:
                    st.caption(f"**Ciri:** {info.get('desc','-')}")
                    st.caption(f"**Kegunaan:** {info.get('guna','-')}")
                    st.markdown(f"""<a href="https://wa.me/?text={urllib.parse.quote(f'Cek harga {label}: Rp {price:,} di Mentawai Market')}" target="_blank" style="color:#00CC96; font-size:12px; font-weight:bold;">📤 Share WA</a>""", unsafe_allow_html=True)

    with tabs[0]: 
        c1, c2, c3 = st.columns(3)
        with c1: show_smart_card("Cengkeh Super", "Cengkeh Super (Kering)"); show_smart_card("Kopra Gudang", "Kopra Gudang (Kering)")
        with c2: show_smart_card("Cengkeh Asalan", "Cengkeh Biasa (Asalan)"); show_smart_card("Pinang Kering", "Pinang Kering (Biji)")
        with c3: show_smart_card("Kelapa Butir", "Kelapa Butir"); show_smart_card("Kakao", "Kakao (Coklat)"); show_smart_card("Sagu", "Sagu")
        with c1: show_smart_card("Gagang Cengkeh", "Gagang Cengkeh"); show_smart_card("Minyak Cengkeh", "Minyak Cengkeh")
        with c2: show_smart_card("Kopra Basah", "Kopra Asalan (Basah)"); show_smart_card("Pinang Basah", "Pinang Basah (Kupas)")
        with c3: show_smart_card("Nilam", "Nilam"); show_smart_card("Gambir", "Gambir")
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1: show_smart_card("Gurita", "Gurita"); show_smart_card("Lobster", "Lobster"); show_smart_card("Ikan Asin", "Ikan Asin")
        with c2: show_smart_card("Teripang", "Teripang"); show_smart_card("Kerapu", "Kerapu")
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1: show_smart_card("Sarang Walet", "Sarang Walet"); show_smart_card("Manau", "Manau (Rotan)")
        with c2: show_smart_card("Madu Hutan", "Madu Hutan")
    st.divider()
    c_graf, c_lap = st.columns([2, 1])
    with c_graf:
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
            except: pass
    with c_lap:
        st.subheader("📋 Laporan Warga")
        if 'df' in locals() and not df.empty:
            df_disp = df.sort_values(by="Waktu", ascending=False).head(5)
            for i, r in df_disp.iterrows(): st.markdown(f"""<div style="border-bottom:1px solid #333; padding:5px;"><small style="color:#00CC96;">{r['Waktu'].strftime('%d/%m')}</small> <b>{r['Barang']}</b>: Rp {r['Harga']:,}</div>""", unsafe_allow_html=True)
        else: st.caption("Belum ada laporan.")

def render_directory():
    st.title("📞 Direktori Toke")
    search = st.text_input("🔍 Cari Desa:", placeholder="Contoh: Sikakap")
    if db:
        try:
            docs = db.collection('agen_mentawai').stream()
            found = False
            for doc in docs:
                d = doc.to_dict()
                if not search or (search.lower() in d.get('lokasi', '').lower()):
                    found = True
                    wa = d.get('wa', '').replace("08", "628").replace("-", "").strip()
                    st.markdown(f"""<div class="card-container"><h3>👤 {d.get('nama')}</h3><p>📍 {d.get('lokasi')} | 📦 {d.get('barang')}</p><a href="https://wa.me/{wa}"><button style="background:#25D366; border:none; color:white; padding:5px 15px; border-radius:15px;">Chat WA</button></a></div>""", unsafe_allow_html=True)
            if not found: st.info("Tidak ditemukan.")
        except: st.error("Error.")

def render_calculator():
    st.title("🧮 Kalkulator Bisnis")
    t1, t2 = st.tabs(["💰 Hitung Cuan", "⚖️ Basah vs Kering"])
    with t1:
        c1, c2 = st.columns(2)
        with c1: w = st.number_input("Berat (Kg)", 1); p = st.number_input("Harga (Rp)", 0, step=500)
        with c2: st.markdown(f"""<div class="card-container" style="text-align:center;"><h4>TOTAL</h4><h1 style="color:#00CC96;">Rp {w*p:,}</h1></div>""", unsafe_allow_html=True)
    with t2:
        c1, c2 = st.columns(2)
        with c1: ts = st.selectbox("Jenis", ["Cengkeh", "Kopra", "Pinang"]); ww = st.number_input("Berat Basah", 1.0); wp = st.number_input("Jual Basah", 0)
        with c2:
            r = {"Cengkeh": 0.30, "Kopra": 0.50, "Pinang": 0.25}
            dw = ww * r[ts]; dp = 0
            if ts == "Cengkeh": dp = acuan_data.get("Cengkeh Super (Kering)", 0)
            elif ts == "Kopra": dp = acuan_data.get("Kopra Gudang (Kering)", 0)
            elif ts == "Pinang": dp = acuan_data.get("Pinang Kering (Biji)", 0)
            dt = dw * dp; wt = ww * wp
            st.write(f"📉 Kering: {dw:.1f} Kg | Rp {dt:,}"); st.write(f"💵 Basah: Rp {wt:,}")
            if dt > wt: st.success(f"UNTUNG KERING +Rp {dt-wt:,}")
            else: st.warning("JUAL BASAH AJA")

def render_admin():
    st.title("🛠️ Panel Admin")
    t1, t2, t3, t4, t5 = st.tabs(["⚙️ Harga", "🚢 Logistik", "📢 WA", "👮‍♂️ Hapus", "👥 Toke"])
    with t1:
        with st.form("upd"):
            upd = {}
            for item in LIST_KOMODITAS:
                old = acuan_data.get(item, 0)
                new = st.number_input(item, value=old)
                upd[item] = new; upd[f"{item}_prev"] = old
            if st.form_submit_button("Simpan"):
                db.collection('settings').document('harga_padang').set(upd, merge=True); st.rerun()
    with t2:
        with st.form("kpl"):
            upd_kpl = {}
            for k in LIST_KAPAL:
                p = ["Jadwal Normal", "Batal", "Docking", "Tunda", "Rusak"]
                cur = logistik_data.get(k, "Jadwal Normal")
                idx = p.index(cur) if cur in p else 0
                upd_kpl[k] = st.selectbox(k, p, index=idx)
            if st.form_submit_button("Simpan"):
                db.collection('settings').document('logistik').set(upd_kpl, merge=True); st.rerun()
    with t3:
        txt = "INFO HARGA MENTAWAI: https://pasarmentawai.streamlit.app"
        st.text_area("Teks:", txt); st.link_button("Kirim WA", f"https://wa.me/?text={urllib.parse.quote(txt)}")
    with t4:
        if st.button("Hapus Laporan Spam"):
            docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(1).stream()
            for d in docs: db.collection('mentawai_v2').document(d.id).delete()
            st.toast("Dihapus!")
    with t5:
        with st.form("tk"):
            n = st.text_input("Nama"); l = st.text_input("Lokasi"); w = st.text_input("WA"); b = st.text_input("Barang")
            if st.form_submit_button("Tambah"): db.collection('agen_mentawai').add({"nama":n,"lokasi":l,"wa":w,"barang":b}); st.success("Ok")

def main():
    inject_custom_css()
    if 'is_admin' not in st.session_state: st.session_state.is_admin = False
    with st.sidebar:
        st.title("🌴 MENTAWAI MARKET")
        if st.session_state.is_admin:
            st.success("ADMIN"); nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Panel Admin"])
            if st.button("Logout"): st.session_state.is_admin = False; st.rerun()
        else:
            nav = st.radio("Menu", ["Dashboard", "Kalkulator", "Direktori Toke", "Lapor Harga"])
            with st.expander("Login"):
                if st.button("Masuk") and st.text_input("Pass", type="password").strip() == st.secrets.get("admin_password", ""):
                    st.session_state.is_admin = True; st.rerun()
        st.divider(); st.caption("v23.0 - Final Stable Images")

    if nav == "Dashboard": render_dashboard()
    elif nav == "Kalkulator": render_calculator()
    elif nav == "Direktori Toke": render_directory()
    elif nav == "Lapor Harga":
        st.title("Lapor Harga")
        with st.form("lapor"):
            if st.form_submit_button("Kirim"):
                db.collection('mentawai_v2').add({"item": st.selectbox("Item", LIST_KOMODITAS), "harga_angka": st.number_input("Rp", step=500), "lokasi": st.text_input("Lokasi"), "waktu": datetime.datetime.now()})
                st.toast("Terkirim!")
    elif nav == "Panel Admin": render_admin()
    st.markdown('<div class="footer-pro">App by Mr. Ghost © 2026</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
