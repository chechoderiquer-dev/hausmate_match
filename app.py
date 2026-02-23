import os
import json
import datetime as dt
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import requests

import folium
from folium.features import GeoJson, GeoJsonTooltip
from streamlit_folium import st_folium

# =========================
# BRAND / UI
# =========================
APP_NAME = "HausMate Match"
LOGO_PATH_LOCAL = "logo.png"

BRAND_BG = "#7FBBC2"
BRAND_BG_2 = "#D9F1F3"
BRAND_DARK = "#0C2D33"
WHITE = "#FFFFFF"

def brand_css():
    st.markdown(
        f"""
        <style>
          .stApp {{
            background: linear-gradient(180deg, {BRAND_BG} 0%, {BRAND_BG_2} 60%, #ffffff 100%);
          }}
          .block-container {{
            padding-top: 2rem;
          }}
          h1, h2, h3, h4, h5, h6, p, label, div {{
            color: {BRAND_DARK} !important;
          }}
          .haus-card {{
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(12,45,51,0.12);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 6px 18px rgba(12,45,51,0.10);
          }}
          .haus-badge {{
            display:inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.75);
            border: 1px solid rgba(12,45,51,0.12);
            font-weight: 600;
          }}
          .stButton > button {{
            background: {BRAND_DARK};
            color: {WHITE} !important;
            border-radius: 12px;
            border: 0;
            width: 100%;
            font-weight: bold;
          }}
          .danger {{
            background: rgba(255, 0, 0, 0.08);
            border: 1px solid rgba(255, 0, 0, 0.18);
            padding: 10px;
            border-radius: 12px;
            color: #cc0000;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_header():
    col1, col2 = st.columns([1, 4], vertical_alignment="center")
    with col1:
        if os.path.exists(LOGO_PATH_LOCAL):
            st.image(LOGO_PATH_LOCAL, use_container_width=True)
        else:
            st.markdown(f"<h1>🏠</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h1 style='margin:0;'>{APP_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='margin:0; opacity:0.8;'>Encuentra tu match ideal en Madrid</p>", unsafe_allow_html=True)

# =========================
# SECRETS & SUPABASE
# =========================
def get_secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except:
        pass
    return os.getenv(name, default)

def get_supabase_client():
    url = get_secret("SUPABASE_URL").strip()
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY").strip()
    if not url or not key:
        return None, "Faltan credenciales de Supabase en Secrets."
    try:
        from supabase import create_client
        return create_client(url, key), ""
    except Exception as e:
        return None, f"Error al conectar: {e}"

def save_to_supabase(payload: Dict[str, Any]) -> (bool, str):
    table = get_secret("SUPABASE_TABLE", "hausmate_leads").strip()
    client, err = get_supabase_client()
    if client is None: return False, err
    try:
        client.table(table).insert(payload).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# =========================
# MAP LOGIC
# =========================
BARRIOS_GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/madrid-neighborhoods.geojson"

@st.cache_data(show_spinner=False)
def load_barrios_geojson():
    r = requests.get(BARRIOS_GEOJSON_URL, timeout=30)
    r.raise_for_status()
    return r.json()

def extract_barrios_list(geojson):
    names = []
    for f in geojson.get("features", []):
        props = f.get("properties", {})
        for k in ["name", "NAME", "neighborhood", "NOMBRE"]:
            if props.get(k):
                names.append(str(props[k]).strip())
                break
    return sorted(list(set(names))) if names else ["Madrid Centro"]

# =========================
# APP CORE
# =========================
st.set_page_config(page_title=APP_NAME, page_icon="🏠", layout="centered")
brand_css()
render_header()

# Sidebar Admin
with st.sidebar:
    st.markdown("### 🔒 Acceso Admin")
    admin_pw = get_secret("ADMIN_PASSWORD")
    input_pw = st.text_input("Contraseña", type="password")
    if st.button("Login"):
        if input_pw == admin_pw and admin_pw != "":
            st.session_state["admin_ok"] = True
            st.success("Acceso concedido")
        else:
            st.error("Incorrecto")

# Inicializar estado de barrios
if "selected_barrios" not in st.session_state:
    st.session_state["selected_barrios"] = []

# Carga de datos geográficos
try:
    geojson_data = load_barrios_geojson()
    barrios_options = extract_barrios_list(geojson_data)
except Exception as e:
    st.error(f"Error cargando mapa: {e}")
    geojson_data, barrios_options = None, []

# FORMULARIO
with st.container():
    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    st.subheader("📝 Tu perfil de búsqueda")
    
    with st.form("survey_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Nombre completo *")
            whatsapp = st.text_input("WhatsApp (ej: +34600000000) *")
        with col2:
            age = st.number_input("Edad", 18, 99, 25)
            budget = st.number_input("Presupuesto Max (€/mes)", 0, 5000, 800)

        col3, col4 = st.columns(2)
        with col3:
            rooms = st.selectbox("Habitaciones", ["1", "2", "3", "4+"])
        with col4:
            living_with = st.selectbox("Preferencia", ["Hombres", "Mujeres", "Mixto"])

        st.markdown("---")
        st.markdown("### 📍 ¿Dónde quieres vivir?")
        selected = st.multiselect("Busca y selecciona barrios", options=barrios_options)
        
        # Mapa visual (no interactivo para selección, el selectbox manda)
        if geojson_data:
            m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
            folium.GeoJson(
                geojson_data,
                style_function=lambda x: {
                    'fillColor': BRAND_DARK if x['properties'].get('name') in selected else '#ffffff',
                    'color': BRAND_DARK,
                    'weight': 1,
                    'fillOpacity': 0.5 if x['properties'].get('name') in selected else 0.1
                }
            ).add_to(m)
            st_folium(m, height=300, use_container_width=True, key="madrid_map")

        st.markdown("---")
        col5, col6 = st.columns(2)
        with col5:
            move_in = st.date_input("Fecha entrada", dt.date.today())
        with col6:
            move_out = st.date_input("Fecha salida", dt.date.today() + dt.timedelta(days=90))

        notes = st.text_area("Notas adicionales (mascotas, trabajo, etc.)")
        
        submitted = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown("</div>", unsafe_allow_html=True)

# PROCESAMIENTO
if submitted:
    if not full_name or not whatsapp:
        st.error("Por favor rellena los campos obligatorios (*)")
    else:
        # Scoring simple
        score_val = 60
        if len(selected) > 0: score_val += 20
        if len(notes) > 10: score_val += 20

        payload = {
            "full_name": full_name,
            "whatsapp": whatsapp,
            "age": age,
            "budget": budget,
            "rooms": rooms,
            "living_with": living_with,
            "barrios": selected,
            "move_in": str(move_in),
            "move_out": str(move_out),
            "notes": notes,
            "score_total": score_val,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }

        success, err = save_to_supabase(payload)
        if success:
            st.balloons()
            st.success("¡Perfil enviado con éxito! Nos pondremos en contacto pronto.")
        else:
            st.error(f"Error al guardar: {err}")

# VISTA ADMIN
if st.session_state.get("admin_ok"):
    st.markdown("---")
    st.subheader("📊 Leads Recientes")
    client, _ = get_supabase_client()
    if client:
        try:
            res = client.table(get_secret("SUPABASE_TABLE", "hausmate_leads")).select("*").execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data))
        except Exception as e:
            st.error(f"Error admin: {e}")
