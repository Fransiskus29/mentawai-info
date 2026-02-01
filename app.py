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

# --- SIDEBAR ---
with st.sidebar:
    st.title("🌴 MENTAWAI MARKET")
    
    if 'is_admin_logged_in' not in st.session_state:
        st.session_state.is_admin_logged_in = False

    if not st.session_state.is_admin_logged_in:
        menu = st.radio("Menu:", ["🏠 Dashboard", "🧮 Cek Kejujuran", "📝 Lapor Harga"])
        st.divider()
        pw = st.text_input("🔐 Admin Area", type="password")
        if "admin_password" in st.secrets:
