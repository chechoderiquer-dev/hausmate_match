import os
import datetime as dt
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    .haus-card { background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .stButton>button { width: 100%; background-color: #0C2D33; color: white; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

DISTRITOS = ["Arganzuela", "Centro", "Chamberí", "Retiro", "Salamanca", "Tetuán", "Otros"]

# --- FUNCIÓN DE ENVÍO ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        # Usamos la URL corregida de tu Project ID: xmexitrkqnrtibapevrk
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        
        from supabase import create_client
        supabase = create_client(url, key)
        
        # Intentamos insertar
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# --- INTERFAZ ---
st.title("🏠 HausMate Match")

with st.container():
    st.markdown('<div class="haus-card">', unsafe_allow_html=True)
    with st.form("form_final"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo *")
            whatsapp = st.text_input("WhatsApp *")
        with col2:
            presupuesto = st.number_input("Presupuesto (€)", 0, 5000, 800)
            preferencia = st.selectbox("Preferencia", ["Mixto", "Hombres", "Mujeres"])
        
        barrios_sel = st.multiselect("📍 Distritos", options=DISTRITOS)
        notas = st.text_area("Notas")
        
        enviar = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not nombre or not whatsapp:
        st.error("Rellena nombre y WhatsApp")
    else:
        # IMPORTANTE: Los nombres de estas llaves deben ser IGUALES a tus columnas en Supabase
        payload = {
            "full_name": nombre,
            "whatsapp": whatsapp,
            "budget": presupuesto,
            "living_with": preferencia,
            "barrios": barrios_sel, # Si en Supabase se llama 'distritos', cambia aquí "barrios" por "distritos"
            "notes": notas,
            "created_at": dt.datetime.now().isoformat()
        }
        
        with st.spinner("Guardando..."):
            exito, error = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("¡Enviado con éxito!")
            else:
                st.error("Error de columnas")
                st.info(f"Detalle técnico: {error}")
                st.warning("Revisa que en Supabase la columna se llame 'barrios'. Si se llama distinto, cambia el nombre en el código.")
