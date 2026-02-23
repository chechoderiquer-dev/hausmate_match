import os
import datetime as dt
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO PERSONALIZADO ---
def apply_custom_style():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
        .haus-card { 
            background: white; 
            padding: 2.5rem; 
            border-radius: 20px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        }
        .logo-container { text-align: center; padding-bottom: 20px; }
        .stButton>button { 
            width: 100%; 
            background-color: #0C2D33 !important; 
            color: white !important; 
            font-weight: bold; 
            border-radius: 12px; 
            height: 3.5em; 
            border: none;
        }
        </style>
        """, unsafe_allow_html=True)

apply_custom_style()

# --- LÓGICA DEL LOGO (MÁS ROBUSTA) ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)

# Lista de posibles nombres por si acaso
posibles_logos = ["LOGO_HAUSMATE.png", "logo_hausmate.png", "LOGO_HAUSMATE.PNG"]
logo_encontrado = False

for nombre_archivo in posibles_logos:
    if os.path.exists(nombre_archivo):
        st.image(nombre_archivo, width=350)
        logo_encontrado = True
        break

if not logo_encontrado:
    st.warning(f"⚠️ No se encontró el archivo del logo. Asegúrate de que se llame exactamente 'LOGO_HAUSMATE.png' y esté en la carpeta principal.")
    st.markdown("<h1 style='text-align: center; color: #0C2D33;'>HAUSMATE</h1>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
DISTRITOS = ["Centro", "Chamberí", "Retiro", "Salamanca", "Tetuán", "Moncloa", "Arganzuela", "Otros"]

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
    with st.form("form_match_final"):
        st.subheader("📝 Encuentra tu HausMate")
        
        col1, col2 = st.columns(2)
        with col1:
            fn = st.text_input("Nombre completo *")
            wa = st.text_input("WhatsApp (con prefijo +34) *")
            age = st.number_input("Edad", 18, 99, 25)
            lw = st.selectbox("Preferencia de convivencia", ["mixto", "solo_mujeres", "solo_hombres"])
        
        with col2:
            bg = st.number_input("Presupuesto Máximo (€)", 0, 5000, 1000)
            rm = st.selectbox("Máximo de habitaciones en casa", ["1", "2", "3", "4", "5+"])
            country = st.text_input("País de origen", "España")
            idioma = st.selectbox("Idioma principal", ["Spanish", "English", "French", "German", "Other"])

        st.write("📍 **Zonas preferidas**")
        barrios_sel = st.multiselect("Selecciona los distritos", options=DISTRITOS)
        
        c3, c4 = st.columns(2)
        with c3:
            m_in = st.date_input("¿Cuándo quieres entrar?", dt.date.today())
        with c4:
            m_out = st.date_input("¿Hasta cuándo te quedas?", dt.date.today() + dt.timedelta(days=180))
            
        notes = st.text_area("Cuéntanos sobre ti (trabajo, hobbies, convivencia...)")
        
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=12, tiles="cartodbpositron")
        st_folium(m, height=200, use_container_width=True, key="mapa_vFinal")
        
        enviar = st.form_submit_button("¡REGISTRARME Y BUSCAR MATCH!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE ENVÍO ---
if enviar:
    if not fn or not wa:
        st.error("⚠️ El nombre y el WhatsApp son obligatorios.")
    else:
        payload = {
            "full_name": fn,
            "whatsapp": wa,
            "age": int(age),
            "budget": int(bg),
            "rooms": rm,
            "living_with": lw,
            "barrios": barrios_sel, 
            "move_in": m_in.isoformat(),
            "move_out": m_out.isoformat(),
            "notes": f"Idioma: {idioma}. {notes}",
            "country_guess": country,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner("Guardando en la base de datos..."):
            exito, error = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("✅ ¡PERFECTO! Datos guardados en tu tabla SQL.")
            else:
                st.error(f"Error de base de datos: {error}")
