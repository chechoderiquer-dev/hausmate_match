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
    .stApp { 
        background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); 
    }
    .block-container { 
        padding-top: 1.5rem !important; 
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 800px !important; 
    }
    .haus-card { 
        background: white; 
        padding: 1.5rem; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        margin-top: 10px;
        color: #0C2D33;
        width: 100%;
        box-sizing: border-box;
    }
    @media (min-width: 768px) {
        .haus-card { padding: 2.5rem; }
    }
    div.stButton > button:first-child {
        width: 100%;
        background-color: #0C2D33 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 12px;
        height: 3.8em;
        transition: all 0.3s ease;
    }
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin-bottom: 5px;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- TRADUCCIONES Y LÓGICA ---
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
        "policy_content": "Responsable: HausMate (info@haus-es.com). Finalidad: Gestión de perfiles y Matching."
    }
}
# Fallback simple para el diccionario
t = texts["Español"] if lang == "Español" else texts["Español"] 

# --- CABECERA ---
logo_url = "https://raw.githubusercontent.com/chechoderiquer-dev/hausmate_match/main/logo_hausmate.png"
st.image(logo_url, width=220)

# --- FUNCIÓN DB ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
        table = st.secrets["SUPABASE_TABLE"]
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
    
    barrios_sel = st.multiselect(t["zonas"], ["Centro", "Chamberí", "Salamanca", "Retiro", "Otros"])
    notes_content = st.text_area(t["notes"])
    
    st.markdown("---")
    st.write(t["legal_header"])
    c_p = st.checkbox(t["legal_opt1"])
    c_s = st.checkbox(t["legal_opt2"])
    c_w = st.checkbox(t["legal_opt3"])
    
    with st.expander(t["view_policy"]):
        st.write(t["policy_content"])
        
    enviar = st.form_submit_button(t["btn"])
st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not fn or not wa or not c_p:
        st.error(t["error"])
    else:
        payload = {
            "nombre": fn, "telefono": wa, "budget": int(bg), 
            "zona": ", ".join(barrios_sel), "Perfil": notes_content,
            "created_at": dt.datetime.now().isoformat()
        }
        with st.spinner(t["loading"]):
            ok, err = save_to_supabase(payload)
            if ok: st.success(t["success"])
            else: st.error(f"Error: {err}")
