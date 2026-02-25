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
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    .block-container { padding-top: 1.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 800px !important; }
    .haus-card { background: white; padding: 1.5rem; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin-top: 10px; color: #0C2D33; width: 100%; box-sizing: border-box; }
    @media (min-width: 768px) { .haus-card { padding: 2.5rem; } }
    div.stButton > button:first-child { width: 100%; background-color: #0C2D33 !important; color: white !important; font-weight: bold; border-radius: 12px; height: 3.8em; border: none; transition: all 0.3s ease; font-size: 16px; }
    div.stButton > button:first-child:hover { background-color: #164a54 !important; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
    [data-testid="stImage"] { display: flex; justify-content: center; margin-bottom: 5px; }
    #MainMenu, footer, header {visibility: hidden;}
    input, select, textarea { font-size: 16px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES LEGALES ---
POLICY_VERSION = "v1.1-2024-05-24" 

# --- SELECTOR DE IDIOMA ---
col_l, col_r = st.columns([3, 1])
with col_r:
    lang = st.radio("Lang", ["Español", "English"], horizontal=True, label_visibility="collapsed")

# --- DICCIONARIO DE TRADUCCIONES ---
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
        "success": "✅ ¡Datos guardados con éxito!", "loading": "Procesando registro...",
        "generic_error": "❌ Error al procesar el registro. Inténtalo más tarde.",
        "legal_header": "⚖️ Información Legal y Privacidad",
        "legal_opt1": "Acepto la Política de Privacidad. *",
        "legal_opt2": "Autorizo compartir mi perfil con otros matches. *",
        "legal_opt3": "Acepto contacto por WhatsApp. *",
        "view_policy": "Ver Política Completa",
        "policy_content": "**POLÍTICA DE PRIVACIDAD**\nResponsable: HausMate (info@haus-es.com).\nFinalidad: Gestión de perfiles y Matching.\nDerechos: Acceso, rectificación y supresión enviando correo a info@haus-es.com."
    },
    "English": {
        "title": "📝 Find your HausMate",
        "name": "Full Name *", "wa": "WhatsApp (with +) *", "age": "Age",
        "gender": "Your gender", "lw": "Living preference", "budget": "Max Budget (€)",
        "rooms": "Rooms", "country": "Country of origin",
        "idioma_form": "Main language", "zonas": "📍 Preferred areas",
        "zonas_help": "Select districts", "move_in": "Move-in date",
        "move_out": "Move-out date", "notes": "About you (work, hobbies...)",
        "btn": "REGISTER & FIND MATCH!", 
        "error": "⚠️ Required: Name, WhatsApp, and legal boxes.",
        "success": "✅ Data saved successfully.", "loading": "Processing...",
        "generic_error": "❌ Error processing registration. Try again later.",
        "legal_header": "⚖️ Legal Information & Privacy",
        "legal_opt1": "I accept the Privacy Policy. *",
        "legal_opt2": "I authorize sharing my profile with matches. *",
        "legal_opt3": "I agree to be contacted via WhatsApp. *",
        "view_policy": "View Full Policy",
        "policy_content": "Please refer to the Spanish version for the official text."
    }
}
t = texts[lang]

# --- CABECERA CON LOGO ---
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 4, 1])
with col_logo_2:
    logo_url = "https://raw.githubusercontent.com/chechoderiquer-dev/hausmate_match/main/logo_hausmate.png"
    st.image(logo_url, width=220)

# --- FUNCIÓN DB SEGURA ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        from supabase import create_client
        # Limpieza de secretos y conexión
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        
        supabase = create_client(url, key)
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        # LOG INTERNO (no se muestra al usuario por seguridad)
        print(f"DEBUG ERROR: {str(e)}")
        return False, "database_error"

# --- FORMULARIO ---
st.markdown('<div class="haus-card">', unsafe_allow_html=True)
with st.form("main_form", border=False):
    st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{t['title']}</h3>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        # MEJORA: max_chars para evitar ataques de desbordamiento
        fn = st.text_input(t["name"], placeholder="Ej: John Doe", max_chars=100)
        wa = st.text_input(t["wa"], placeholder="+34 600 000 000", max_chars=20)
        age_val = st.number_input(t["age"], 18, 99, 25)
        user_gender = st.selectbox(t["gender"], ["Mujer", "Hombre", "Otro"])
    
    with c2:
        bg = st.number_input(t["budget"], 0, 5000, 800, step=50)
        rm = st.selectbox(t["rooms"], ["1", "2", "3", "4", "5+"])
        pref_gender = st.selectbox(t["lw"], ["Mixto", "Solo Mujeres", "Solo Hombres"])
        country = st.text_input(t["country"], "España" if lang == "Español" else "Spain", max_chars=50)

    idioma_val = st.selectbox(t["idioma_form"], ["Spanish", "English", "French", "German", "Other"])

    st.write(t["zonas"])
    distritos = ["Centro", "Arganzuela", "Retiro", "Salamanca", "Chamartín", "Tetuán", "Chamberí", "Fuencarral-El Pardo", "Moncloa-Aravaca", "Latina", "Carabanchel", "Usera", "Puente de Vallecas", "Moratalaz", "Ciudad Lineal", "Hortaleza", "Villaverde", "Villa de Vallecas", "Vicálvaro", "San Blas-Canillejas", "Barajas", "Otros"]
    barrios_sel = st.multiselect(t["zonas_help"], options=distritos, label_visibility="collapsed")
    
    c3, c4 = st.columns(2)
    with c3:
        m_in = st.date_input(t["move_in"], dt.date.today())
    with c4:
        m_out = st.date_input(t["move_out"], dt.date.today() + dt.timedelta(days=180))
        
    notes_content = st.text_area(t["notes"], placeholder="Cuéntanos un poco sobre ti...", max_chars=1000)
    
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
    st_folium(m, height=200, use_container_width=True, key="madrid_map")
    
    st.markdown("---")
    st.markdown(f"**{t['legal_header']}**")
    
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

        extended_notes = f"LOG LEGAL {POLICY_VERSION} | {now_utc.isoformat()} | Pais: {country} | Consentimiento: OK"

        payload = {
            "nombre": fn.strip()[:100],
            "telefono": clean_wa[:15],
            "telefono_raw": wa.strip()[:25],
            "dedupe_key": dedupe_key,
            "budget": int(bg),
            "habitaciones": rm,
            "pref_genero": pref_gender, 
            "edad": int(age_val),       
            "genero": user_gender,      
            "zona": ", ".join(barrios_sel) if barrios_sel else "Sin especificar",
            "inicio": m_in.isoformat(),
            "fin": m_out.isoformat(),
            "idioma": idioma_val,       
            "Perfil": notes_content.strip()[:1000],
            "notas": extended_notes,
            "created_at": now_utc.isoformat()
        }
        
        with st.spinner(t["loading"]):
            exito, error_code = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success(t["success"])
            else:
                if error_code == "database_error":
                    st.error(t["generic_error"])
                else:
                    st.warning("⚠️ Ya recibimos tu solicitud hoy.")
