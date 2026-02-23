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

    /* Estilo para los checkbox legales */
    .legal-text {
        font-size: 0.85rem;
        color: #555;
        line-height: 1.2;
    }

    /* Ocultar elementos innecesarios */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

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
        "error": "⚠️ Requerido: Nombre, WhatsApp y aceptar términos legales.",
        "success": "✅ ¡Datos guardados con éxito!", "loading": "Guardando datos...",
        "legal_header": "⚖️ Información Legal y Privacidad",
        "legal_notice": "Responsable: HausMate. Finalidad: Gestionar tu solicitud y realizar el 'match' con otros usuarios. Derechos: Acceso, supresión y portabilidad.",
        "legal_opt1": "He leído y acepto la Política de Privacidad y el tratamiento de mis datos para el servicio. *",
        "legal_opt2": "Autorizo expresamente a compartir mi contacto y perfil con otros usuarios que coincidan en el 'match'. *",
        "legal_opt3": "Acepto ser contactado por WhatsApp para la gestión del servicio.",
        "view_policy": "Leer Política de Privacidad completa",
        "policy_content": """
        **POLÍTICA DE PRIVACIDAD Y CONSENTIMIENTO DE TRATAMIENTO**
        
        **Responsable del Tratamiento:** El responsable de los datos recogidos en esta encuesta es HausMate. Para cualquier consulta o ejercicio de derechos, puede dirigirse a nuestro Delegado de Protección de Datos a través del correo electrónico: info@haus-es.com.
        
        **Finalidad del Tratamiento:** Los datos de carácter personal recabados (nombre, preferencias de vivienda y datos de contacto) se utilizarán exclusivamente para gestionar su perfil de búsqueda, analizar la compatibilidad con otros usuarios y facilitar la conexión ("Matching") entre las partes interesadas.
        
        **Base Jurídica (Legitimación):** El tratamiento se basa en el consentimiento libre, específico, informado e inequívoco del usuario (Art. 6.1.a RGPD) manifestado mediante la marcación de las casillas de aceptación.
        
        **Cesión y Comunicación de Datos:** En cumplimiento del principio de minimización, sus datos de contacto (Nombre y WhatsApp) solo serán compartidos con aquellos usuarios con los que el sistema genere un "match" positivo y aceptado. Fuera de este supuesto, no se cederán datos a terceros ni se realizarán transferencias internacionales, salvo requerimiento judicial o administrativo.
        
        **Plazo de Conservación:** Los datos se conservarán mientras se mantenga la relación para la prestación del servicio de matching o hasta que el usuario revoque su consentimiento. Una vez finalizada la finalidad, los datos serán bloqueados y posteriormente eliminados conforme a la normativa vigente.
        
        **Derechos del Usuario:** Usted tiene derecho a retirar su consentimiento en cualquier momento. Puede ejercer sus derechos de acceso, rectificación, supresión ("derecho al olvido"), limitación del tratamiento, portabilidad y oposición enviando un correo electrónico a info@haus-es.com. Asimismo, se le informa de su derecho a presentar una reclamación ante la Agencia Española de Protección de Datos (AEPD) si considera vulnerados sus derechos.
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
        "error": "⚠️ Required: Name, WhatsApp, and legal consent.",
        "success": "✅ Data saved successfully.", "loading": "Saving data...",
        "legal_header": "⚖️ Legal Information & Privacy",
        "legal_notice": "Data Controller: HausMate. Purpose: Manage your request and perform matching with other users. Rights: Access, deletion, and portability.",
        "legal_opt1": "I have read and accept the Privacy Policy and data processing for the service. *",
        "legal_opt2": "I expressly authorize sharing my contact and profile with other matching users. *",
        "legal_opt3": "I agree to be contacted via WhatsApp for service management.",
        "view_policy": "Read full Privacy Policy",
        "policy_content": """
        **PRIVACY POLICY AND TREATMENT CONSENT**
        
        **Data Controller:** The controller for the data collected in this survey is HausMate. For any queries or to exercise your rights, you can contact our Data Protection Officer via email: info@haus-es.com.
        
        **Purpose of Treatment:** The personal data collected (name, housing preferences, and contact details) will be used exclusively to manage your search profile, analyze compatibility with other users, and facilitate the connection ("Matching") between interested parties.
        
        **Legal Basis (Legitimation):** The treatment is based on the free, specific, informed, and unambiguous consent of the user (Art. 6.1.a GDPR) expressed by checking the acceptance boxes.
        
        **Data Transfer and Communication:** In compliance with the principle of minimization, your contact details (Name and WhatsApp) will only be shared with those users where the system generates a positive and accepted "match". Otherwise, no data will be transferred to third parties or international transfers will be made, except for judicial or administrative requirements.
        
        **Retention Period:** Data will be kept as long as the relationship for the provision of the matching service is maintained or until the user revokes their consent. Once the purpose has ended, the data will be blocked and subsequently deleted in accordance with current regulations.
        
        **User Rights:** You have the right to withdraw your consent at any time. You can exercise your rights of access, rectification, deletion ("right to be forgotten"), limitation of treatment, portability, and opposition by sending an email to info@haus-es.com. You are also informed of your right to file a claim with the Spanish Data Protection Agency (AEPD) if you consider your rights to have been violated.
        """
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
    distritos = [
        "Centro", "Arganzuela", "Retiro", "Salamanca", "Chamartín", 
        "Tetuán", "Chamberí", "Fuencarral-El Pardo", "Moncloa-Aravaca", 
        "Latina", "Carabanchel", "Usera", "Puente de Vallecas", 
        "Moratalaz", "Ciudad Lineal", "Hortaleza", "Villaverde", 
        "Villa de Vallecas", "Vicálvaro", "San Blas-Canillejas", "Barajas",
        "Otros"
    ]
    barrios_sel = st.multiselect(t["zonas_help"], options=distritos, label_visibility="collapsed")
    
    c3, c4 = st.columns(2)
    with c3:
        m_in = st.date_input(t["move_in"], dt.date.today())
    with c4:
        m_out = st.date_input(t["move_out"], dt.date.today() + dt.timedelta(days=180))
        
    notes_content = st.text_area(t["notes"], placeholder="..." )
    
    # Mapa decorativo
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=12, tiles="cartodbpositron")
    st_folium(m, height=180, use_container_width=True, key="madrid_map")
    
    st.markdown("---")
    # --- SECCIÓN LEGAL ---
    st.markdown(f"**{t['legal_header']}**")
    st.caption(t['legal_notice'])
    
    check_privacy = st.checkbox(t['legal_opt1'])
    check_share = st.checkbox(t['legal_opt2'])
    check_whatsapp = st.checkbox(t['legal_opt3'])
    
    # Desplegable con la política completa (Segunda Capa de Información)
    with st.expander(t['view_policy']):
        st.markdown(t['policy_content'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    enviar = st.form_submit_button(t["btn"])
st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE ENVÍO ---
if enviar:
    if not fn or not wa or not check_privacy or not check_share:
        st.error(t["error"])
    else:
        clean_wa = "".join(filter(str.isdigit, wa))
        dedupe_key = hashlib.md5(f"{clean_wa}_{dt.datetime.now().date()}".encode()).hexdigest()

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
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner(t["loading"]):
            exito, error_msg = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success(t["success"])
            else:
                if "duplicate key" in error_msg.lower():
                    st.warning("⚠️ Ya hemos recibido una solicitud de este número hoy.")
                else:
                    st.error(f"Error técnico: {error_msg}")
