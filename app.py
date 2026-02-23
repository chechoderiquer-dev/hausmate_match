import os
import io
import json
import zipfile
import datetime as dt
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import requests

import folium
from folium.features import GeoJson, GeoJsonTooltip
from streamlit_folium import st_folium

# geopandas stack (ya lo tienes en requirements)
import geopandas as gpd


# =========================
# BRAND / UI
# =========================
APP_NAME = "HausMate Match"
LOGO_PATH_LOCAL = "logo.png"  # opcional (si lo subes al repo)
LOGO_PATH_FALLBACK = None     # si no existe, igual corre

# Colores aproximados del logo (fondo turquesa + blanco)
BRAND_BG = "#7FBBC2"
BRAND_BG_2 = "#D9F1F3"
BRAND_DARK = "#0C2D33"
BRAND_ACCENT = "#B06CFF"  # acento moradito como tu UI (puedes cambiar)
WHITE = "#FFFFFF"


def brand_css():
    st.markdown(
        f"""
        <style>
          .stApp {{
            background: linear-gradient(180deg, {BRAND_BG} 0%, {BRAND_BG_2} 60%, #ffffff 100%);
          }}
          .block-container {{
            padding-top: 2rem;
          }}
          h1, h2, h3, h4, h5, h6, p, label, div {{
            color: {BRAND_DARK};
          }}
          .haus-card {{
            background: rgba(255,255,255,0.85);
            border: 1px solid rgba(12,45,51,0.12);
            border-radius: 18px;
            padding: 16px 16px;
            box-shadow: 0 6px 18px rgba(12,45,51,0.10);
          }}
          .haus-badge {{
            display:inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.7);
            border: 1px solid rgba(12,45,51,0.12);
            font-weight: 600;
          }}
          .stButton > button {{
            background: {BRAND_DARK};
            color: {WHITE};
            border-radius: 12px;
            border: 0;
            padding: 10px 14px;
          }}
          .stButton > button:hover {{
            filter: brightness(1.05);
          }}
          .danger {{
            background: rgba(255, 0, 0, 0.08);
            border: 1px solid rgba(255, 0, 0, 0.18);
            padding: 10px 12px;
            border-radius: 12px;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    col1, col2 = st.columns([1, 3], vertical_alignment="center")
    with col1:
        # Intenta cargar logo local si existe
        if os.path.exists(LOGO_PATH_LOCAL):
            st.image(LOGO_PATH_LOCAL, use_container_width=True)
        else:
            st.markdown(f"<div class='haus-badge'>🏠 {APP_NAME}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h2 style='margin-bottom:0'>{APP_NAME}</h2>", unsafe_allow_html=True)
        st.markdown(
            "<div class='haus-badge'>Encuesta inteligente para encontrar tu match de piso / roomie</div>",
            unsafe_allow_html=True,
        )


# =========================
# SUPABASE
# =========================
def get_secret(name: str, default: str = "") -> str:
    # Streamlit Cloud secrets -> st.secrets
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    # fallback env
    return os.getenv(name, default)


def get_supabase_client():
    """
    Usa service role key (server-side) para insertar sin exponer políticas.
    """
    supabase_url = get_secret("SUPABASE_URL", "").strip()
    supabase_key = get_secret("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not supabase_url or not supabase_key:
        return None, "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en Secrets."

    # Validación simple para evitar el error DNS típico por URL mal copiada
    if "supabase.co" not in supabase_url:
        return None, f"SUPABASE_URL no parece válida: {supabase_url}"

    try:
        from supabase import create_client  # pip install supabase
    except Exception:
        return None, "No está instalada la librería 'supabase'. Agrega 'supabase' a requirements.txt."

    try:
        client = create_client(supabase_url, supabase_key)
        return client, ""
    except Exception as e:
        return None, f"No pude inicializar Supabase: {e}"


def save_to_supabase(payload: Dict[str, Any]) -> (bool, str):
    table = get_secret("SUPABASE_TABLE", "hausmate_leads").strip()

    client, err = get_supabase_client()
    if client is None:
        return False, err

    try:
        client.table(table).insert(payload).execute()
        return True, ""
    except Exception as e:
        return False, str(e)


def admin_password_ok() -> bool:
    admin_pw = get_secret("ADMIN_PASSWORD", "").strip()
    if not admin_pw:
        return False
    if st.session_state.get("admin_ok") is True:
        return True
    return False


# =========================
# MADRID BARRIOS MAP (auto-download official SHP)
# =========================
BARRIOS_SHP_ZIP_URL = "https://geoportal.madrid.es/fsdescargas/IDEAM_WBGEOPORTAL/LIMITES_ADMINISTRATIVOS/Barrios/Barrios.zip"

@st.cache_data(show_spinner=True)
def load_barrios_geodata() -> gpd.GeoDataFrame:
    """
    Descarga el SHP oficial de Barrios (Ayuntamiento de Madrid), lo lee con GeoPandas,
    lo reproyecta a WGS84 y devuelve un GeoDataFrame listo para Folium.
    """
    r = requests.get(BARRIOS_SHP_ZIP_URL, timeout=60)
    r.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(r.content))
    # Extraer en memoria a /tmp
    extract_dir = "/tmp/madrid_barrios_shp"
    os.makedirs(extract_dir, exist_ok=True)
    z.extractall(extract_dir)

    # Encontrar el .shp
    shp_path = None
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f.lower().endswith(".shp"):
                shp_path = os.path.join(root, f)
                break
        if shp_path:
            break
    if not shp_path:
        raise RuntimeError("No encontré un archivo .shp dentro del zip de Barrios.")

    gdf = gpd.read_file(shp_path)

    # Reproyectar a WGS84
    if gdf.crs is None:
        # Según metadato es EPSG:25830 normalmente, pero si viene sin CRS, intentamos asignarlo
        gdf = gdf.set_crs(epsg=25830, allow_override=True)
    gdf = gdf.to_crs(epsg=4326)

    # Normalizar columna de nombre barrio (según dataset suele tener NOMBRE / BARRIO / etc.)
    cols_lower = {c.lower(): c for c in gdf.columns}
    name_col = None
    for candidate in ["barrio", "nombre", "nom_barrio", "distrito", "barrios"]:
        if candidate in cols_lower:
            name_col = cols_lower[candidate]
            break
    if name_col is None:
        # si no, toma la primera columna tipo object
        obj_cols = [c for c in gdf.columns if gdf[c].dtype == "object"]
        if obj_cols:
            name_col = obj_cols[0]
        else:
            raise RuntimeError("No encontré una columna de nombre de barrio en el SHP.")

    gdf = gdf.rename(columns={name_col: "barrio_nombre"})
    gdf["barrio_nombre"] = gdf["barrio_nombre"].astype(str).str.strip()

    # Elimina geometrías inválidas
    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf["geometry"] = gdf["geometry"].buffer(0)

    return gdf


def barrios_map(selected_barrios: List[str], gdf: gpd.GeoDataFrame, height=520):
    """
    Renderiza mapa folium con polígonos. Seleccionados se resaltan.
    """
    madrid_center = [40.4168, -3.7038]
    m = folium.Map(location=madrid_center, zoom_start=11, tiles="cartodbpositron")

    # estilo
    def style_fn(feature):
        b = feature["properties"].get("barrio_nombre", "")
        is_sel = b in set(selected_barrios)
        return {
            "fillColor": BRAND_DARK if is_sel else "#ffffff",
            "color": BRAND_DARK if is_sel else "#666666",
            "weight": 2 if is_sel else 1,
            "fillOpacity": 0.35 if is_sel else 0.08,
        }

    gj = GeoJson(
        data=json.loads(gdf.to_json()),
        style_function=style_fn,
        tooltip=GeoJsonTooltip(fields=["barrio_nombre"], aliases=["Barrio:"]),
        name="Barrios",
    )
    gj.add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)

    st_folium(m, height=height, use_container_width=True)


# =========================
# SURVEY FIELDS
# =========================
ROOM_OPTIONS = [
    "1 habitación",
    "2 habitaciones",
    "3 habitaciones",
    "4 habitaciones",
    "5 habitaciones",
    "6 habitaciones",
    "7 habitaciones",
    "8 habitaciones",
    "9 habitaciones",
    "10 habitaciones",
    "11+ habitaciones",
]

LIVING_PREF = ["Hombre", "Mujer", "Mixto"]


def whatsapp_country_from_phone(phone: str) -> str:
    """
    Inferencia básica por prefijo. (No dependemos de phonenumbers si falla)
    """
    p = phone.strip().replace(" ", "")
    if not p:
        return "—"
    if not p.startswith("+"):
        # si meten solo números, asumimos España si empieza con 6/7/9 y longitud típica
        if p.startswith(("6", "7", "9")) and len(p) in (9, 10):
            return "España (posible)"
        return "—"
    # mapeo básico
    prefixes = {
        "+34": "España",
        "+52": "México",
        "+1": "EEUU/Canadá",
        "+44": "Reino Unido",
        "+49": "Alemania",
        "+33": "Francia",
        "+39": "Italia",
        "+31": "Países Bajos",
        "+41": "Suiza",
        "+57": "Colombia",
        "+54": "Argentina",
        "+56": "Chile",
        "+51": "Perú",
    }
    for k, v in prefixes.items():
        if p.startswith(k):
            return v
    return "Otro"


def compute_score(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scoring simple/visible (lo puedes tunear).
    """
    weights = {
        "completitud": 25,
        "zonas": 15,
        "fechas": 20,
        "requisitos": 10,
        "operativo": 15,
    }

    completitud = 0
    required = ["full_name", "whatsapp", "age", "budget", "move_in", "move_out"]
    have = sum(1 for k in required if answers.get(k))
    completitud = int((have / len(required)) * 100)

    zonas = min(100, int(len(answers.get("barrios", [])) * 12.5))  # 8 barrios = 100
    fechas = 100 if answers.get("move_in") and answers.get("move_out") else 0
    requisitos = 100 if answers.get("living_with") else 0
    operativo = 100 if answers.get("rooms") else 0

    components = {
        "completitud": completitud,
        "zonas": zonas,
        "fechas": fechas,
        "requisitos": requisitos,
        "operativo": operativo,
    }

    weighted = 0.0
    total_w = sum(weights.values())
    for k, v in components.items():
        weighted += (v * weights[k]) / total_w

    return {
        "score_total": round(weighted, 1),
        "score_components": components,
        "weights": weights,
    }


def generate_whatsapp_intro(answers: Dict[str, Any]) -> str:
    budget = answers.get("budget", "—")
    barrios = answers.get("barrios", [])
    move_in = answers.get("move_in")
    move_out = answers.get("move_out")
    zonas = ", ".join(barrios[:6]) + ("…" if len(barrios) > 6 else "")
    return (
        "Hola! Soy del equipo de HausMate Match 😊\n"
        f"Vi tu perfil: budget €{budget}, zonas {zonas if zonas else '—'}, "
        f"fechas {move_in if move_in else '—'}–{move_out if move_out else '—'}.\n"
        "¿Te va bien si te comparto opciones que encajen contigo hoy?"
    )


# =========================
# APP
# =========================
st.set_page_config(page_title=APP_NAME, page_icon="🏠", layout="wide")

brand_css()
render_header()

# Sidebar Admin
with st.sidebar:
    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    st.markdown("### 🔒 Admin")
    admin_pw = get_secret("ADMIN_PASSWORD", "")
    if not admin_pw:
        st.warning("No hay ADMIN_PASSWORD en Secrets.")
    input_pw = st.text_input("Password admin", type="password")
    if st.button("Entrar"):
        if input_pw and admin_pw and input_pw == admin_pw:
            st.session_state["admin_ok"] = True
            st.success("Admin activado ✅")
        else:
            st.session_state["admin_ok"] = False
            st.error("Password incorrecto")
    if st.session_state.get("admin_ok"):
        st.info("Modo admin activo")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
st.markdown("### 📝 Encuesta")
st.markdown("Completa esto para que podamos hacerte match rápido y bien.")
st.markdown("</div>", unsafe_allow_html=True)

# Load barrios
barrios_load_err = ""
gdf_barrios = None
try:
    with st.spinner("Cargando mapa de barrios de Madrid…"):
        gdf_barrios = load_barrios_geodata()
except Exception as e:
    barrios_load_err = str(e)

if "selected_barrios" not in st.session_state:
    st.session_state["selected_barrios"] = []

# Form
with st.form("survey_form", clear_on_submit=False):
    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("Nombre y apellido *", placeholder="Ej. Michelle De Riquer")
    with c2:
        whatsapp = st.text_input("WhatsApp (con lada) *", placeholder="+34 6XXXXXXXX")
    with c3:
        age = st.number_input("Edad *", min_value=16, max_value=99, value=25, step=1)

    country_guess = whatsapp_country_from_phone(whatsapp)
    st.caption(f"📍 País por lada: **{country_guess}**")

    c4, c5, c6 = st.columns(3)
    with c4:
        budget = st.number_input("Presupuesto mensual (€) *", min_value=0, value=900, step=50)
    with c5:
        rooms = st.selectbox("Habitaciones (elige una) *", ROOM_OPTIONS, index=1)
    with c6:
        living_with = st.selectbox("¿Deseas vivir con…? *", LIVING_PREF, index=2)

    st.markdown("---")
    st.markdown("### 🗺️ Zonas / Barrios (selecciona 1 o varios)")

    if barrios_load_err:
        st.markdown(f"<div class='danger'>No pude cargar el mapa: {barrios_load_err}</div>", unsafe_allow_html=True)
        barrios_options = []
    else:
        barrios_options = sorted(gdf_barrios["barrio_nombre"].unique().tolist())

    # Multiselect + mapa resaltado (persistente)
    selected = st.multiselect(
        "Busca y selecciona barrios",
        options=barrios_options,
        default=st.session_state["selected_barrios"],
        help="Puedes seleccionar varios. Se quedarán marcados en el mapa.",
    )
    st.session_state["selected_barrios"] = selected

    if not barrios_load_err and gdf_barrios is not None:
        barrios_map(selected, gdf_barrios, height=520)

    st.markdown("---")
    st.markdown("### 📅 Fechas")
    c7, c8 = st.columns(2)
    with c7:
        move_in = st.date_input("Fecha de entrada *", value=dt.date.today())
    with c8:
        move_out = st.date_input("Fecha de salida *", value=dt.date.today() + dt.timedelta(days=60))

    st.markdown("---")
    st.markdown("### 🧩 Preferencias extra (opcional)")
    notes = st.text_area("Cuéntanos lo más importante (rutina, mascotas, humo, etc.)", height=120)

    submitted = st.form_submit_button("✅ Enviar")

    st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    # payload
    answers = {
        "full_name": full_name.strip(),
        "whatsapp": whatsapp.strip(),
        "country_guess": country_guess,
        "age": int(age) if age else None,
        "budget": int(budget) if budget else None,
        "rooms": rooms,
        "living_with": living_with,
        "barrios": st.session_state.get("selected_barrios", []),
        "move_in": str(move_in) if move_in else None,
        "move_out": str(move_out) if move_out else None,
        "notes": notes.strip(),
    }

    score = compute_score(answers)

    payload = {
        "full_name": answers["full_name"],
        "whatsapp": answers["whatsapp"],
        "country_guess": answers["country_guess"],
        "age": answers["age"],
        "budget": answers["budget"],
        "rooms": answers["rooms"],
        "living_with": answers["living_with"],
        "barrios": answers["barrios"],
        "move_in": answers["move_in"],
        "move_out": answers["move_out"],
        "notes": answers["notes"],
        "score_total": score["score_total"],
        "score_components": score["score_components"],
        "created_at": dt.datetime.utcnow().isoformat(),
    }

    ok, err = save_to_supabase(payload)
    if ok:
        st.success("✅ Listo, guardamos tu información.")
    else:
        st.error("No pude guardar tu respuesta en este momento.")
        st.code(err)

    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    st.markdown("### 🧠 Sistema de scoring (visible)")
    st.metric("Score total", f"{score['score_total']}/100")
    st.json(score["score_components"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    st.markdown("### ✉️ Generate WhatsApp introduction message")
    st.text_area("Copia y pega:", value=generate_whatsapp_intro(answers), height=100)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>")
    st.button("➕ Nuevo registro", on_click=lambda: st.session_state.update({"selected_barrios": []}))

# =========================
# ADMIN RESULTS VIEW
# =========================
if admin_password_ok():
    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    st.markdown("## 📊 Resultados (solo admin)")

    client, err = get_supabase_client()
    table = get_secret("SUPABASE_TABLE", "hausmate_leads").strip()

    if client is None:
        st.error(err)
    else:
        try:
            # últimos 200
            res = client.table(table).select("*").order("created_at", desc=True).limit(200).execute()
            rows = res.data if hasattr(res, "data") else []
            df = pd.DataFrame(rows)
            if df.empty:
                st.info("Aún no hay registros.")
            else:
                st.dataframe(df, use_container_width=True, height=420)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar CSV", data=csv, file_name="hausmate_leads.csv", mime="text/csv")
        except Exception as e:
            st.error(f"No pude leer resultados: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
