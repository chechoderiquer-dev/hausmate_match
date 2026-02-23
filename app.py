# app.py
# HausMate Match — branded dynamic survey + Supabase storage + admin-only results
#
# ✅ IMPORTANT (requirements.txt)
# Add this line if you don't have it yet:
# supabase>=2.0.0
#
# ✅ IMPORTANT (Streamlit Secrets - TOML)
# ADMIN_PASSWORD = "..."
# SUPABASE_URL = "https://<YOUR_PROJECT_ID>.supabase.co"
# SUPABASE_SERVICE_ROLE_KEY = "sb_secret_..."
# SUPABASE_TABLE = "hausmate_leads"
#
# ✅ IMPORTANT (Supabase table)
# Create a table named like SUPABASE_TABLE with columns:
# - nombre (text)
# - telefono (text)
# - edad (int4)
# - genero (text)
# - pref_genero (text)
# - idioma (text)
# - zona (text)                # pipe-separated e.g. "Chamberí|Retiro"
# - budget (int4)
# - inicio (date)
# - fin (date)
# - max_compartir_con (int4)
# - banos_min (int4)
# - notas (text)
# - rooms_pref (text)          # e.g. "1|2|3|..."
# - l_country (text)           # inferred from phone
# - created_at (timestamptz default now())
#
# Then enable RLS ON and add policy to allow ONLY service-role inserts (recommended).
# Easiest: keep RLS OFF while testing, then lock later.

import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from supabase import create_client
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium


# ----------------------------
# Branding (colors from logo)
# ----------------------------
BRAND_PRIMARY = "#86C1C9"   # teal from your logo bg
BRAND_DARK = "#143A3F"
BRAND_TEXT = "#0F172A"
BRAND_CARD = "#FFFFFF"
BRAND_MUTED = "#EAF6F7"


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="HausMate Match — Encuesta",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_css():
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: linear-gradient(180deg, {BRAND_PRIMARY} 0%, #ffffff 55%);
            }}
            .block-container {{
                padding-top: 1.2rem;
                padding-bottom: 2rem;
                max-width: 1100px;
            }}
            h1, h2, h3, h4, h5 {{
                color: {BRAND_TEXT};
            }}
            .hm-card {{
                background: {BRAND_CARD};
                border-radius: 18px;
                padding: 18px 18px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.10);
                border: 1px solid rgba(0,0,0,0.06);
            }}
            .hm-pill {{
                display:inline-block;
                padding:6px 10px;
                border-radius: 999px;
                background: {BRAND_MUTED};
                color: {BRAND_DARK};
                font-weight:600;
                margin-right:6px;
                margin-bottom:6px;
                font-size: 13px;
                border: 1px solid rgba(20,58,63,0.12);
            }}
            .hm-header {{
                display:flex;
                align-items:center;
                gap: 14px;
                margin-bottom: 10px;
            }}
            .hm-logo {{
                width: 86px;
                height: 86px;
                border-radius: 16px;
                object-fit: cover;
                border: 2px solid rgba(255,255,255,0.6);
                box-shadow: 0 10px 25px rgba(0,0,0,0.12);
                background: white;
            }}
            .hm-sub {{
                color: rgba(15,23,42,0.75);
                margin-top: -6px;
            }}
            .hm-step {{
                font-weight:700;
                color: {BRAND_DARK};
                background: rgba(255,255,255,0.65);
                border: 1px solid rgba(20,58,63,0.15);
                padding: 6px 10px;
                border-radius: 12px;
                display:inline-block;
            }}
            .hm-btn-primary button {{
                background: {BRAND_DARK} !important;
                color: white !important;
                border-radius: 12px !important;
                border: none !important;
                padding: 0.6rem 1rem !important;
                font-weight: 700 !important;
            }}
            .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {{
                border-radius: 12px !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# ----------------------------
# Helpers
# ----------------------------
def get_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in Streamlit Secrets."
        )
    return create_client(url, key)


def safe_parse_phone(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (e164, country_name) if possible.
    """
    if not raw:
        return None, None

    # Normalize common input
    raw = raw.strip()
    # If user writes "6XXXXXXXX" without +34, we try Spain default
    default_region = "ES"

    try:
        num = phonenumbers.parse(raw, default_region)
        if not phonenumbers.is_valid_number(num):
            return None, None
        e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
        region = phonenumbers.region_code_for_number(num)
        return e164, region
    except NumberParseException:
        return None, None


def compute_completeness(payload: Dict) -> int:
    """
    A simple completeness score (0–100) based on filled fields.
    """
    keys = [
        "nombre",
        "telefono",
        "edad",
        "genero",
        "pref_genero",
        "idioma",
        "zona",
        "budget",
        "inicio",
        "fin",
        "max_compartir_con",
        "banos_min",
    ]
    filled = sum(1 for k in keys if payload.get(k) not in (None, "", [], {}))
    return int(round((filled / len(keys)) * 100))


def whatsapp_intro(payload: Dict) -> str:
    zonas = payload.get("zona", "")
    zonas_pretty = zonas.replace("|", ", ")
    budget = payload.get("budget", "—")
    inicio = payload.get("inicio", "—")
    fin = payload.get("fin", "—")
    return (
        "Hola! Soy del equipo de HausMate Match 😊\n"
        f"Vi tu perfil: budget €{budget}, zonas {zonas_pretty}, fechas {inicio}–{fin}.\n"
        "¿Te va bien si te comparto opciones que encajen contigo hoy?"
    )


# ----------------------------
# Madrid zones (map + list)
# NOTE: without a full GeoJSON file, we do:
# - full selection list via multiselect
# - clickable map markers for the most used/central zones (nice UX)
# Users can still pick ANY barrio from the list; map helps visual.
# ----------------------------
ALL_ZONAS = [
    # Distritos/zonas (broad + common barrio names people use)
    "Centro", "Sol", "Malasaña", "Chueca", "Lavapiés", "La Latina", "Huertas",
    "Salamanca", "Recoletos", "Goya", "Lista", "Castellana", "Ibiza", "Jerónimos",
    "Retiro", "Pacífico", "Adelfas", "Estrella", "Niño Jesús",
    "Chamberí", "Trafalgar", "Almagro", "Ríos Rosas", "Arapiles", "Gaztambide",
    "Argüelles", "Moncloa", "Ciudad Universitaria", "Valdezarza",
    "Tetuán", "Cuatro Caminos", "Castillejos", "Bellas Vistas",
    "Chamartín", "El Viso", "Prosperidad", "Nueva España", "Hispanoamérica",
    "Madrid Río", "Legazpi", "Delicias", "Atocha", "Palos de la Frontera",
    "Usera", "Carabanchel", "Latina (distrito)", "Aluche",
    "Puente de Vallecas", "Vallecas", "Moratalaz", "Ciudad Lineal",
    "Hortaleza", "Sanchinarro", "Las Tablas", "Valdebebas",
    "San Blas", "Canillejas", "Barajas",
    # You can keep extending this list any time — it supports “all barrios” by adding names here.
]

# Map marker centroids for popular zones (approx; just for visual selection).
ZONA_COORDS = {
    "Sol": (40.4169, -3.7035),
    "Malasaña": (40.4278, -3.7042),
    "Chueca": (40.4231, -3.6973),
    "Lavapiés": (40.4089, -3.7018),
    "La Latina": (40.4106, -3.7082),
    "Huertas": (40.4133, -3.6978),
    "Recoletos": (40.4235, -3.6887),
    "Goya": (40.4259, -3.6756),
    "Ibiza": (40.4197, -3.6735),
    "Jerónimos": (40.4159, -3.6898),
    "Retiro": (40.4153, -3.6844),
    "Chamberí": (40.4340, -3.7038),
    "Trafalgar": (40.4324, -3.7005),
    "Almagro": (40.4307, -3.6922),
    "Ríos Rosas": (40.4410, -3.7022),
    "Arapiles": (40.4328, -3.7077),
    "Argüelles": (40.4303, -3.7173),
    "Moncloa": (40.4359, -3.7194),
    "Ciudad Universitaria": (40.4483, -3.7240),
    "Chamartín": (40.4686, -3.6795),
    "El Viso": (40.4447, -3.6787),
    "Prosperidad": (40.4445, -3.6687),
    "Tetuán": (40.4597, -3.6976),
    "Cuatro Caminos": (40.4467, -3.7040),
    "Madrid Río": (40.4019, -3.7190),
    "Atocha": (40.4066, -3.6904),
    "Delicias": (40.4010, -3.7002),
    "Sanchinarro": (40.4940, -3.6602),
    "Las Tablas": (40.5053, -3.6720),
    "Valdebebas": (40.4882, -3.6083),
}


def render_map_selector(selected: List[str]) -> List[str]:
    """
    Click markers to toggle zones.
    """
    m = folium.Map(location=(40.4168, -3.7038), zoom_start=12, control_scale=True)
    cluster = MarkerCluster().add_to(m)

    # markers for known coords
    for name, (lat, lon) in ZONA_COORDS.items():
        is_selected = name in selected
        emoji = "✅" if is_selected else "📍"
        folium.Marker(
            location=(lat, lon),
            tooltip=f"{emoji} {name}",
            popup=name,
        ).add_to(cluster)

    out = st_folium(m, height=420, width=None)

    # When user clicks, folium returns last_object_clicked_popup or tooltip data depending on platform
    clicked_name = None

    # Try popup
    if out and isinstance(out, dict):
        popup = out.get("last_object_clicked_popup")
        if popup and isinstance(popup, str):
            clicked_name = popup

        # Some builds return tooltip instead
        if not clicked_name:
            tt = out.get("last_object_clicked_tooltip")
            if tt and isinstance(tt, str):
                # tooltip like "✅ Sol" or "📍 Sol" -> remove emoji
                clicked_name = tt.replace("✅", "").replace("📍", "").strip()

    if clicked_name and clicked_name in ZONA_COORDS:
        if clicked_name in selected:
            selected.remove(clicked_name)
        else:
            selected.append(clicked_name)

    return selected


# ----------------------------
# State
# ----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

if "selected_zonas" not in st.session_state:
    st.session_state.selected_zonas = []

if "rooms_pref" not in st.session_state:
    st.session_state.rooms_pref = []

if "submitted_ok" not in st.session_state:
    st.session_state.submitted_ok = False


# ----------------------------
# Header (logo)
# ----------------------------
colA, colB = st.columns([0.25, 0.75], vertical_alignment="center")

with colA:
    # If you add a file to repo: assets/logo.png, it will show.
    # Otherwise it shows a nice fallback.
    try:
        st.image("assets/logo.png", use_container_width=True)
    except Exception:
        st.markdown(
            f"""
            <div class="hm-card" style="text-align:center;">
                <div style="font-size:34px;">🏡</div>
                <div style="font-weight:800; color:{BRAND_DARK};">HausMate</div>
                <div style="margin-top:-6px; font-weight:700; color:{BRAND_DARK}; opacity:0.9;">Match</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with colB:
    st.markdown(
        f"""
        <div class="hm-card">
            <div class="hm-header">
                <div>
                    <div style="font-size:30px; font-weight:900; color:{BRAND_TEXT};">Encuesta HausMate Match</div>
                    <div class="hm-sub">Responde en 2–3 minutos. Tus respuestas se usan para encontrar el mejor match.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")


# ----------------------------
# Sidebar: Admin (results only for you)
# ----------------------------
with st.sidebar:
    st.markdown("## 🔒 Admin")
    admin_pass = st.text_input("Admin password", type="password")
    admin_ok = bool(admin_pass) and admin_pass == st.secrets.get("ADMIN_PASSWORD", "")
    if admin_ok:
        st.success("Admin unlocked")
        st.divider()

        if st.button("🔄 Refresh results"):
            st.rerun()

        try:
            supa = get_supabase()
            table = st.secrets.get("SUPABASE_TABLE", "hausmate_leads")

            # Try order by created_at if exists
            try:
                res = supa.table(table).select("*").order("created_at", desc=True).limit(500).execute()
            except Exception:
                res = supa.table(table).select("*").limit(500).execute()

            rows = res.data or []
            df = pd.DataFrame(rows)
            st.write("### Results")
            st.dataframe(df, use_container_width=True, height=420)

            if not df.empty:
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", data=csv, file_name="hausmate_results.csv", mime="text/csv")

        except Exception as e:
            st.error("Admin: could not read Supabase.")
            st.exception(e)
    else:
        st.caption("Solo tú puedes ver resultados.")


# ----------------------------
# Stepper UI
# ----------------------------
TOTAL_STEPS = 4
progress = int(((st.session_state.step - 1) / (TOTAL_STEPS - 1)) * 100) if TOTAL_STEPS > 1 else 0
st.progress(progress)


def nav_buttons(can_back=True, can_next=True, next_label="Siguiente ➜", back_label="⟵ Atrás"):
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if can_back and st.button(back_label):
            st.session_state.step = max(1, st.session_state.step - 1)
            st.rerun()
    with c3:
        st.markdown('<div class="hm-btn-primary">', unsafe_allow_html=True)
        if can_next and st.button(next_label):
            st.session_state.step = min(TOTAL_STEPS, st.session_state.step + 1)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Form data (stored in session)
# ----------------------------
if "form" not in st.session_state:
    st.session_state.form = {
        "nombre": "",
        "telefono": "",
        "edad": 0,
        "genero": "mujer",
        "pref_genero": "mixto",
        "idioma": "Spanish",
        "budget": 0,
        "inicio": date.today(),
        "fin": date.today(),
        "max_compartir_con": 2,
        "banos_min": 1,
        "notas": "",
    }


# ----------------------------
# Step 1 — Perfil
# ----------------------------
if st.session_state.step == 1:
    st.markdown('<div class="hm-card">', unsafe_allow_html=True)
    st.markdown('<span class="hm-step">Paso 1/4 — Perfil</span>', unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.form["nombre"] = st.text_input(
            "Nombre y apellido *",
            value=st.session_state.form["nombre"],
            placeholder="Ej. Sofía García",
        )
        st.session_state.form["telefono"] = st.text_input(
            "WhatsApp (con lada) *",
            value=st.session_state.form["telefono"],
            placeholder="+34 6XXXXXXXX",
            help="Pon tu número con código de país. Ej: +34 6XXXXXXXX",
        )
        e164, country = safe_parse_phone(st.session_state.form["telefono"])
        if e164:
            st.success(f"Detectado: {e164} (Región: {country})")
        else:
            st.info("Tip: usa formato +34..., +52..., etc. para detectar país automáticamente.")

    with c2:
        st.session_state.form["edad"] = st.number_input(
            "Edad *",
            min_value=16,
            max_value=99,
            value=int(st.session_state.form.get("edad") or 25),
            step=1,
        )
        st.session_state.form["genero"] = st.selectbox(
            "Género *",
            options=["mujer", "hombre", "otro"],
            index=["mujer", "hombre", "otro"].index(st.session_state.form.get("genero", "mujer")),
        )
        st.session_state.form["pref_genero"] = st.selectbox(
            "¿Con quién te gustaría vivir? *",
            options=["solo_mujeres", "solo_hombres", "mixto"],
            index=["solo_mujeres", "solo_hombres", "mixto"].index(st.session_state.form.get("pref_genero", "mixto")),
            help="Preferencia de roommates",
        )
        st.session_state.form["idioma"] = st.selectbox(
            "Idioma preferido *",
            options=["Spanish", "English", "French", "Italian", "German", "Portuguese"],
            index=["Spanish", "English", "French", "Italian", "German", "Portuguese"].index(st.session_state.form.get("idioma", "Spanish")),
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    nav_buttons(can_back=False, can_next=True)


# ----------------------------
# Step 2 — Presupuesto + Fechas + Habitaciones
# ----------------------------
if st.session_state.step == 2:
    st.markdown('<div class="hm-card">', unsafe_allow_html=True)
    st.markdown('<span class="hm-step">Paso 2/4 — Presupuesto & Fechas</span>', unsafe_allow_html=True)
    st.write("")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.form["budget"] = st.number_input(
            "Budget mensual (€) *",
            min_value=200,
            max_value=15000,
            value=int(st.session_state.form.get("budget") or 900),
            step=50,
        )
    with c2:
        st.session_state.form["inicio"] = st.date_input(
            "Fecha inicio *",
            value=st.session_state.form.get("inicio") or date.today(),
        )
    with c3:
        st.session_state.form["fin"] = st.date_input(
            "Fecha fin (si aplica) *",
            value=st.session_state.form.get("fin") or date.today(),
        )

    st.write("")
    st.subheader("Preferencia de habitaciones (elige 10 o más si quieres)")
    room_opts = [str(i) for i in range(1, 21)] + ["20+"]
    st.session_state.rooms_pref = st.multiselect(
        "¿Cuántas habitaciones te gustaría que tenga el piso? (multi-select)",
        options=room_opts,
        default=st.session_state.rooms_pref or ["2", "3"],
        help="Puedes seleccionar múltiples opciones.",
    )

    st.write("")
    c4, c5 = st.columns(2)
    with c4:
        st.session_state.form["max_compartir_con"] = st.number_input(
            "Máximo de personas para compartir (roommates) *",
            min_value=0,
            max_value=12,
            value=int(st.session_state.form.get("max_compartir_con") or 2),
            step=1,
        )
    with c5:
        st.session_state.form["banos_min"] = st.number_input(
            "Baños mínimos *",
            min_value=1,
            max_value=6,
            value=int(st.session_state.form.get("banos_min") or 1),
            step=1,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    nav_buttons(can_back=True, can_next=True)


# ----------------------------
# Step 3 — Zonas (map + list) multi select, sticky selection
# ----------------------------
if st.session_state.step == 3:
    st.markdown('<div class="hm-card">', unsafe_allow_html=True)
    st.markdown('<span class="hm-step">Paso 3/4 — Zonas en Madrid</span>', unsafe_allow_html=True)
    st.write("Selecciona **una o varias** zonas. Puedes hacerlo por lista y/o con el mapa (clic para marcar/desmarcar).")
    st.write("")

    left, right = st.columns([0.52, 0.48], vertical_alignment="top")
    with left:
        st.session_state.selected_zonas = st.multiselect(
            "Lista de zonas (multi-select) *",
            options=sorted(set(ALL_ZONAS)),
            default=st.session_state.selected_zonas,
            help="Si falta alguna zona, puedes escribirla en Notas al final y la añadimos.",
        )

        st.write("**Seleccionadas:**")
        if st.session_state.selected_zonas:
            st.markdown(
                "".join([f'<span class="hm-pill">{z}</span>' for z in st.session_state.selected_zonas]),
                unsafe_allow_html=True,
            )
        else:
            st.info("Aún no has seleccionado zonas.")

    with right:
        st.caption("🗺️ Mapa (clic en marcadores para seleccionar).")
        st.session_state.selected_zonas = render_map_selector(st.session_state.selected_zonas)

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    nav_buttons(can_back=True, can_next=True)


# ----------------------------
# Step 4 — Notas + Submit
# ----------------------------
if st.session_state.step == 4:
    st.markdown('<div class="hm-card">', unsafe_allow_html=True)
    st.markdown('<span class="hm-step">Paso 4/4 — Confirmación</span>', unsafe_allow_html=True)
    st.write("")

    st.session_state.form["notas"] = st.text_area(
        "Notas (opcional)",
        value=st.session_state.form.get("notas", ""),
        placeholder="Ej: Busco roomies limpios, no fiestas, cerca de metro, etc.",
        height=110,
    )

    # Build payload
    e164, region = safe_parse_phone(st.session_state.form.get("telefono", ""))
    zonas_pipe = "|".join(st.session_state.selected_zonas) if st.session_state.selected_zonas else ""
    rooms_pipe = "|".join(st.session_state.rooms_pref) if st.session_state.rooms_pref else ""

    payload = {
        "nombre": (st.session_state.form.get("nombre") or "").strip(),
        "telefono": e164 or (st.session_state.form.get("telefono") or "").strip(),
        "edad": int(st.session_state.form.get("edad") or 0),
        "genero": st.session_state.form.get("genero"),
        "pref_genero": st.session_state.form.get("pref_genero"),
        "idioma": st.session_state.form.get("idioma"),
        "zona": zonas_pipe,
        "budget": int(st.session_state.form.get("budget") or 0),
        "inicio": str(st.session_state.form.get("inicio")),
        "fin": str(st.session_state.form.get("fin")),
        "max_compartir_con": int(st.session_state.form.get("max_compartir_con") or 0),
        "banos_min": int(st.session_state.form.get("banos_min") or 1),
        "notas": st.session_state.form.get("notas", ""),
        "rooms_pref": rooms_pipe,
        "l_country": region or "",
        "created_at": datetime.utcnow().isoformat(),
    }

    completeness = compute_completeness(payload)

    st.subheader("Resumen")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Nombre:** {payload['nombre'] or '—'}")
        st.write(f"**WhatsApp:** {payload['telefono'] or '—'}")
        st.write(f"**Edad:** {payload['edad'] or '—'}")
        st.write(f"**Género:** {payload['genero'] or '—'}")
        st.write(f"**Preferencia:** {payload['pref_genero'] or '—'}")
        st.write(f"**Idioma:** {payload['idioma'] or '—'}")
    with c2:
        st.write(f"**Budget:** €{payload['budget'] or '—'}")
        st.write(f"**Fechas:** {payload['inicio']} – {payload['fin']}")
        st.write(f"**Zonas:** {payload['zona'].replace('|', ', ') if payload['zona'] else '—'}")
        st.write(f"**Rooms:** {payload['rooms_pref'].replace('|', ', ') if payload['rooms_pref'] else '—'}")
        st.write(f"**Máx compartir con:** {payload['max_compartir_con']}")
        st.write(f"**Baños mínimos:** {payload['banos_min']}")

    st.write("")
    st.info(f"Completitud: **{completeness}%**")

    st.write("")
    st.subheader("Generate WhatsApp introduction message")
    st.text_area("Mensaje", value=whatsapp_intro(payload), height=90)

    st.write("")
    st.markdown('<div class="hm-btn-primary">', unsafe_allow_html=True)
    submit = st.button("✅ Enviar encuesta", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        # Validate essentials
        errors = []
        if not payload["nombre"]:
            errors.append("Falta nombre.")
        if not payload["telefono"]:
            errors.append("Falta WhatsApp válido (usa +34..., +52..., etc.).")
        if not payload["zona"]:
            errors.append("Selecciona al menos una zona.")
        if payload["budget"] <= 0:
            errors.append("Budget inválido.")

        if errors:
            st.error("Corrige esto antes de enviar:\n- " + "\n- ".join(errors))
        else:
            try:
                supa = get_supabase()
                table = st.secrets.get("SUPABASE_TABLE", "hausmate_leads")

                # Insert
                res = supa.table(table).insert(payload).execute()
                st.session_state.submitted_ok = True
                st.success("¡Listo! Guardamos tu respuesta ✅")
                st.balloons()

            except Exception as e:
                st.error("No pude guardar tu respuesta en este momento.")
                st.exception(e)

    st.write("")
    nav_buttons(can_back=True, can_next=False, next_label="")

    st.markdown("</div>", unsafe_allow_html=True)

# Footer note
st.caption("© HausMate Match — Tus respuestas se almacenan de forma privada. Resultados visibles solo para Admin.")
