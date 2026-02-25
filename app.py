import os
import datetime as dt
import hashlib
from typing import Dict,Any
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HausMate Match",page_icon="🏠",layout="centered")

st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#7FBBC2 0%,#D9F1F3 60%,#ffffff 100%);}
.block-container{padding-top:1.5rem!important;padding-left:1rem!important;padding-right:1rem!important;max-width:800px!important;}
.haus-card{background:white;padding:1.5rem;border-radius:20px;box-shadow:0 10px 25px rgba(0,0,0,0.1);margin-top:10px;color:#0C2D33;width:100%;box-sizing:border-box;}
@media(min-width:768px){.haus-card{padding:2.5rem;}}
div.stButton>button:first-child{width:100%;background-color:#0C2D33!important;color:white!important;font-weight:bold;border-radius:12px;height:3.8em;border:none;transition:all 0.3s ease;font-size:16px;}
div.stButton>button:first-child:hover{background-color:#164a54!important;transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,0.2);}
div.stButton>button:first-child:active{transform:translateY(0);}
[data-testid="stImage"] img{max-width:100%;height:auto;}
[data-testid="stImage"]{display:flex;justify-content:center;margin-bottom:5px;}
#MainMenu,footer,header{visibility:hidden;}
input,select,textarea{font-size:16px!important;}
</style>
""",unsafe_allow_html=True)

POLICY_VERSION="v1.1-2024-05-24"

col_l,col_r=st.columns([3,1])
with col_r:
    lang=st.radio("Lang",["Español","English"],horizontal=True,label_visibility="collapsed")

texts={
"Español":{
"title":"📝 Encuentra tu HausMate",
"name":"Nombre completo *","wa":"WhatsApp (+34) *","age":"Edad",
"gender":"Tu género","lw":"Preferencia de convivencia","budget":"Presupuesto Máximo (€)",
"rooms":"Habitaciones","country":"País de origen",
"idioma_form":"Idioma principal","zonas":"📍 Zonas preferidas",
"zonas_help":"Selecciona los distritos","move_in":"¿Cuándo entras?",
"move_out":"¿Hasta cuándo?","notes":"Sobre ti (trabajo, hobbies...)",
"btn":"¡REGISTRARME Y BUSCAR MATCH!",
"error":"⚠️ Requerido: Nombre, WhatsApp y aceptar las casillas legales.",
"success":"✅ ¡Datos guardados con éxito!","loading":"Procesando registro...",
"legal_header":"⚖️ Información Legal y Privacidad",
"legal_opt1":"Acepto la Política de Privacidad. *",
"legal_opt2":"Autorizo compartir mi perfil con otros matches. *",
"legal_opt3":"Acepto contacto por WhatsApp. *",
"view_policy":"Ver Política Completa",
"policy_content":"""
POLÍTICA DE PRIVACIDAD, CONSENTIMIENTO EXPRESO Y AUTORIZACIÓN DE CESIÓN DE DATOS

Responsable del tratamiento:
HausMate
Email de contacto: info@haus-es.com

Normativa aplicable:
Este tratamiento de datos se realiza en cumplimiento de:

• Reglamento (UE) 2016/679 (Reglamento General de Protección de Datos — RGPD)
• Ley Orgánica 3/2018 de Protección de Datos Personales y Garantía de los Derechos Digitales (LOPDGDD)
• Ley 34/2002 de Servicios de la Sociedad de la Información (LSSI-CE), cuando aplique

1. Datos personales recopilados

Al completar este formulario, el usuario proporciona voluntaria y expresamente los siguientes datos personales:

• Nombre completo  
• Número de teléfono y WhatsApp  
• Edad  
• Género  
• País de origen  
• Idioma  
• Preferencias de convivencia  
• Preferencias de ubicación  
• Presupuesto  
• Fechas de entrada y salida  
• Información personal incluida en la descripción del perfil  
• Cualquier otra información facilitada voluntariamente  

Estos datos constituyen datos personales conforme al artículo 4 del RGPD.

2. Finalidad del tratamiento

El usuario autoriza expresamente a HausMate a tratar sus datos personales con las siguientes finalidades:

• Crear su perfil dentro de la plataforma HausMate  
• Analizar compatibilidad con otros usuarios  
• Realizar procesos de matching entre usuarios compatibles  
• Contactar al usuario mediante WhatsApp, teléfono o medios electrónicos  
• Compartir su perfil con otros usuarios potencialmente compatibles  
• Facilitar el contacto directo entre usuarios compatibles  
• Mejorar el servicio y optimizar los algoritmos de matching  

3. Cesión y comunicación de datos a terceros usuarios

El usuario autoriza de forma expresa, informada, específica e inequívoca que HausMate pueda compartir sus datos personales con otros usuarios registrados que sean identificados como potencialmente compatibles.

Esta información puede incluir:

• Nombre  
• Edad  
• Preferencias  
• Descripción personal  
• Número de WhatsApp o teléfono  
• Información del perfil  

La finalidad exclusiva de esta cesión es facilitar el contacto entre usuarios compatibles.

HausMate no venderá los datos a terceros externos.

4. Base jurídica del tratamiento

La base legal del tratamiento es el consentimiento explícito del usuario conforme al artículo 6.1.a del RGPD.

Este consentimiento se otorga mediante la aceptación activa de las casillas correspondientes.

El consentimiento puede retirarse en cualquier momento.

5. Conservación de los datos

Los datos serán conservados durante un máximo de 24 meses desde su registro, salvo que el usuario solicite su eliminación antes.

6. Transferencias internacionales

HausMate utiliza Supabase como proveedor tecnológico, el cual actúa como Encargado del Tratamiento conforme al artículo 28 del Reglamento (UE) 2016/679 (RGPD). Los datos se almacenan en servidores seguros ubicados dentro de la Unión Europea (Irlanda), garantizando el cumplimiento de la normativa europea de protección de datos.

7. Derechos del usuario

El usuario puede ejercer en cualquier momento sus derechos de:

• Acceso  
• Rectificación  
• Supresión (derecho al olvido)  
• Limitación del tratamiento  
• Oposición  
• Portabilidad  

Enviando una solicitud a:

info@haus-es.com

8. Consentimiento explícito y aceptación

Al aceptar las casillas correspondientes, el usuario declara que:

• Ha leído y comprendido esta política
• Autoriza expresamente el tratamiento de sus datos
• Autoriza el contacto vía WhatsApp, teléfono o medios electrónicos
• Autoriza la cesión de sus datos a otros usuarios compatibles
• Comprende que el objetivo es facilitar procesos de matching

Este consentimiento constituye una base legal válida conforme al RGPD.

Fecha de última actualización: 2026
"""
},
"English":{
"title":"📝 Find your HausMate",
"name":"Full Name *","wa":"WhatsApp (with +) *","age":"Age",
"gender":"Your gender","lw":"Living preference","budget":"Max Budget (€)",
"rooms":"Rooms","country":"Country of origin",
"idioma_form":"Main language","zonas":"📍 Preferred areas",
"zonas_help":"Select districts","move_in":"Move-in date",
"move_out":"Move-out date","notes":"About you (work, hobbies...)",
"btn":"REGISTER & FIND MATCH!",
"error":"⚠️ Required: Name, WhatsApp, and legal boxes.",
"success":"✅ Data saved successfully.","loading":"Processing...",
"legal_header":"⚖️ Legal Information & Privacy",
"legal_opt1":"I accept the Privacy Policy. *",
"legal_opt2":"I authorize sharing my profile with matches. *",
"legal_opt3":"I agree to be contacted via WhatsApp. *",
"view_policy":"View Full Policy",
"policy_content":"""
PRIVACY POLICY, EXPLICIT CONSENT AND DATA SHARING AUTHORIZATION

Data Controller:
HausMate
Contact email: info@haus-es.com

Applicable regulations:

This data processing complies with:

• Regulation (EU) 2016/679 (General Data Protection Regulation — GDPR)
• Spanish Organic Law 3/2018 on Data Protection (LOPDGDD)
• Information Society Services Law (LSSI-CE), when applicable

1. Personal data collected

By completing this form, the user voluntarily and explicitly provides the following personal data:

• Full name  
• Phone number and WhatsApp  
• Age  
• Gender  
• Country of origin  
• Language  
• Living preferences  
• Location preferences  
• Budget  
• Move-in and move-out dates  
• Personal description  
• Any additional voluntarily provided information  

These constitute personal data under Article 4 of the GDPR.

2. Purpose of processing

The user explicitly authorizes HausMate to process their data for the following purposes:

• Creating their HausMate profile  
• Performing compatibility analysis  
• Matching users with compatible roommates  
• Contacting the user via WhatsApp, phone, or electronic means  
• Sharing their profile with potentially compatible users  
• Facilitating direct communication between users  
• Improving the matching service  

3. Data sharing with other users

The user expressly authorizes HausMate to share their personal data with other registered users when compatibility is identified.

This may include:

• Name  
• Age  
• Preferences  
• Profile description  
• WhatsApp or phone number  
• Profile information  

This sharing is strictly limited to roommate matching purposes.

HausMate does not sell personal data to external third parties.

4. Legal basis

The legal basis for processing is the user's explicit consent under Article 6.1.a of the GDPR.

Consent is granted by actively selecting the required checkboxes.

Consent may be withdrawn at any time.

5. Data retention

Data will be stored for a maximum period of 24 months unless deletion is requested earlier.

6. International transfers

HausMate uses Supabase as a technology provider, acting as a Data Processor under Article 28 GDPR. Data is stored on secure servers located within the European Union (Ireland), ensuring compliance with EU data protection laws.

7. User rights

Users may exercise their rights of:

• Access  
• Rectification  
• Erasure  
• Restriction  
• Objection  
• Portability  

by contacting:

info@haus-es.com

8. Explicit consent and acceptance

By accepting the required checkboxes, the user confirms that they:

• Have read and understood this policy  
• Explicitly consent to the processing of their personal data  
• Authorize contact via WhatsApp, phone, or electronic means  
• Authorize the sharing of their data with compatible users  
• Understand the purpose is to facilitate roommate matching  

This consent constitutes a valid legal basis under GDPR.

Last updated: 2026
"""
}}
t=texts[lang]

col_logo_1,col_logo_2,col_logo_3=st.columns([1,4,1])
with col_logo_2:
    logo_url="https://raw.githubusercontent.com/chechoderiquer-dev/hausmate_match/main/logo_hausmate.png"
    try:
        st.image(logo_url,width=220)
    except:
        st.markdown("<h1 style='text-align: center; color: #0C2D33;'>HAUSMATE</h1>",unsafe_allow_html=True)

def save_to_supabase(data:Dict[str,Any]):
    try:
        from supabase import create_client
        url=st.secrets["SUPABASE_URL"].strip().replace('"','')
        key=st.secrets["SUPABASE_ANON_KEY"].strip().replace('"','')
        table=st.secrets["SUPABASE_TABLE"].strip().replace('"','')
        supabase=create_client(url,key)
        supabase.table(table).insert(data).execute()
        return True,""
    except Exception as e:
        return False,str(e)

st.markdown('<div class="haus-card">',unsafe_allow_html=True)
with st.form("main_form",border=False):
    st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>{t['title']}</h3>",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        fn=st.text_input(t["name"],placeholder="Ej: John Doe")
        wa=st.text_input(t["wa"],placeholder="+34 600 000 000")
        age_val=st.number_input(t["age"],18,99,25)
        user_gender=st.selectbox(t["gender"],["Mujer","Hombre","Otro"])
    with c2:
        bg=st.number_input(t["budget"],0,5000,800,step=50)
        rm=st.selectbox(t["rooms"],["1","2","3","4","5+"])
        pref_gender=st.selectbox(t["lw"],["Mixto","Solo Mujeres","Solo Hombres"])
        country=st.text_input(t["country"],"España" if lang=="Español" else "Spain")

    idioma_val=st.selectbox(t["idioma_form"],["Spanish","English","French","German","Other"])

    st.write(t["zonas"])
    distritos=["Centro","Arganzuela","Retiro","Salamanca","Chamartín","Tetuán","Chamberí","Fuencarral-El Pardo","Moncloa-Aravaca","Latina","Carabanchel","Usera","Puente de Vallecas","Moratalaz","Ciudad Lineal","Hortaleza","Villaverde","Villa de Vallecas","Vicálvaro","San Blas-Canillejas","Barajas","Otros"]
    barrios_sel=st.multiselect(t["zonas_help"],options=distritos,label_visibility="collapsed")

    c3,c4=st.columns(2)
    with c3:
        m_in=st.date_input(t["move_in"],dt.date.today())
    with c4:
        m_out=st.date_input(t["move_out"],dt.date.today()+dt.timedelta(days=180))

    notes_content=st.text_area(t["notes"],placeholder="Cuéntanos un poco sobre ti...")

    m=folium.Map(location=[40.4168,-3.7038],zoom_start=11,tiles="cartodbpositron")
    st_folium(m,height=200,use_container_width=True,key="madrid_map")

    st.markdown("---")
    st.markdown(f"**{t['legal_header']}**")

    check_privacy=st.checkbox(t['legal_opt1'])
    check_share=st.checkbox(t['legal_opt2'])
    check_whatsapp=st.checkbox(t['legal_opt3'])

    with st.expander(t['view_policy']):
        st.markdown(t['policy_content'])

    st.markdown("<br>",unsafe_allow_html=True)
    enviar=st.form_submit_button(t["btn"])
st.markdown('</div>',unsafe_allow_html=True)

if enviar:
    if not fn or not wa or not check_privacy or not check_share or not check_whatsapp:
        st.error(t["error"])
    else:
        now_utc=dt.datetime.now(dt.timezone.utc)
        clean_wa="".join(filter(str.isdigit,wa))
        dedupe_key=hashlib.md5(f"{clean_wa}_{now_utc.date()}".encode()).hexdigest()
        extended_notes=f"LOG LEGAL {POLICY_VERSION} | {now_utc.isoformat()} | Pais: {country} | Consentimiento: OK"
        payload={
            "nombre":fn,
            "telefono":wa,
            "telefono_raw":wa,
            "dedupe_key":dedupe_key,
            "budget":int(bg),
            "habitaciones":rm,
            "pref_genero":pref_gender,
            "edad":int(age_val),
            "genero":user_gender,
            "zona":", ".join(barrios_sel) if barrios_sel else "Sin especificar",
            "inicio":m_in.isoformat(),
            "fin":m_out.isoformat(),
            "idioma":idioma_val,
            "Perfil":notes_content,
            "notas":extended_notes,
            "created_at":now_utc.isoformat(),
            "policy_version":POLICY_VERSION,
            "consent_timestamp":now_utc.isoformat(),
            "consent_language":lang,
            "consent_privacy":check_privacy,
            "consent_share":check_share,
            "consent_whatsapp":check_whatsapp
        }

        with st.spinner(t["loading"]):
            exito,error_msg=save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success(t["success"])
            else:
                if "duplicate key" in error_msg.lower():
                    st.warning("⚠️ Ya recibimos tu solicitud hoy.")
                else:
                    st.error(f"Error: {error_msg}")
