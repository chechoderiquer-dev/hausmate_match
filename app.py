import streamlit as st
import datetime as dt
from supabase import create_client

# 1. Configuración de página
st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# 2. Estilo Visual (Fondo y tarjetas)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    .haus-card { 
        background: white; padding: 2rem; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); color: #0C2D33; 
    }
    div.stButton > button:first-child {
        width: 100%; background-color: #0C2D33 !important; color: white !important;
        font-weight: bold; border-radius: 12px; height: 3.5em; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Función de conexión a Supabase
def save_to_supabase(data):
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
        table_name = st.secrets["SUPABASE_TABLE"]
        supabase = create_client(url, key)
        supabase.table(table_name).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# 4. Interfaz del Formulario
st.image("https://raw.githubusercontent.com/chechoderiquer-dev/hausmate_match/main/logo_hausmate.png", width=200)

st.markdown('<div class="haus-card">', unsafe_allow_html=True)
st.subheader("📝 Encuentra tu HausMate")

with st.form("main_form", border=False):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre completo *")
        whatsapp = st.text_input("WhatsApp *")
        edad = st.number_input("Edad", 18, 99, 25)
    with col2:
        presupuesto = st.number_input("Presupuesto Máximo (€)", value=800)
        habitaciones = st.selectbox("Habitaciones", ["1", "2", "3", "4+"])
        preferencia = st.selectbox("Preferencia", ["Mixto", "Solo Mujeres", "Solo Hombres"])
    
    zonas = st.multiselect("📍 Zonas preferidas", ["Centro", "Chamberí", "Salamanca", "Tetuán", "Otros"])
    perfil = st.text_area("Sobre ti (trabajo, hobbies, etc.)")
    
    st.markdown("---")
    c1 = st.checkbox("Acepto la Política de Privacidad *")
    c2 = st.checkbox("Autorizo compartir mi perfil *")
    
    submit = st.form_submit_button("¡REGISTRARME Y BUSCAR MATCH!")
st.markdown('</div>', unsafe_allow_html=True)

# 5. Lógica de guardado
if submit:
    if not nombre or not whatsapp or not c1:
        st.error("⚠️ Rellena los campos obligatorios.")
    else:
        # Los nombres de las llaves deben coincidir con tu tabla en image_168703.png
        payload = {
            "full_name": nombre,
            "whatsapp": whatsapp,
            "age": int(edad),
            "budget": int(presupuesto),
            "rooms": habitaciones,
            "living_with": preferencia,
            "barrios": zonas,
            "notes": perfil,
            "created_at": dt.datetime.now().isoformat()
        }
        
        with st.spinner("Conectando con HausMate..."):
            success, error_msg = save_to_supabase(payload)
            if success:
                st.balloons()
                st.success("✅ ¡Registro completado! Te contactaremos pronto.")
            else:
                st.error(f"Error: {error_msg}")
