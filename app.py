import os
import datetime as dt
import hashlib
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO Y LOGO ---
def apply_custom_style():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
        .haus-card { background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .logo-container { text-align: center; margin-bottom: 20px; }
        .stButton>button { 
            width: 100%; 
            background-color: #0C2D33 !important; 
            color: white !important; 
            font-weight: bold; 
            border-radius: 10px; 
            height: 3em; 
        }
        </style>
        """, unsafe_allow_html=True)

apply_custom_style()

# --- INSERTAR LOGO ---
# Reemplaza "logo.png" por el nombre exacto de tu archivo (ej. "hausmate_logo.png")
try:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    # Si subiste el logo a GitHub o lo tienes local, pon el nombre aquí:
    st.image("logo.png", width=200) 
    st.markdown('</div>', unsafe_allow_html=True)
except:
    st.markdown("<h1 style='text-align: center; color: #0C2D33;'>🏠 HausMate Match</h1>", unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
DISTRITOS = ["Arganzuela", "Centro", "Chamberí", "Retiro", "Salamanca", "Tetuán", "Moncloa", "Otros"]
IDIOMAS = ["Spanish", "English", "French", "German", "Italian", "Portuguese", "Other"]

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
    with st.form("form_final"):
        st.subheader("📝 Perfil de Búsqueda")
        
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo *")
            tel = st.text_input("Teléfono/WhatsApp *")
            edad = st.number_input("Edad", 18, 99, 25)
            genero = st.selectbox("Tu género", ["mujer", "hombre", "otro"])
            idioma = st.selectbox("Idioma principal", options=IDIOMAS)
        
        with col2:
            budget = st.number_input("Presupuesto Máximo (€)", 0, 5000, 800)
            pref_gen = st.selectbox("Preferencia de convivencia", ["mixto", "solo_mujeres", "solo_hombres"])
            hab_max = st.selectbox("Máximo de habitaciones", ["1", "2", "3", "4", "5+"])
            banos = st.selectbox("Mínimo de baños", ["1", "2", "3+"])
        
        st.write("📍 **Zonas de interés**")
        zona_sel = st.multiselect("Selecciona distritos", options=DISTRITOS)
        
        c3, c4 = st.columns(2)
        with c3:
            f_inicio = st.date_input("Fecha entrada", dt.date.today())
        with c4:
            f_fin = st.date_input("Fecha salida", dt.date.today() + dt.timedelta(days=90))
            
        notas = st.text_area("Notas adicionales")
        
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
        st_folium(m, height=200, use_container_width=True, key="mapa_madrid")
        
        enviar = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not nombre or not tel:
        st.error("⚠️ Nombre y Teléfono son obligatorios.")
    else:
        unique_id = hashlib.md5(f"{tel}_{dt.datetime.now()}".encode()).hexdigest()
        
        payload = {
            "nombre": nombre,
            "telefono": tel,
            "telefono_raw": tel,
            "edad": int(edad),
            "genero": genero,
            "pref_genero": pref_gen,
            "idioma": idioma,
            "zona": "|".join(zona_sel),
            "budget": int(budget),
            "inicio": f_inicio.isoformat(),
            "fin": f_fin.isoformat(),
            "habitaciones": hab_max,
            "banos_min": int(banos.replace("+", "")),
            "notas": notas,
            "dedupe_key": unique_id,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner("Registrando..."):
            exito, error = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("✅ ¡Registro completado con éxito!")
            else:
                st.error(f"Error: {error}")
