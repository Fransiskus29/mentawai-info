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
# DATABASE GAMBAR & EDUKASI (LENGKAP 21 ITEM)
# ==========================================
INFO_KOMODITAS = {
    # --- CENGKEH GROUP ---
    "Cengkeh Super (Kering)": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Clove_in_white_background.jpg/640px-Clove_in_white_background.jpg",
        "desc": "Ciri: Kering sempurna (patah saat ditekan), warna coklat tua/hitam mengkilap, bersih, kepala bunga utuh.",
        "guna": "Komoditas Ekspor, Rokok Kretek Premium."
    },
    "Cengkeh Biasa (Asalan)": {
        "img": "https://asset.kompas.com/crops/O2yq2Gv7W2qQ9Z2q9Z2q9Z2q9Z2=/0x0:1000x667/750x500/data/photo/2020/05/12/5eba5a5a5a5a5.jpg",
        "desc": "Ciri: Warna agak pudar/kemerahan, kandungan air masih ada (lembab), sering tercampur kotoran.",
        "guna": "Tetap laku, tapi harga dipotong rafaksi (susut berat)."
    },
    "Gagang Cengkeh": {
        "img": "https://cdn.pixabay.com/photo/2017/12/12/16/32/cloves-3014902_1280.jpg",
        "desc": "Batang/tangkai bunga cengkeh yang sudah dipisahkan dari bunganya dan dikeringkan.",
        "guna": "Bahan campuran rokok murah dan penyulingan minyak atsiri."
    },
    "Minyak Cengkeh": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Essential_oil_clove.jpg/640px-Essential_oil_clove.jpg",
        "desc": "Cairan hasil penyulingan daun atau gagang cengkeh. Wangi menyengat.",
        "guna": "Obat sakit gigi, aromaterapi, dan bahan farmasi."
    },

    # --- KELAPA GROUP ---
    "Kopra Gudang (Kering)": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Coconut_meat.jpg/640px-Coconut_meat.jpg",
        "desc": "Daging kelapa cungkil yang dikeringkan (jemur/oven) sampai kadar air <5%. Warna putih bersih.",
        "guna": "Minyak goreng kemasan (Bimoli dll), kosmetik, sabun."
    },
    "Kopra Asalan (Basah)": {
        "img": "https://awsimages.detik.net.id/community/media/visual/2022/04/18/kopra-putih-di-biak-numfor-papua-1.jpeg?w=700&q=90",
        "desc": "Kopra yang baru diasap/jemur sebentar. Masih mengandung air, rawan jamur.",
        "guna": "Minyak curah, pakan ternak."
    },
    "Kelapa Butir": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Coconut_123.jpg/640px-Coconut_123.jpg",
        "desc": "Kelapa tua utuh yang belum dicungkil dagingnya. Bisa sabut atau gundul.",
        "guna": "Dijual ke pasar basah atau pabrik santan."
    },

    # --- PINANG & LAINNYA ---
    "Pinang Kering (Biji)": {
        "img": "https://asset.kompas.com/crops/O2yq2Gv7W2qQ9Z2q9Z2q9Z2q9Z2=/0x0:1000x667/750x500/data/photo/2021/03/15/604f0a5a5a5a5.jpg",
        "desc": "Biji pinang belah yang sudah dijemur kering keras seperti batu.",
        "guna": "Ekspor ke India/Pakistan, pewarna tekstil, permen."
    },
    "Pinang Basah (Kupas)": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Areca_catechu_fruit.jpg/640px-Areca_catechu_fruit.jpg",
        "desc": "Pinang muda atau tua yang baru dikupas kulitnya, belum dijemur.",
        "guna": "Biasanya harga murah, harus segera diolah."
    },
    "Kakao (Coklat)": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Matengo_Cacao.jpg/640px-Matengo_Cacao.jpg",
        "desc": "Biji coklat fermentasi yang sudah dikeringkan.",
        "guna": "Bahan baku coklat (makanan/minuman)."
    },
    "Sagu": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Sago_pearls.jpg/640px-Sago_pearls.jpg",
        "desc": "Tepung pati yang diekstrak dari batang rumbia/sagu.",
        "guna": "Makanan pokok, bahan kue, papeda."
    },
    "Nilam": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Pogostemon_cablin_01.jpg/640px-Pogostemon_cablin_01.jpg",
        "desc": "Daun kering atau minyak hasil penyulingan nilam.",
        "guna": "Pengikat wangi parfum (Fixative) termahal di dunia."
    },
    "Gambir": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Uncaria_gambir.jpg/640px-Uncaria_gambir.jpg",
        "desc": "Getah kering dari daun gambir, biasanya berbentuk koin atau blok.",
        "guna": "Menyirih, bahan farmasi, pewarna."
    },

    # --- LAUT & HUTAN ---
    "Gurita": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Octopus_vulgaris_2.jpg/640px-Octopus_vulgaris_2.jpg",
        "desc": "Gurita segar atau beku.",
        "guna": "Komoditas ekspor Jepang/Korea."
    },
    "Lobster": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Panulirus_versicolor.jpg/640px-Panulirus_versicolor.jpg",
        "desc": "Udang karang besar, biasanya jenis Mutiara atau Pasir.",
        "guna": "Makanan mewah restoran."
    },
    "Kerapu": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Epinephelus_malabaricus.jpg/640px-Epinephelus_malabaricus.jpg",
        "desc": "Ikan karang hidup atau segar.",
        "guna": "Ekspor Hongkong/China."
    },
    "Teripang": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Thelenota_ananas.jpg/640px-Thelenota_ananas.jpg",
        "desc": "Timun laut yang sudah dikeringkan (asap/jemur).",
        "guna": "Obat tradisional China, makanan kesehatan."
    },
    "Ikan Asin": {
        "img": "https://asset.kompas.com/crops/O2yq2Gv7W2qQ9Z2q9Z2q9Z2q9Z2=/0x0:1000x667/750x500/data/photo/2020/05/12/5eba5a5a5a5a5.jpg", # Placeholder umum
        "desc": "Ikan laut yang diawetkan dengan garam dan dijemur.",
        "guna": "Lauk pauk tahan lama."
    },
    "Sarang Walet": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Edible_bird%27s_nest.jpg/640px-Edible_bird%27s_nest.jpg",
        "desc": "Sarang burung walet murni (warna putih/mangkok).",
        "guna": "Sup kesehatan, harga sangat mahal."
    },
    "Manau (Rotan)": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Calamus_manan.jpg/640px-Calamus_manan.jpg",
        "desc": "Batang rotan diameter besar (Manau).",
        "guna": "Bahan baku furniture (Kursi/Meja)."
    },
    "Madu Hutan": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Honey_comb.jpg/640px-Honey_comb.jpg",
        "desc": "Madu murni dari lebah liar hutan Mentawai.",
        "guna": "Kesehatan, obat."
    }
}
DEFAULT_IMG = "https://via.placeholder.com/300x200.png?text=Mentawai+Market"

# DAFTAR KAPAL
LIST_KAPAL = ["Mentawai Fast", "KMP Ambu-Ambu", "KMP Gambolo", "Sabuk Nusantara", "Kapal Perintis"]

# ==========================================
# 2. FRONT-END ENGINE (CSS PRO V20)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        #MainMenu {visibility: visible;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] { background-color: transparent; z-index: 1; }

        /* Running Text */
        .marquee-container {
            width: 100%; background-color: #222; color: #FFA500; padding: 10px;
            white-space: nowrap; overflow: hidden; box-sizing: border-box; border-bottom: 2px solid #FFA500; margin-bottom: 20px;
        }
        .marquee { display: inline-block; padding-left: 100%; animation: marquee 25s linear infinite; font-weight: bold; font-family: monospace; }
        @keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }

        /* Cards */
        .card-container {
            background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px);
            border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 15px; margin-bottom: 15px; transition: all 0.3s ease;
        }
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
    # 1. RUNNING TEXT
    berita = settings_data.get('berita', 'Selamat Datang di Mentawai Smart Market')
    st.markdown(f"""<div class="marquee-container"><div class="marquee">📢 INFO PASAR: {berita} &nbsp;&nbsp;|&nbsp;&nbsp; 🚢 UPDATE: Cek Status Kapal di bawah...</div></div>""", unsafe_allow_html=True)

    st.title("📡 Pusat Pantauan Harga")
    
    # 2. STATUS KAPAL
    with st.expander("🚢 STATUS LOGISTIK & KAPAL", expanded=True):
        cols = st.columns(len(LIST_KAPAL))
        for i, nama_kapal in enumerate(LIST_KAPAL):
            status = logistik_data.get(nama_kapal, "Jadwal Normal")
            wc = "ship-ok"
            if "Batal" in status or "Rusak" in status: wc = "ship-bad"
            elif "Docking" in status or "Tunda" in status: wc = "ship-warn"
            with cols[i]: st.markdown(f"""<div style="text-align:center; border:1px solid #444; padding:8px; border-radius:8px;"><small>{nama_kapal}</small><br><span class="{wc}">{status}</span></div>""", unsafe_allow_html=True)

    st.divider()
    
    # 3. DAFTAR HARGA + GAMBAR
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
        # Tambahan item tani lainnya
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
    # Grafik & Laporan
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
        st.divider(); st.caption("v20.0 Visual Pro")

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
