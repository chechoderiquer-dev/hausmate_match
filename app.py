import os
import datetime as dt
import hashlib
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

DISTRITOS = ["Arganzuela", "Centro", "Chamberí", "Retiro", "Salamanca", "Tetuán", "Otros"]

# --- FUNCIÓN DE ENVÍO ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        
        from supabase import create_client
        supabase = create_client(url, key)
        
        # Insertar datos en la tabla hausmate_leads
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# --- INTERFAZ ---
st.title("🏠 HausMate Match")

with st.container():
    st.markdown('<div class="haus-card">', unsafe_allow_html=True)
    with st.form("form_final"):
        st.subheader("📝 Tu perfil de búsqueda")
        
        col1, col2 = st.columns(2)
        with col1:
            nombre_input = st.text_input("Nombre completo *")
            tel_input = st.text_input("Teléfono/WhatsApp *")
            edad_input = st.number_input("Edad", 18, 99, 25)
            genero_user = st.selectbox("Tu género", ["mujer", "hombre", "otro"])
        
        with col2:
            budget_input = st.number_input("Presupuesto Máximo (€)", 0, 5000, 800)
            pref_gen = st.selectbox("Preferencia de convivencia", ["mixto", "solo_mujeres", "solo_hombres"])
            # NUEVOS DATOS SOLICITADOS
            hab_max = st.selectbox("Máximo de habitaciones en la casa", ["1", "2", "3", "4", "5+"])
            banos_min = st.selectbox("Mínimo de baños", ["1", "2", "3+"])
        
        st.write("📍 **¿Dónde quieres vivir?**")
        zona_sel = st.multiselect("Selecciona distritos", options=DISTRITOS)
        
        c3, c4 = st.columns(2)
        with c3:
            fecha_inicio = st.date_input("Fecha entrada preferida", dt.date.today())
        with c4:
            fecha_fin = st.date_input("Fecha salida aproximada", dt.date.today() + dt.timedelta(days=90))
            
        notas_input = st.text_area("Notas adicionales (idiomas, hobbies, trabajo...)")
        
        # Mapa visual de Madrid
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
        st_folium(m, height=200, use_container_width=True, key="mapa_madrid")
        
        enviar = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not nombre_input or not tel_input:
        st.error("⚠️ El nombre y el teléfono son obligatorios.")
    else:
        # Generar dedupe_key única para evitar errores de restricción SQL
        unique_str = f"{tel_input}_{dt.datetime.now().isoformat()}"
        d_key = hashlib.md5(unique_str.encode()).hexdigest()

        # PAYLOAD MAPEADO EXACTAMENTE A TU TABLA hausmate_leads
        payload = {
            "nombre": nombre_input,
            "telefono": tel_input,
            "telefono_raw": tel_input,
            "edad": int(edad_input),
            "genero": genero_user,
            "pref_genero": pref_gen,
            "zona": "|".join(zona_sel), # Usamos el separador que suele haber en tus datos
            "budget": int(budget_input),
            "inicio": fecha_inicio.isoformat(),
            "fin": fecha_fin.isoformat(),
            "habitaciones": hab_max,
            "banos_min": int(banos_min.replace("+", "")),
            "notas": notas_input,
            "dedupe_key": d_key,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner("Guardando perfil..."):
            exito, error_msg = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("✅ ¡Perfecto! Tu perfil ha sido registrado con todos los detalles.")
            else:
                st.error("❌ Error al guardar en la base de datos.")
                st.info(f"Detalle técnico: {error_msg}")
