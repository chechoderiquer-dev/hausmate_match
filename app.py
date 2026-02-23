import os
import datetime as dt
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO PERSONALIZADO ---
st.markdown("""
    <style>
    /* Fondo degradado */
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    
    /* Reducción de espacios (Padding/Margin) */
    .block-container { padding-top: 1rem !important; }
    .stImage { margin-bottom: -30px !important; } /* Sube el contenido debajo del logo */
    
    /* Estilo de la tarjeta */
    .haus-card { 
        background: white; 
        padding: 2rem; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-top: -20px; /* Sube la tarjeta hacia el logo */
    }
    
    .stButton>button { 
        width: 100%; 
        background-color: #0C2D33 !important; 
        color: white !important; 
        font-weight: bold; 
        border-radius: 12px; 
        height: 3.5em; 
    }
    
    /* Selector de idioma más pequeño */
    div[data-testid="stRadio"] > div { gap: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SELECTOR DE IDIOMA ---
col_lang_l, col_lang_r = st.columns([3, 1])
with col_lang_r:
    lang = st.radio("Language", ["Español", "English"], horizontal=True, label_visibility="collapsed")

# --- DICCIONARIO DE TRADUCCIONES ---
texts = {
    "Español": {
        "title": "📝 Encuentra tu HausMate",
        "name": "Nombre completo *", "wa": "WhatsApp (+34) *", "age": "Edad",
        "gender": "Tu género", "lw": "Preferencia de convivencia",
        "budget": "Presupuesto Máximo (€)", "rooms": "Máximo de habitaciones",
        "country": "País de origen", "idioma_form": "Idioma principal",
        "zonas": "📍 Zonas preferidas", "zonas_help": "Selecciona los distritos",
        "move_in": "¿Cuándo quieres entrar?", "move_out": "¿Hasta cuándo?",
        "notes": "Sobre ti (trabajo, hobbies...)", "btn": "¡REGISTRARME!",
        "error": "⚠️ Nombre y WhatsApp obligatorios.", "success": "✅ ¡Datos guardados!", "loading": "Guardando..."
    },
    "English": {
        "title": "📝 Find your HausMate",
        "name": "Full Name *", "wa": "WhatsApp (include +) *", "age": "Age",
        "gender": "Your gender", "lw": "Living preference",
        "budget": "Max Budget (€)", "rooms": "Max rooms",
        "country": "Country of origin", "idioma_form": "Main language",
        "zonas": "📍 Preferred areas", "zonas_help": "Select districts",
        "move_in": "Move-in date", "move_out": "Move-out date",
        "notes": "About you (work, hobbies...)", "btn": "REGISTER!",
        "error": "⚠️ Name and WhatsApp are required.", "success": "✅ Data saved.", "loading": "Saving..."
    }
}
t = texts[lang]

# --- LOGO CENTRADO ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    # Usando el nombre que analizamos: LOGO_HAUSMATE.png
    if os.path.exists("LOGO_HAUSMATE.png"):
        st.image("LOGO_HAUSMATE.png", use_container_width=True)
    else:
        st.markdown(f"<h1 style='text-align: center; color: #0C2D33;'>HAUSMATE</h1>", unsafe_allow_html=True)

# --- FUNCIÓN DB ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        from supabase import create_client
        supabase = create_client(url, key)
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# --- FORMULARIO ---
with st.container():
    st.markdown('<div class="haus-card">', unsafe_allow_html=True)
    with st.form("main_form"):
        st.subheader(t["title"])
        c1, c2 = st.columns(2)
        with c1:
            fn = st.text_input(t["name"])
            wa = st.text_input(t["wa"])
            age = st.number_input(t["age"], 18, 99, 25)
            lw = st.selectbox(t["lw"], ["mixto", "solo_mujeres", "solo_hombres"])
        with c2:
            bg = st.number_input(t["budget"], 0, 5000, 1000)
            rm = st.selectbox(t["rooms"], ["1", "2", "3", "4", "5+"])
            country = st.text_input(t["country"], "España" if lang == "Español" else "Spain")
            idioma_val = st.selectbox(t["idioma_form"], ["Spanish", "English", "French", "German", "Other"])

        st.write(t["zonas"])
        distritos = ["Centro", "Chamberí", "Retiro", "Salamanca", "Tetuán", "Moncloa", "Arganzuela", "Otros"]
        barrios_sel = st.multiselect(t["zonas_help"], options=distritos, label_visibility="collapsed")
        
        c3, c4 = st.columns(2)
        with c3:
            m_in = st.date_input(t["move_in"], dt.date.today())
        with c4:
            m_out = st.date_input(t["move_out"], dt.date.today() + dt.timedelta(days=180))
            
        notes = st.text_area(t["notes"])
        
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=12, tiles="cartodbpositron")
        st_folium(m, height=200, use_container_width=True, key="mapa_final")
        
        enviar = st.form_submit_button(t["btn"])
    st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE ENVÍO ---
if enviar:
    if not fn or not wa:
        st.error(t["error"])
    else:
        payload = {
            "full_name": fn, "whatsapp": wa, "age": int(age), "budget": int(bg),
            "rooms": rm, "living_with": lw, "barrios": barrios_sel, 
            "move_in": m_in.isoformat(), "move_out": m_out.isoformat(),
            "notes": f"Lang: {lang}. {notes}", "country_guess": country,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        with st.spinner(t["loading"]):
            exito, error = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success(t["success"])
            else:
                st.error(f"Error: {error}")
