import streamlit as st
import datetime as dt
from supabase import create_client

# Configuración de página
st.set_page_config(page_title="HausMate Match", page_icon="🏠")

# Función para guardar datos
def save_to_supabase(data):
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
        supabase = create_client(url, key)
        # Intentamos insertar en la tabla definida en secrets
        supabase.table(st.secrets["SUPABASE_TABLE"]).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# Interfaz
st.title("🏠 Registro HausMate")
st.write("Completa tus datos para encontrar match.")

with st.form("form_registro"):
    nombre = st.text_input("Nombre completo")
    telefono = st.text_input("WhatsApp")
    presupuesto = st.number_input("Presupuesto (€)", value=800)
    enviar = st.form_submit_button("REGISTRARME")

if enviar:
    if nombre and telefono:
        payload = {
            "nombre": nombre,
            "telefono": telefono,
            "budget": presupuesto,
            "created_at": dt.datetime.now().isoformat()
        }
        success, error_msg = save_to_supabase(payload)
        if success:
            st.success("✅ ¡Datos guardados correctamente!")
        else:
            st.error(f"Error de conexión: {error_msg}")
            st.info("💡 Consejo: Revisa si el nombre de la tabla en Supabase es 'usuarios' o tiene otro nombre.")
    else:
        st.warning("Rellena los campos obligatorios.")
