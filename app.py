import os
import datetime as dt
import hashlib
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO PERSONALIZADO ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    .block-container { padding-top: 1.5rem !important; max-width: 800px !important; }
    .haus-card { 
        background: white; padding: 2rem; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin-top: 10px; color: #0C2D33; 
    }
    div.stButton > button:first-child {
        width: 100%; background-color: #0C2D33 !important; color: white !important;
        font-weight: bold; border-radius: 12px; height: 3.8em; border: none;
    }
    [data-testid="stImage"] { display: flex; justify-content: center; margin-bottom: 5px; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- TRADUCCIONES ---
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
        "success": "✅ ¡Datos guardados con éxito!", "loading": "Procesando registro...",
        "legal_header": "⚖️ Información Legal y Privacidad",
        "legal_opt1": "Acepto la Política de Privacidad. *",
        "legal_opt2": "Autorizo compartir mi perfil con otros matches. *",
        "legal_opt3": "Acepto contacto por WhatsApp. *",
        "view_policy": "Ver Política Completa",
        "policy_content": "Responsable: HausMate. Finalidad: Gestión de perfiles y Matching."
    }
}
t = texts["Español"]

# --- LOGO ---
st.image("https://raw.githubusercontent.com/chechoderiquer-dev/hausmate_match/main/logo_hausmate.png", width=220)

# --- FUNCIÓN DB ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"].replace('"', '').strip()
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].replace('"', '').strip()
        table = st.secrets["SUPABASE_TABLE"].replace('"', '').strip()
        supabase = create_client(url, key)
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# --- FORMULARIO ---
st.markdown('<div class="haus-card">', unsafe_allow_html=True)
with st.form("main_form", border=False):
    st.markdown(f"<h3 style='text-align: center;'>{t['title']}</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fn = st.text_input(t["name"])
        wa = st.text_input(t["wa"])
        age_val = st.number_input(t["age"], 18, 99, 25)
    with c2:
        bg = st.number_input(t["budget"], 0, 5000, 800)
        rm = st.selectbox(t["rooms"], ["1", "2", "3", "4", "5+"])
        country = st.text_input(t["country"], "España")

    distritos = ["Centro", "Arganzuela", "Retiro", "Salamanca", "Chamberí", "Tetuán", "Otros"]
    barrios_sel = st.multiselect(t["zonas"], options=distritos)
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
            "nombre": fn, "telefono": wa, "budget": int(bg), 
            "zona": ", ".join(barrios_sel), "Perfil": notes_content,
            "created_at": dt.datetime.now().isoformat()
        }
        with st.spinner(t["loading"]):
            ok, err = save_to_supabase(payload)
            if ok:
                st.balloons()
                st.success(t["success"])
            else:
                st.error(f"Error: {err}")
