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
    .hasil-box { padding: 15px; border-radius: 8px; margin-top: 10px; color: white; font-weight: bold; text-align: center; }
    .danger {background-color: #FF4B4B;} 
    .warning {background-color: #FFA500; color: black;} 
    .success {background-color: #00CC96;} 
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

# --- SIDEBAR (LOGIC LOGIN DIPERBAIKI) ---
with st.sidebar:
    st.title("🌴 MENTAWAI MARKET")
    
    # Inisialisasi status login
    if 'is_admin_logged_in' not in st.session_state:
        st.session_state.is_admin_logged_in = False

    # === JIKA BELUM LOGIN ===
    if not st.session_state.is_admin_logged_in:
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga"])
        st.divider()
        
        st.write("🔐 **Admin Area**")
        pw = st.text_input("Masukkan Password:", type="password", key="login_pw")
        
        # TOMBOL LOGIN (BIAR LEBIH JELAS)
        if st.button("LOGIN ADMIN"):
            if "admin_password" in st.secrets:
                if pw == st.secrets["admin_password"]:
                    st.success("Login Berhasil! 🔓")
                    st.session_state.is_admin_logged_in = True
                    time.sleep(1) # Kasih waktu baca sukses dulu
                    st.rerun()
                else:
                    st.error("❌ Password Salah Bos! Coba lagi.")
            else:
                st.error("⚠️ Password belum disetting di Secrets!")

    # === JIKA SUDAH LOGIN ===
    else:
        st.success("👤 Mode Admin: AKTIF")
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga", "📢 Update Berita", "⚙️ Update Harga", "🗑️ Hapus Data"])
        
        st.divider()
        if st.button("Logout Keluar"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    st.divider()
    st.link_button("💬 Chat Admin (WA)", "https://wa.me/6281234567890") # GANTI NO WA
    st.caption("v7.1 - Login Fixed")

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
    
    # BERITA
    if settings_data.get('berita'):
        st.markdown(f"""<div class="berita-box"><h3>📢 INFO: {settings_data.get('tanggal_berita', '-')}</h3><p>{settings_data.get('berita')}</p></div>""", unsafe_allow_html=True)
    
    # HARGA ACUAN
    st.markdown("### 🏙️ Harga Acuan (Gudang Padang/Ekspor)")
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
    
    # GRAFIK TREN HARGA
    st.subheader("📈 Grafik Tren Harga (Real-Time)")
    if db:
        docs = db.collection('mentawai_v2').order_by('waktu').stream()
        data_all = []
        for d in docs:
            dt = d.to_dict()
            if dt.get('waktu') and dt.get('harga_angka'):
                data_all.append({
                    "Barang": dt.get('item'),
                    "Harga": dt.get('harga_angka'),
                    "Waktu": dt.get('waktu'),
                    "Lokasi": dt.get('lokasi'),
                    "Catatan": dt.get('catatan')
                })
        
        df = pd.DataFrame(data_all)
        if not df.empty:
            pilihan_grafik = st.selectbox("Pilih Komoditas:", df['Barang'].unique())
            df_chart = df[df['Barang'] == pilihan_grafik].copy()
            if not df_chart.empty:
                st.line_chart(df_chart, x="Waktu", y="Harga", color="#00CC96")
                with st.expander(f"Lihat Detail {pilihan_grafik}"):
                    df_display = df_chart.sort_values(by="Waktu", ascending=False)
                    df_display['Harga'] = df_display['Harga'].apply(lambda x: f"Rp {x:,}")
                    df_display['Waktu'] = df_display['Waktu'].dt.strftime("%d %b %H:%M")
                    st.dataframe(df_display[['Waktu', 'Harga', 'Lokasi', 'Catatan']], use_container_width=True, hide_index=True)
            else: st.info("Data grafik belum cukup.")
        else: st.warning("Belum ada data.")

# ================= MENU 2: KALKULATOR =================
elif menu == "🧮 Cek Kejujuran":
    st.title("🧮 Kalkulator Cekik Agen")
    c_kiri, c_kanan = st.columns(2)
    with c_kiri:
        kom = st.selectbox("Mau jual apa?", LIST_KOMODITAS)
        harga_pusat = acuan_data.get(kom, 0)
        
        if harga_pusat == 0: st.warning("⚠️ Harga acuan belum diset Admin.")
        else: st.info(f"Patokan Padang: **Rp {harga_pusat:,}**")
        tawaran = st.number_input("Tawaran Agen (Rp):", step=500)

    with c_kanan:
        st.write("### 📊 Analisa:")
        if tawaran > 0 and harga_pusat > 0:
            selisih = harga_pusat - tawaran
            persen = (selisih / harga_pusat) * 100
            st.metric("Potongan Agen", f"Rp {selisih:,} /kg")
            if persen < 20: st.markdown(f"""<div class="hasil-box success">✅ HARGA ISTIMEWA!</div>""", unsafe_allow_html=True)
            elif persen < 40: st.markdown(f"""<div class="hasil-box warning">👌 HARGA WAJAR</div>""", unsafe_allow_html=True)
            else: st.markdown(f"""<div class="hasil-box danger">🛑 HARGA MENCEKIK!</div>""", unsafe_allow_html=True)

# ================= MENU 3: LAPOR =================
elif menu == "📝 Lapor Harga":
    st.title("📝 Lapor Harga Lapangan")
    with st.form("lapor"):
        item = st.selectbox("Jenis Barang", LIST_KOMODITAS)
        price = st.number_input("Harga Tawaran (Rp)", step=500)
        loc = st.text_input("Lokasi", placeholder="Nama Desa")
        note = st.text_input("Catatan", placeholder="Nama Agen / Info")
        if st.form_submit_button("Kirim"):
            if price > 0:
                db.collection('mentawai_v2').add({"item": item, "harga_angka": price, "lokasi": loc, "catatan": note, "waktu": datetime.datetime.now()})
                st.success("Terkirim!")
                time.sleep(1)
                st.rerun()

# ================= MENU 4: UPDATE BERITA =================
elif menu == "📢 Update Berita":
    st.title("📢 Update Kabar Pasar")
    current_news = settings_data.get('berita', '')
    with st.form("news_form"):
        news_text = st.text_area("Isi Berita:", value=current_news)
        if st.form_submit_button("Terbitkan"):
            db.collection('settings').document('general').set({
                "berita": news_text,
                "tanggal_berita": datetime.datetime.now().strftime("%d %b %Y")
            })
            st.success("Berita Terbit!")
            st.rerun()

# ================= MENU 5: UPDATE HARGA (KOMPLIT) =================
elif menu == "⚙️ Update Harga":
    st.title("⚙️ Update Harga Pusat")
    st.link_button("🔍 Cek Google", "https://www.google.com/search?q=harga+komoditas+sumatera+barat+hari+ini")
    
    with st.form("update_komplit"):
        st.subheader("🌱 Hasil Tani")
        c1, c2, c3 = st.columns(3)
        h_cs = c1.number_input("Cengkeh Super", value=acuan_data.get('Cengkeh Super', 0))
        h_cb = c2.number_input("Cengkeh Biasa", value=acuan_data.get('Cengkeh Biasa', 0))
        h_gc = c3.number_input("Gagang Cengkeh", value=acuan_data.get('Gagang Cengkeh', 0))
        
        c4, c5, c6 = st.columns(3)
        h_kop = c4.number_input("Kopra", value=acuan_data.get('Kopra', 0))
        h_pin = c5.number_input("Pinang", value=acuan_data.get('Pinang', 0))
        h_kak = c6.number_input("Kakao (Coklat)", value=acuan_data.get('Kakao (Coklat)', 0))
        
        c7, c8, c9 = st.columns(3)
        h_sag = c7.number_input("Sagu", value=acuan_data.get('Sagu', 0))
        h_nil = c8.number_input("Nilam", value=acuan_data.get('Nilam', 0))
        h_gam = c9.number_input("Gambir", value=acuan_data.get('Gambir', 0))
        
        st.divider()
        st.subheader("🐟 Hasil Laut")
        l1, l2, l3 = st.columns(3)
        h_gur = l1.number_input("Gurita", value=acuan_data.get('Gurita', 0))
        h_lob = l2.number_input("Lobster", value=acuan_data.get('Lobster', 0))
        h_ker = l3.number_input("Kerapu", value=acuan_data.get('Kerapu', 0))
        
        l4, l5 = st.columns(2)
        h_ter = l4.number_input("Teripang", value=acuan_data.get('Teripang', 0))
        h_ias = l5.number_input("Ikan Asin", value=acuan_data.get('Ikan Asin', 0))
        
        st.divider()
        st.subheader("🦅 Hasil Hutan")
        u1, u2, u3 = st.columns(3)
        h_wal = u1.number_input("Sarang Walet", value=acuan_data.get('Sarang Walet', 0))
        h_man = u2.number_input("Manau (Rotan)", value=acuan_data.get('Manau (Rotan)', 0))
        h_mad = u3.number_input("Madu Hutan", value=acuan_data.get('Madu Hutan', 0))

        if st.form_submit_button("SIMPAN HARGA"):
            data_baru = {
                "Cengkeh Super": h_cs, "Cengkeh Biasa": h_cb, "Gagang Cengkeh": h_gc,
                "Kopra": h_kop, "Pinang": h_pin, "Kakao (Coklat)": h_kak,
                "Sagu": h_sag, "Nilam": h_nil, "Gambir": h_gam,
                "Gurita": h_gur, "Lobster": h_lob, "Kerapu": h_ker, "Teripang": h_ter, "Ikan Asin": h_ias,
                "Sarang Walet": h_wal, "Manau (Rotan)": h_man, "Madu Hutan": h_mad,
                "updated_at": datetime.datetime.now()
            }
            db.collection('settings').document('harga_padang').set(data_baru, merge=True)
            st.success("Tersimpan!")
            st.rerun()

# ================= MENU 6: HAPUS =================
elif menu == "🗑️ Hapus Data":
    st.title("🗑️ Hapus Laporan")
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
