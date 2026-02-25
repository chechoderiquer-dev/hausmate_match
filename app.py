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
    /* 1. Fondo degradado */
    .stApp { 
        background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); 
    }
    
    /* 2. Ajustes de contenedor principal */
    .block-container { 
        padding-top: 1.5rem !important; 
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 800px !important; 
    }
    
    /* 3. Tarjeta adaptable (Responsive Card) */
    .haus-card { 
        background: white; 
        padding: 1.5rem; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        margin-top: 10px;
        color: #0C2D33;
        width: 100%;
        box-sizing: border-box;
    }

    /* Ajuste para pantallas grandes */
    @media (min-width: 768px) {
        .haus-card {
            padding: 2.5rem;
        }
    }
    
    /* 4. Botón con feedback táctil y visual */
    div.stButton > button:first-child {
        width: 100%;
        background-color: #0C2D33 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 12px;
        height: 3.8em;
        border: none;
        transition: all 0.3s ease;
        font-size: 16px;
    }
    div.stButton > button:first-child:hover {
        background-color: #164a54 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    div.stButton > button:first-child:active {
        transform: translateY(0);
    }

    /* 5. Asegurar que las imágenes no se desborden */
    [data-testid="stImage"] img {
        max-width: 100%;
        height: auto;
    }

    /* Forzar centrado del logo */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin-bottom: 5px;
    }

    /* Ocultar elementos de Streamlit para look App nativa */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Ajuste de inputs para móviles (más espacio para tocar) */
    input, select, textarea {
        font-size: 16px !important; /* Evita zoom automático en iOS */
    }
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
        "legal_header": "⚖️ Información Legal y Privacidad",
        "legal_opt1": "Acepto la Política de Privacidad. *",
        "legal_opt2": "Autorizo compartir mi perfil con otros matches. *",
        "legal_opt3": "Acepto contacto por WhatsApp. *",
        "view_policy": "Ver Política Completa",
        "policy_content": """
**POLÍTICA DE PRIVACIDAD**
Responsable: HausMate (info@haus-es.com).
Finalidad: Gestión de perfiles y Matching.
Legitimación: Consentimiento del usuario.
Derechos: Acceso, rectificación y supresión enviando correo a info@haus-es.com.
        """
    },
    "English": {
        "title": "
