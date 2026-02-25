import os
import datetime as dt
import hashlib
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO PERSONALIZADO RESPONSIVO ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    .block-container { padding-top: 1.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 800px !important; }
    .haus-card { background: white; padding: 1.5rem; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin-top: 10px; color: #0C2D33; width: 100%; box-sizing: border-box; }
    @media (min-width: 768px) { .haus-card { padding: 2.5rem; } }
    div.stButton > button:first-child { width: 100%; background-color: #0C2D33 !important; color: white !important; font-weight: bold; border-radius: 12px; height: 3.8em; border: none; transition: all 0.3s ease; font-size: 16px; }
    div.stButton > button:first-child:hover { background-color: #164a54 !important; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
    [data-testid="stImage"] { display: flex; justify-content: center; margin-bottom: 5px; }
    #MainMenu, footer, header {visibility: hidden;}
    input, select, textarea { font-size: 16px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES ---
POLICY_VERSION = "v1.1-2024-05-24" 
lang = st.radio("Lang", ["Español", "English"], horizontal=True, label_visibility="collapsed")

texts = {
    "Español": {
        "title": "📝 Encuentra tu HausMate",
        "name": "Nombre completo *", "wa": "WhatsApp (+34) *", "age": "Edad",
        "gender": "Tu género", "lw": "Preferencia de convivencia", "budget": "Presupuesto Máximo (€)",
        "rooms": "Habitaciones", "country": "País de origen",
        "idioma_form": "Idioma principal", "zonas": "📍 Zonas preferidas",
        "zonas_help": "Selecciona los distritos", "move_in": "¿Cuándo entras?",
        "move_out": "¿Hasta cuándo?", "notes": "Sobre ti (trabajo, hobbies...)",
        "btn": "¡REGISTRARME Y BUSCAR MATCH!", 
        "error": "⚠️ Requerido: Nombre, WhatsApp y aceptar las casillas legales.",
        "success": "✅ ¡Datos guardados con éxito!", "loading": "Procesando...",
        "legal_header": "⚖️ Información Legal y Privacidad",
        "legal_opt1": "Acepto la Política de Privacidad. *",
        "legal_opt2": "Autorizo compartir mi perfil con otros matches. *",
        "legal_opt3": "Acepto contacto por WhatsApp. *",
        "view_policy": "Ver Política Completa",
        "policy_content": "Responsable: HausMate (info@haus-es.com). Finalidad: Matching."
    },
    "English": {
        "title": "📝 Find your HausMate",
        "name": "Full Name *", "wa": "WhatsApp *", "age": "Age",
        "gender": "Gender", "lw": "Preference", "budget": "Max Budget (€)",
        "rooms": "Rooms", "country": "Country",
        "idioma_form": "Language", "zonas": "📍 Areas",
        "zonas_help": "Select districts", "move_in": "Move-in",
        "move_out": "Move-out", "notes": "About you",
        "btn": "REGISTER!", 
        "error": "⚠️ Fields required.",
        "success": "✅ Success!", "loading": "Loading...",
        "legal_header": "⚖️ Legal",
        "legal_opt1": "Privacy Policy *",
        "legal_opt2": "Share profile *",
        "legal_opt3": "WhatsApp contact *",
        "view_policy": "Full Policy",
        "policy_content": "Data controller: HausMate."
    }
}
t = texts[lang]

st.image("https://raw.githubusercontent.com/chechoderiquer-dev/hausmate_match/main/logo_hausmate.png", width=220)

def save_to_supabase(data):
    try:
        from supabase import create_client
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_ROLE_KEY"])
        supabase.table(st.secrets["SUPABASE_TABLE"]).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

st.markdown('<div class="haus-card">', unsafe_allow_html=True)
with st.form("main_form", border=False):
    st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{t['title']}</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fn = st.text_input(t["name"])
        wa = st.text_input(t["wa"])
        age_val = st.number_input(t["age"], 18, 99, 25)
        user_gender = st.selectbox(t["gender"], ["Mujer", "Hombre", "Otro"])
    with c2:
        bg = st.number_input(t["budget"], 0, 5000, 800)
        rm = st.selectbox(t["rooms"], ["1", "2", "3", "4", "5+"])
        pref_gender = st.selectbox(t["lw"], ["Mixto", "Solo Mujeres", "Solo Hombres"])
        country = st.text_input(t["country"], "España")

    idioma_val = st.selectbox(t["idioma_form"], ["Spanish", "English", "Other"])
    barrios_sel = st.multiselect(t["zonas"], ["Centro", "Chamberí", "Salamanca", "Tetuán", "Otros"])
    
    c3, c4 = st.columns(2)
    m_in = c3.date_input(t["move_in"], dt.date.today())
    m_out = c4.date_input(t["move_out"], dt.date.today() + dt.timedelta(days=180))
    notes_content = st.text_area(t["notes"])
    
    st_folium(folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron"), height=200, use_container_width=True)
    
    st.markdown("---")
    st.write(f"**{t['legal_header']}**")
    c_p = st.checkbox(t["legal_opt1"])
    c_s = st.checkbox(t["legal_opt2"])
    c_w = st.checkbox(t["legal_opt3"])
    with st.expander(t["view_policy"]):
        st.write(t["policy_content"])
    enviar = st.form_submit_button(t["btn"])
st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not fn or not wa or not c_p or not c_s or not c_w:
        st.error(t["error"])
    else:
        payload = {
            "nombre": fn, "telefono": wa, "budget": int(bg), "edad": int(age_val),
            "zona": ", ".join(barrios_sel), "Perfil": notes_content,
            "created_at": dt.datetime.now().isoformat()
        }
        with st.spinner(t["loading"]):
            ok, err = save_to_supabase(payload)
            if ok: st.success(t["success"])
            else: st.error(f"Error: {err}")
