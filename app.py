import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import json
import os
import time

# 1. SETUP PAGE
st.set_page_config(
    page_title="Mentawai Smart Market", 
    page_icon="🌴", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS VISUAL ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .acuan-box {
        background-color: #0e1117;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 5px;
    }
    .harga-besar { font-size: 20px; font-weight: bold; color: #00CC96; }
    .label-kecil { font-size: 11px; color: #aaaaaa; text-transform: uppercase; margin-bottom: 5px;}
    
    .berita-box {
        background-color: #262730;
        border-left: 5px solid #FFA500;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .duit-box { background-color: #00CC96; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px; }
    
    .hasil-box { padding: 15px; border-radius: 8px; margin-top: 10px; color: white; font-weight: bold; text-align: center; }
    .danger {background-color: #FF4B4B;} 
    .warning {background-color: #FFA500; color: black;} 
    .success {background-color: #00CC96;} 
    
    /* Style Kartu Agen */
    .agen-card {
        background-color: #1E1E1E;
        border: 1px solid #444;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    .footer-credit {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #0e1117; color: #888; text-align: center;
        padding: 10px; font-size: 12px; border-top: 1px solid #333; z-index: 100;
    }
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
    st.title("🌴 MENTAWAI MARKET")
    
    if 'is_admin_logged_in' not in st.session_state:
        st.session_state.is_admin_logged_in = False

    # === FORM LOGIN ===
    if not st.session_state.is_admin_logged_in:
        # MENU USER BIASA
        menu = st.radio("Menu Warga:", ["🏠 Dashboard", "📞 Cari Toke/Agen", "🧮 Kalkulator Cuan", "📝 Lapor Harga"])
        st.divider()
        st.write("🔐 **Admin Area**")
        
        with st.form("login_form"):
            pw = st.text_input("Password Admin:", type="password")
            submitted = st.form_submit_button("LOGIN")
            
            if submitted:
                pw_bersih = pw.strip()
                if "admin_password" not in st.secrets:
                    st.error("⚠️ EROR: Password belum disetting di Secrets!")
                elif pw_bersih == st.secrets["admin_password"]:
                    st.success("✅ Login Berhasil!")
                    st.session_state.is_admin_logged_in = True
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Password Salah!")

    # === MENU ADMIN ===
    else:
        st.success("👤 Admin Mode")
        # MENU LENGKAP ADMIN
        menu = st.radio("Menu Admin:", [
            "🏠 Dashboard", 
            "📞 Cari Toke/Agen", # Admin juga bisa liat
            "👥 Kelola Data Toke", # Menu Baru Admin
            "🧮 Kalkulator Cuan", 
            "📝 Lapor Harga", 
            "📢 Update Berita", 
            "⚙️ Update Harga", 
            "📂 Download Data", 
            "🗑️ Hapus Laporan"
        ])
        st.divider()
        if st.button("Logout"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    st.divider()
    st.link_button("💬 Chat Admin (WA)", "https://wa.me/6281234567890") # GANTI NOMOR WA
    st.caption("v9.0 - Direktori Toke")

# --- HELPER DATA ---
def get_settings():
    if db:
        try:
            doc = db.collection('settings').document('general').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}

def get_harga_acuan():
    if db:
        try:
            doc = db.collection('settings').document('harga_padang').get()
            if doc.exists: return doc.to_dict()
        except: pass
    return {}

settings_data = get_settings()
acuan_data = get_harga_acuan()

LIST_KOMODITAS = [
    "Cengkeh Super", "Cengkeh Biasa", "Gagang Cengkeh", "Minyak Cengkeh",
    "Kopra", "Pinang", "Kakao (Coklat)", "Sagu", "Nilam", "Gambir",
    "Gurita", "Lobster", "Kerapu", "Teripang", "Ikan Asin",
    "Sarang Walet", "Manau (Rotan)", "Madu Hutan"
]

# ================= MENU 1: DASHBOARD =================
if menu == "🏠 Dashboard":
    st.title("📡 Pusat Pantauan Harga")
    
    if settings_data.get('berita'):
        st.markdown(f"""<div class="berita-box"><h3>📢 INFO: {settings_data.get('tanggal_berita', '-')}</h3><p>{settings_data.get('berita')}</p></div>""", unsafe_allow_html=True)
    
    st.markdown("### 🏙️ Harga Acuan (Gudang Padang)")
    tab1, tab2, tab3 = st.tabs(["🌱 HASIL TANI", "🐟 HASIL LAUT", "🦅 HASIL HUTAN"])
    
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">CENGKEH SUPER</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh Super', 0):,}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">CENGKEH BIASA</div><div class="harga-besar">Rp {acuan_data.get('Cengkeh Biasa', 0):,}</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">KOPRA</div><div class="harga-besar">Rp {acuan_data.get('Kopra', 0):,}</div></div>""", unsafe_allow_html=True)
        with c4: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">PINANG</div><div class="harga-besar">Rp {acuan_data.get('Pinang', 0):,}</div></div>""", unsafe_allow_html=True)
    with tab2:
        l1, l2, l3, l4 = st.columns(4)
        with l1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">GURITA</div><div class="harga-besar">Rp {acuan_data.get('Gurita', 0):,}</div></div>""", unsafe_allow_html=True)
        with l2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">LOBSTER</div><div class="harga-besar">Rp {acuan_data.get('Lobster', 0):,}</div></div>""", unsafe_allow_html=True)
        with l3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">TERIPANG</div><div class="harga-besar">Rp {acuan_data.get('Teripang', 0):,}</div></div>""", unsafe_allow_html=True)
        with l4: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">KERAPU</div><div class="harga-besar">Rp {acuan_data.get('Kerapu', 0):,}</div></div>""", unsafe_allow_html=True)
    with tab3:
        h1, h2, h3 = st.columns(3)
        with h1: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">SARANG WALET</div><div class="harga-besar">Rp {acuan_data.get('Sarang Walet', 0):,}</div></div>""", unsafe_allow_html=True)
        with h2: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">MANAU (ROTAN)</div><div class="harga-besar">Rp {acuan_data.get('Manau (Rotan)', 0):,}</div></div>""", unsafe_allow_html=True)
        with h3: st.markdown(f"""<div class="acuan-box"><div class="label-kecil">MADU HUTAN</div><div class="harga-besar">Rp {acuan_data.get('Madu Hutan', 0):,}</div></div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("📈 Grafik Tren Harga")
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu').stream()
        data_all = []
        for d in docs:
            dt = d.to_dict()
            if dt.get('waktu') and dt.get('harga_angka'):
                data_all.append({"Barang": dt.get('item'), "Harga": dt.get('harga_angka'), "Waktu": dt.get('waktu'), "Lokasi": dt.get('lokasi'), "Catatan": dt.get('catatan')})
        df = pd.DataFrame(data_all)
        if not df.empty:
            pilihan_grafik = st.selectbox("Pilih Komoditas:", df['Barang'].unique())
            df_chart = df[df['Barang'] == pilihan_grafik].copy()
            if not df_chart.empty:
                st.line_chart(df_chart, x="Waktu", y="Harga", color="#00CC96")
        else: st.warning("Belum ada data grafik.")

# ================= MENU BARU: CARI TOKE (USER) =================
elif menu == "📞 Cari Toke/Agen":
    st.title("📞 Direktori Toke & Agen")
    st.write("Temukan pembeli terpercaya di sekitarmu. Hubungi mereka langsung!")
    
    # Filter Lokasi
    cari_lokasi = st.text_input("🔍 Cari berdasarkan Desa / Kecamatan:", placeholder="Contoh: Sikakap")
    
    if db:
        agen_ref = db.collection('agen_mentawai').stream()
        data_agen = []
        for a in agen_ref:
            ad = a.to_dict()
            # Filter Sederhana
            if cari_lokasi:
                if cari_lokasi.lower() in ad.get('lokasi', '').lower():
                    data_agen.append(ad)
            else:
                data_agen.append(ad)
        
        if data_agen:
            for agen in data_agen:
                with st.container():
                    st.markdown(f"""
                    <div class="agen-card">
                        <h3>👤 {agen.get('nama', 'Tanpa Nama')}</h3>
                        <p>📍 <b>Lokasi:</b> {agen.get('lokasi', '-')}</p>
                        <p>📦 <b>Menerima:</b> {agen.get('barang', '-')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    # Tombol WA
                    no_hp = agen.get('wa', '').replace("08", "628").replace("-", "").replace(" ", "")
                    link_wa = f"https://wa.me/{no_hp}?text=Halo%20Bos,%20saya%20dapat%20info%20dari%20Mentawai%20Market.%20Mau%20tanya%20harga..."
                    st.link_button(f"💬 Chat WA ({agen.get('wa')})", link_wa)
        else:
            st.info("Belum ada data Toke di lokasi ini.")

# ================= MENU BARU: KELOLA TOKE (ADMIN ONLY) =================
elif menu == "👥 Kelola Data Toke":
    st.title("👥 Kelola Data Toke/Agen")
    st.write("Tambahkan kontak Toke terpercaya biar petani gampang jual barang.")
    
    with st.form("tambah_agen"):
        nama = st.text_input("Nama Toke/Gudang")
        lokasi = st.text_input("Lokasi (Desa/Kecamatan)")
        wa = st.text_input("Nomor WA (Contoh: 0812xxx)")
        barang = st.text_input("Barang yang diterima (Contoh: Cengkeh, Kopra)")
        
        if st.form_submit_button("Simpan Data Toke"):
            if nama and wa:
                db.collection('agen_mentawai').add({
                    "nama": nama, "lokasi": lokasi, "wa": wa, "barang": barang,
                    "added_at": datetime.datetime.now()
                })
                st.success("Data Toke tersimpan!")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    st.subheader("Daftar Toke Terdaftar")
    docs = db.collection('agen_mentawai').stream()
    for doc in docs:
        d = doc.to_dict()
        c1, c2 = st.columns([4,1])
        with c1: st.write(f"**{d.get('nama')}** ({d.get('lokasi')}) - {d.get('wa')}")
        with c2: 
            if st.button("Hapus", key=doc.id):
                db.collection('agen_mentawai').document(doc.id).delete()
                st.rerun()

# ================= MENU: KALKULATOR =================
elif menu == "🧮 Kalkulator Cuan":
    st.title("🧮 Kalkulator Pintar")
    tab_cek, tab_hitung = st.tabs(["🕵️ Cek Kejujuran Agen", "💰 Hitung Total Panen"])
    with tab_cek:
        c1, c2 = st.columns(2)
        with c1:
            kom = st.selectbox("Barang:", LIST_KOMODITAS, key="cek_kom")
            harga_pusat = acuan_data.get(kom, 0)
            st.info(f"Harga Pusat: **Rp {harga_pusat:,}**")
            tawaran = st.number_input("Tawaran Agen (Rp):", step=500, key="cek_tawar")
        with c2:
            if tawaran > 0 and harga_pusat > 0:
                selisih = harga_pusat - tawaran
                persen = (selisih / harga_pusat) * 100
                st.metric("Potongan", f"Rp {selisih:,} /kg")
                if persen < 20: st.markdown(f"""<div class="hasil-box success">✅ BAGUS!</div>""", unsafe_allow_html=True)
                elif persen < 40: st.markdown(f"""<div class="hasil-box warning">👌 WAJAR</div>""", unsafe_allow_html=True)
                else: st.markdown(f"""<div class="hasil-box danger">🛑 MENCEKIK!</div>""", unsafe_allow_html=True)
    with tab_hitung:
        c3, c4 = st.columns(2)
        with c3:
            berat = st.number_input("Berat Panen (Kg):", min_value=1, step=1)
            harga_deal = st.number_input("Harga Deal per Kg (Rp):", min_value=0, step=500)
        with c4:
            if berat > 0 and harga_deal > 0:
                total_duit = berat * harga_deal
                st.markdown(f"""<div class="duit-box">Total Pendapatan:<br>Rp {total_duit:,}</div>""", unsafe_allow_html=True)

# ================= MENU: LAPOR =================
elif menu == "📝 Lapor Harga":
    st.title("📝 Lapor Harga Lapangan")
    with st.form("lapor"):
        item = st.selectbox("Barang", LIST_KOMODITAS)
        price = st.number_input("Harga (Rp)", step=500)
        loc = st.text_input("Lokasi", placeholder="Nama Desa")
        note = st.text_input("Catatan", placeholder="Nama Agen / Info")
        if st.form_submit_button("Kirim"):
            if price > 0:
                db.collection('mentawai_v2').add({"item": item, "harga_angka": price, "lokasi": loc, "catatan": note, "waktu": datetime.datetime.now()})
                st.success("Terkirim!")
                time.sleep(1)
                st.rerun()

# ================= MENU ADMIN LAINNYA =================
elif menu == "📢 Update Berita":
    st.title("📢 Update Kabar Pasar")
    current_news = settings_data.get('berita', '')
    with st.form("news_form"):
        news_text = st.text_area("Isi Berita:", value=current_news)
        if st.form_submit_button("Terbitkan"):
            db.collection('settings').document('general').set({"berita": news_text, "tanggal_berita": datetime.datetime.now().strftime("%d %b %Y")})
            st.success("Berita Terbit!")
            st.rerun()

elif menu == "⚙️ Update Harga":
    st.title("⚙️ Update Harga Pusat")
    st.link_button("🔍 Cek Google", "https://www.google.com/search?q=harga+komoditas+sumatera+barat+hari+ini")
    with st.form("update_komplit"):
        st.write("Update Database Harga")
        updates = {}
        for item in LIST_KOMODITAS:
            updates[item] = st.number_input(f"{item}", value=acuan_data.get(item, 0))
        if st.form_submit_button("SIMPAN SEMUA"):
            updates["updated_at"] = datetime.datetime.now()
            db.collection('settings').document('harga_padang').set(updates, merge=True)
            st.success("Tersimpan!")
            st.rerun()

elif menu == "📂 Download Data":
    st.title("📂 Download Arsip Data")
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).stream()
        data_dl = []
        for d in docs:
            dt = d.to_dict()
            data_dl.append({"Tanggal": dt.get('waktu').strftime("%Y-%m-%d") if dt.get('waktu') else "-", "Komoditas": dt.get('item'), "Harga": dt.get('harga_angka'), "Lokasi": dt.get('lokasi')})
        df_download = pd.DataFrame(data_dl)
        if not df_download.empty:
            st.dataframe(df_download.head(), use_container_width=True)
            csv = df_download.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 DOWNLOAD CSV", data=csv, file_name=f'laporan_{datetime.datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')
        else: st.warning("Belum ada data.")

elif menu == "🗑️ Hapus Laporan":
    st.title("🗑️ Hapus Laporan Sampah")
    docs = db.collection('mentawai_v2').order_by('waktu', direction=firestore.Query.DESCENDING).limit(20).stream()
    for doc in docs:
        d = doc.to_dict()
        with st.container(border=True):
            c1, c2 = st.columns([4,1])
            with c1: st.write(f"**{d.get('item')}** - Rp {d.get('harga_angka', 0):,} ({d.get('lokasi')})")
            with c2: 
                if st.button("Hapus", key=doc.id):
                    db.collection('mentawai_v2').document(doc.id).delete()
                    st.rerun()

# FOOTER
st.markdown("""<div class="footer-credit">Developed by <b>Mr. Ghost</b> & Tim Mentawai Bangkit © 2026</div>""", unsafe_allow_html=True)
