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
    /* 1. Fondo degradado */
    .stApp { 
        background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); 
    }
    
    /* 2. Ajustes de contenedor */
    .block-container { 
        padding-top: 2rem !important; 
        max-width: 700px !important; 
    }
    
    /* 3. Estilo de la tarjeta blanca */
    .haus-card { 
        background: white; 
        padding: 2.5rem; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        margin-top: -20px;
        color: #0C2D33;
    }
    
    /* 4. Botón personalizado */
    div.stButton > button:first-child {
        width: 100%;
        background-color: #0C2D33 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 12px;
        height: 3.5em;
        border: none;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #164a54 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* Ocultar elementos innecesarios */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES LEGALES (Para el Log de Responsabilidad Proactiva) ---
POLICY_VERSION = "v1.0-2024-05-24" # Actualizar cada vez que cambie el texto legal

# --- SELECTOR DE IDIOMA ---
col_l, col_r = st.columns([4, 1])
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
        "btn": "¡REGISTRARME Y BUSCAR MATCH!", 
        "error": "⚠️ Requerido: Nombre, WhatsApp y aceptar las 3 casillas legales.",
        "success": "✅ ¡Datos guardados con éxito!", "loading": "Guardando datos...",
        "legal_header": "⚖️ Información Legal y Privacidad",
        "legal_notice": "Responsable: HausMate. Finalidad: Gestionar tu solicitud y realizar el 'match'.",
        "legal_opt1": "He leído y acepto la Política de Privacidad y el tratamiento de mis datos. *",
        "legal_opt2": "Autorizo expresamente a compartir mi contacto y perfil con otros matches. *",
        "legal_opt3": "Acepto ser contactado por WhatsApp para la gestión del servicio. *",
        "view_policy": "Leer Política de Privacidad completa",
        "policy_content": """
        **POLÍTICA DE PRIVACIDAD Y CONSENTIMIENTO DE TRATAMIENTO**
        
        **Responsable del Tratamiento:** HausMate (info@haus-es.com).
        
        **Finalidad:** Gestión de perfil y facilitar la conexión ("Matching").
        
        **Base Jurídica:** Consentimiento del usuario (Art. 6.1.a RGPD).
        
        **Cesión de Datos:** Nombre y WhatsApp compartidos solo con matches positivos.
        
        **Plazo:** Mientras se preste el servicio o hasta revocación.
        
        **Derechos:** Acceso, supresión y portabilidad vía info@haus-es.com.
        """
    },
    "English": {
        "title": "📝 Find your HausMate",
        "name": "Full Name *", "wa": "WhatsApp (with +) *", "age": "Age",
        "lw": "Living preference", "budget": "Max Budget (€)",
        "rooms": "Rooms in house", "country": "Country of origin",
        "idioma_form": "Main language", "zonas": "📍 Preferred areas",
        "zonas_help": "Select districts", "move_in": "Move-in date",
        "move_out": "Move-out date", "notes": "About you (work, hobbies...)",
        "btn": "REGISTER & FIND MATCH!", 
        "error": "⚠️ Required: Name, WhatsApp, and the 3 legal consent boxes.",
        "success": "✅ Data saved successfully.", "loading": "Saving data...",
        "legal_header": "⚖️ Legal Information & Privacy",
        "legal_notice": "Controller: HausMate. Purpose: Manage your request and match you.",
        "legal_opt1": "I accept the Privacy Policy and data processing. *",
        "legal_opt2": "I authorize sharing my contact/profile with matches. *",
        "legal_opt3": "I agree to be contacted via WhatsApp for service management. *",
        "view_policy": "Read full Privacy Policy",
        "policy_content": "Full policy content as per Spanish version but in English context..."
    }
}
t = texts[lang]

# --- LOGO / CABECERA ---
c_l, c_c, c_r = st.columns([1, 2, 1])
with c_c:
    logo_path = "logo_hausmate.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown(f"<h1 style='text-align: center; color: #0C2D33; margin-bottom: 20px;'>HAUSMATE</h1>", unsafe_allow_html=True)

# --- FUNCIÓN DB (SUPABASE) ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        
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
        fn = st.text_input(t["name"], placeholder="John Doe")
        wa = st.text_input(t["wa"], placeholder="+34 600 000 000")
        age_val = st.number_input(t["age"], 18, 99, 25)
        lw = st.selectbox(t["lw"], ["Mixto", "Solo Mujeres", "Solo Hombres"])
    
    with c2:
        bg = st.number_input(t["budget"], 0, 5000, 800, step=50)
        rm = st.selectbox(t["rooms"], ["1", "2", "3", "4", "5+"])
        country = st.text_input(t["country"], "España" if lang == "Español" else "Spain")
        idioma_val = st.selectbox(t["idioma_form"], ["Spanish", "English", "French", "German", "Other"])

    st.write(t["zonas"])
    distritos = ["Centro", "Arganzuela", "Retiro", "Salamanca", "Chamartín", "Tetuán", "Chamberí", "Fuencarral-El Pardo", "Moncloa-Aravaca", "Latina", "Carabanchel", "Usera", "Puente de Vallecas", "Moratalaz", "Ciudad Lineal", "Hortaleza", "Villaverde", "Villa de Vallecas", "Vicálvaro", "San Blas-Canillejas", "Barajas", "Otros"]
    barrios_sel = st.multiselect(t["zonas_help"], options=distritos, label_visibility="collapsed")
    
    c3, c4 = st.columns(2)
    with c3:
        m_in = st.date_input(t["move_in"], dt.date.today())
    with c4:
        m_out = st.date_input(t["move_out"], dt.date.today() + dt.timedelta(days=180))
        
    notes_content = st.text_area(t["notes"], placeholder="..." )
    
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=12, tiles="cartodbpositron")
    st_folium(m, height=180, use_container_width=True, key="madrid_map")
    
    st.markdown("---")
    st.markdown(f"**{t['legal_header']}**")
    st.caption(t['legal_notice'])
    
    check_privacy = st.checkbox(t['legal_opt1'])
    check_share = st.checkbox(t['legal_opt2'])
    check_whatsapp = st.checkbox(t['legal_opt3'])
    
    with st.expander(t['view_policy']):
        st.markdown(t['policy_content'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    enviar = st.form_submit_button(t["btn"])
st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE ENVÍO ---
if enviar:
    if not fn or not wa or not check_privacy or not check_share or not check_whatsapp:
        st.error(t["error"])
    else:
        now_utc = dt.datetime.now(dt.timezone.utc)
        clean_wa = "".join(filter(str.isdigit, wa))
        dedupe_key = hashlib.md5(f"{clean_wa}_{now_utc.date()}".encode()).hexdigest()

        # Registro de consentimiento (Log de Accountability)
        legal_log = {
            "policy_version": POLICY_VERSION,
            "consent_timestamp": now_utc.isoformat(),
            "accepted_privacy": check_privacy,
            "accepted_share_data": check_share,
            "accepted_whatsapp": check_whatsapp,
            "user_ip_logged": True # Opcional: registrar que se guardó el log
        }

        payload = {
            "nombre": fn,
            "telefono": wa,
            "telefono_raw": wa,
            "dedupe_key": dedupe_key,
            "edad": int(age_val),
            "budget": int(bg),
            "habitaciones": rm,
            "pref_genero": lw,
            "zona": ", ".join(barrios_sel) if barrios_sel else "Sin especificar",
            "inicio": m_in.isoformat(),
            "fin": m_out.isoformat(),
            "notas": f"Country: {country}. UI_Lang: {lang}. {notes_content}",
            "idioma": idioma_val,
            "created_at": now_utc.isoformat(),
            "consent_log": legal_log # GUARDAMOS EL LOG DENTRO DEL REGISTRO
        }
        
        with st.spinner(t["loading"]):
            exito, error_msg = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success(t["success"])
            else:
                if "duplicate key" in error_msg.lower():
                    st.warning("⚠️ Ya recibimos tu solicitud hoy.")
                else:
                    st.error(f"Error: {error_msg}")
