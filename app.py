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
    /* 1. Fondo degradado */
    .stApp { 
        background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); 
    }
    
    /* 2. Eliminar el espacio superior de Streamlit */
    .block-container { 
        padding-top: 1rem !important; 
        max-width: 700px !important; 
    }
    
    /* 3. Reducir espacio entre logo y tarjeta */
    [data-testid="stVerticalBlock"] > div:has(div.logo-container) {
        margin-bottom: -50px !important;
    }

    .logo-container { 
        text-align: center;
        margin-bottom: -40px; /* Ajuste fino para subir la tarjeta */
    }
    
    /* 4. Estilo de la tarjeta blanca */
    .haus-card { 
        background: white; 
        padding: 2.5rem; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        margin-top: 0px;
    }
    
    /* 5. Botón */
    .stButton>button { 
        width: 100%; 
        background-color: #0C2D33 !important; 
        color: white !important; 
        font-weight: bold; 
        border-radius: 12px; 
        height: 3.5em; 
    }

    /* Ocultar espacios vacíos de Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SELECTOR DE IDIOMA ---
# Lo ponemos en una columna pequeña a la derecha para que no robe espacio
col_l, col_r = st.columns([3, 1])
with col_r:
    lang = st.radio("Lang", ["Español", "English"], horizontal=True, label_visibility="collapsed")

# --- DICCIONARIO DE TRADUCCIONES ---
texts = {
    "Español": {
        "title": "📝 Encuentra tu HausMate",
        "name": "Nombre completo *", "wa": "WhatsApp (+34) *", "age": "Edad",
        "lw": "Preferencia de convivencia", "budget": "Presupuesto Máximo (€)",
        "rooms": "Habitaciones en casa", "country": "País de origen",
        "idioma_form": "Idioma principal", "zonas": "📍 Zonas preferidas",
        "zonas_help": "Selecciona los distritos", "move_in": "¿Cuándo entras?",
        "move_out": "¿Hasta cuándo?", "notes": "Sobre ti (trabajo, hobbies...)",
        "btn": "¡REGISTRARME Y BUSCAR MATCH!", "error": "⚠️ Requerido: Nombre y WhatsApp.",
        "success": "✅ ¡Datos guardados!", "loading": "Guardando..."
    },
    "English": {
        "title": "📝 Find your HausMate",
        "name": "Full Name *", "wa": "WhatsApp (with +) *", "age": "Age",
        "lw": "Living preference", "budget": "Max Budget (€)",
        "rooms": "Rooms in house", "country": "Country of origin",
        "idioma_form": "Main language", "zonas": "📍 Preferred areas",
        "zonas_help": "Select districts", "move_in": "Move-in date",
        "move_out": "Move-out date", "notes": "About you (work, hobbies...)",
        "btn": "REGISTER & FIND MATCH!", "error": "⚠️ Required: Name and WhatsApp.",
        "success": "✅ Data saved.", "loading": "Saving..."
    }
}
t = texts[lang]

# --- LOGO CENTRADO ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
c_l, c_c, c_r = st.columns([1, 2, 1])
with c_c:
    logo_names = ["LOGO_HAUSMATE.png", "logo_hausmate.png"]
    logo_found = False
    for name in logo_names:
        if os.path.exists(name):
            st.image(name, use_container_width=True)
            logo_found = True
            break
    if not logo_found:
        st.markdown(f"<h1 style='text-align: center; color: #0C2D33;'>HAUSMATE</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

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
        st_folium(m, height=200, use_container_width=True, key="mapa_vFinal")
        
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
            "notes": f"UI_Lang: {lang}. {notes}", "country_guess": country,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        with st.spinner(t["loading"]):
            exito, error = save_to_supabase(payload)
            if exito:
                st.balloons(); st.success(t["success"])
            else:
                st.error(f"Error: {error}")
