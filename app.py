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
        
        # Insertar datos
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
            nombre_input = st.text_input("Nombre completo *")
            tel_input = st.text_input("Teléfono/WhatsApp *")
            edad_input = st.number_input("Edad", 18, 99, 25)
        with col2:
            budget_input = st.number_input("Presupuesto (€)", 0, 5000, 800)
            pref_gen = st.selectbox("Preferencia de género", ["Mixto", "Hombres", "Mujeres"])
            genero_input = st.selectbox("Tu género", ["Hombre", "Mujer", "Otro"])
        
        zona_sel = st.multiselect("📍 Zonas de interés", options=DISTRITOS)
        
        c3, c4 = st.columns(2)
        with c3:
            fecha_inicio = st.date_input("Fecha entrada", dt.date.today())
        with c4:
            fecha_fin = st.date_input("Fecha salida", dt.date.today() + dt.timedelta(days=90))
            
        notas_input = st.text_area("Notas adicionales")
        enviar = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not nombre_input or not tel_input:
        st.error("⚠️ Nombre y Teléfono son obligatorios.")
    else:
        # Generamos la dedupe_key (obligatoria en tu tabla)
        # Usamos el teléfono y la fecha para que sea única
        unique_str = f"{tel_input}_{dt.datetime.now().isoformat()}"
        d_key = hashlib.md5(unique_str.encode()).hexdigest()

        # PAYLOAD MAPEADO EXACTAMENTE A TU SQL
        payload = {
            "nombre": nombre_input,
            "telefono": tel_input,
            "telefono_raw": tel_input,
            "edad": int(edad_input),
            "genero": genero_input,
            "pref_genero": pref_gen,
            "zona": ", ".join(zona_sel), # Convertimos lista a texto
            "budget": int(budget_input),
            "inicio": fecha_inicio.isoformat(),
            "fin": fecha_fin.isoformat(),
            "notas": notas_input,
            "dedupe_key": d_key, # Evita el error de constraint
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner("Guardando en HausMate Leads..."):
            exito, error_msg = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("✅ ¡PERFIL CREADO! Ya apareces en la base de datos.")
            else:
                st.error("❌ Error de validación en la tabla.")
                st.info(f"Detalle: {error_msg}")
