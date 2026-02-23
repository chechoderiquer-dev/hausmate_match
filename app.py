import os
import json
import datetime as dt
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import requests

import folium
from folium.features import GeoJson, GeoJsonTooltip
from streamlit_folium import st_folium


# =========================
# BRAND / UI
# =========================
APP_NAME = "HausMate Match"
LOGO_PATH_LOCAL = "logo.png"  # si subes el logo al repo con ese nombre, se verá

BRAND_BG = "#7FBBC2"
BRAND_BG_2 = "#D9F1F3"
BRAND_DARK = "#0C2D33"
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
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(12,45,51,0.12);
            border-radius: 18px;
            padding: 16px 16px;
            box-shadow: 0 6px 18px rgba(12,45,51,0.10);
          }}
          .haus-badge {{
            display:inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.75);
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
        if os.path.exists(LOGO_PATH_LOCAL):
            st.image(LOGO_PATH_LOCAL, use_container_width=True)
        else:
            st.markdown(f"<div class='haus-badge'>🏠 {APP_NAME}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h2 style='margin-bottom:0'>{APP_NAME}</h2>", unsafe_allow_html=True)
        st.markdown(
            "<div class='haus-badge'>Encuesta inteligente para encontrar tu match</div>",
            unsafe_allow_html=True,
        )


# =========================
# SECRETS HELPERS
# =========================
def get_secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, default)


# =========================
# SUPABASE
# =========================
def get_supabase_client():
    supabase_url = get_secret("SUPABASE_URL", "").strip()
    supabase_key = get_secret("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not supabase_url or not supabase_key:
        return None, "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en Secrets."

    if "supabase.co" not in supabase_url:
        return None, f"SUPABASE_URL no parece válida: {supabase_url}"

    try:
        from supabase import create_client
    except Exception:
        return None, "Falta instalar 'supabase'. Agrégalo en requirements.txt."

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
    return st.session_state.get("admin_ok") is True


# =========================
# BARRIOS GEOJSON (NO GEOPANDAS)
# =========================
# GeoJSON público con barrios/distritos (Madrid). Si quieres, luego lo cambiamos por otro.
# Este suele traer "name" o similar.
BARRIOS_GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/madrid-neighborhoods.geojson"

@st.cache_data(show_spinner=True)
def load_barrios_geojson() -> Dict[str, Any]:
    r = requests.get(BARRIOS_GEOJSON_URL, timeout=60)
    r.raise_for_status()
    return r.json()


def extract_barrios_list(geojson: Dict[str, Any]) -> List[str]:
    feats = geojson.get("features", [])
    names = []
    for f in feats:
        props = f.get("properties", {}) or {}
        # intenta varias keys comunes
        for k in ["name", "NAME", "neighborhood", "Barrio", "barrio", "NOMBRE"]:
            if k in props and props[k]:
                names.append(str(props[k]).strip())
                break
    # si no encontró nada, crea ids genéricos
    if not names:
        names = [f"Barrio {i+1}" for i in range(len(feats))]
    # únicos + orden
    names = sorted(list(dict.fromkeys(names)))
    return names


def style_fn(selected_set: set, name_value: str):
    is_sel = name_value in selected_set
    return {
        "fillColor": BRAND_DARK if is_sel else "#ffffff",
        "color": BRAND_DARK if is_sel else "#666666",
        "weight": 2 if is_sel else 1,
        "fillOpacity": 0.35 if is_sel else 0.08,
    }


def render_barrios_map(geojson: Dict[str, Any], selected_barrios: List[str], height=520):
    selected_set = set(selected_barrios)
    madrid_center = [40.4168, -3.7038]
    m = folium.Map(location=madrid_center, zoom_start=11, tiles="cartodbpositron")

    feats = geojson.get("features", [])
    for f in feats:
        props = f.get("properties", {}) or {}
        # determina nombre
        name_val = None
        for k in ["name", "NAME", "neighborhood", "Barrio", "barrio", "NOMBRE"]:
            if k in props and props[k]:
                name_val = str(props[k]).strip()
                break
        if not name_val:
            continue

        gj = GeoJson(
            data=f,
            style_function=lambda feature, n=name_val: style_fn(selected_set, n),
            tooltip=GeoJsonTooltip(fields=[], aliases=[]),
            name=name_val,
        )
        gj.add_child(folium.Tooltip(name_val))
        gj.add_to(m)

    st_folium(m, height=height, use_container_width=True)


# =========================
# SURVEY
# =========================
ROOM_OPTIONS = [
    "1 habitación", "2 habitaciones", "3 habitaciones", "4 habitaciones", "5 habitaciones",
    "6 habitaciones", "7 habitaciones", "8 habitaciones", "9 habitaciones", "10 habitaciones",
    "11+ habitaciones"
]
LIVING_PREF = ["Hombre", "Mujer", "Mixto"]


def whatsapp_country_from_phone(phone: str) -> str:
    p = phone.strip().replace(" ", "")
    if not p:
        return "—"
    if not p.startswith("+"):
        if p.startswith(("6", "7", "9")) and len(p) in (9, 10):
            return "España (posible)"
        return "—"
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
    weights = {"completitud": 25, "zonas": 15, "fechas": 20, "requisitos": 10, "operativo": 15}

    required = ["full_name", "whatsapp", "age", "budget", "move_in", "move_out"]
    have = sum(1 for k in required if answers.get(k))
    completitud = int((have / len(required)) * 100)

    zonas = min(100, int(len(answers.get("barrios", [])) * 12.5))
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

    total_w = sum(weights.values())
    weighted = sum((components[k] * weights[k]) / total_w for k in components)
    return {"score_total": round(weighted, 1), "score_components": components, "weights": weights}


def generate_whatsapp_intro(answers: Dict[str, Any]) -> str:
    zonas = answers.get("barrios", [])
    zonas_txt = ", ".join(zonas[:6]) + ("…" if len(zonas) > 6 else "")
    return (
        "Hola! Soy del equipo de HausMate Match 😊\n"
        f"Vi tu perfil: budget €{answers.get('budget','—')}, zonas {zonas_txt if zonas_txt else '—'}, "
        f"fechas {answers.get('move_in','—')}–{answers.get('move_out','—')}.\n"
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
    admin_pw = get_secret("ADMIN_PASSWORD", "").strip()
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

if "selected_barrios" not in st.session_state:
    st.session_state["selected_barrios"] = []

geo_err = ""
geojson = None
barrios_options = []
try:
    with st.spinner("Cargando mapa de barrios de Madrid…"):
        geojson = load_barrios_geojson()
        barrios_options = extract_barrios_list(geojson)
except Exception as e:
    geo_err = str(e)

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

    if geo_err:
        st.markdown(f"<div class='danger'>No pude cargar el mapa: {geo_err}</div>", unsafe_allow_html=True)
    else:
        selected = st.multiselect(
            "Busca y selecciona barrios",
            options=barrios_options,
            default=st.session_state["selected_barrios"],
            help="Puedes seleccionar varios. Se quedarán marcados en el mapa.",
        )
        st.session_state["selected_barrios"] = selected
        render_barrios_map(geojson, selected, height=520)

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

    st.button("➕ Nuevo registro", on_click=lambda: st.session_state.update({"selected_barrios": []}))

# ADMIN RESULTS
if admin_password_ok():
    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    st.markdown("## 📊 Resultados (solo admin)")

    client, err = get_supabase_client()
    table = get_secret("SUPABASE_TABLE", "hausmate_leads").strip()

    if client is None:
        st.error(err)
    else:
        try:
            res = client.table(table).select("*").order("created_at", desc=True).limit(200).execute()
            rows = res.data if hasattr(res, "data") else []
            df = pd.DataFrame(rows)
            if df.empty:
                st.info("Aún no hay registros.")
            else:
                st.dataframe(df, use_container_width=True, height=420)
                st.download_button(
                    "⬇️ Descargar CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="hausmate_leads.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"No pude leer resultados: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
