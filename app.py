# ---------------------------
# HausMate Match (Streamlit) - FINAL (Cloud Safe)
# - NO geopandas/shapely/pyproj (evita fallos en Streamlit Cloud)
# - Mapa con barrios (GeoJSON) + click -> barrio via point-in-polygon (pure python)
# - Branding + Logo
# - Anti-duplicados por teléfono E.164
# - Export Excel con 13 columnas exactas
# ---------------------------

import json
import hashlib
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.request import urlretrieve

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException


# ---------------------------
# BRANDING (colores del logo HausMate)
# Ajusta si quieres, pero estos funcionan muy parecido al look de tu logo
# ---------------------------
HM_PRIMARY = "#7FB3B8"       # turquesa principal
HM_PRIMARY_DARK = "#5A9CA1"  # turquesa oscuro para botones
HM_BG = "#7FB3B8"            # fondo general
HM_CARD = "#FFFFFF"          # tarjetas
HM_TEXT = "#1F2E2F"          # texto oscuro
HM_WHITE = "#FFFFFF"


# ---------------------------
# GeoJSON barrios/neighborhoods (descarga automática)
# Si luego quieres el GeoJSON oficial de 131 barrios, lo cambiamos por el del Ayuntamiento.
# ---------------------------
MADRID_GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/madrid.geojson"
LOCAL_GEOJSON_PATH = "data/madrid_barrios.geojson"

DATA_PATH = "data/leads_store.csv"


# ---------------------------
# UI Styling
# ---------------------------
def inject_branding():
    st.set_page_config(page_title="HausMate Match", layout="wide")

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {HM_BG};
        }}
        .block-container {{
            padding-top: 2rem;
        }}
        .hm-shell {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .hm-header {{
            display: flex;
            align-items: center;
            gap: 18px;
            margin-bottom: 18px;
        }}
        .hm-title {{
            font-size: 36px;
            font-weight: 900;
            color: {HM_WHITE};
            margin: 0;
            line-height: 1.0;
        }}
        .hm-sub {{
            font-size: 16px;
            color: {HM_WHITE};
            opacity: 0.92;
            margin: 6px 0 0 0;
        }}
        .hm-card {{
            background: {HM_CARD};
            border-radius: 22px;
            padding: 22px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.10);
        }}
        .hm-pill {{
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            background: {HM_PRIMARY_DARK};
            color: white;
            font-weight: 700;
            margin: 5px 8px 0 0;
            font-size: 13px;
        }}
        .hm-muted {{
            color: rgba(31,46,47,0.72);
            font-size: 13px;
        }}

        /* Buttons */
        div.stButton > button {{
            background-color: {HM_PRIMARY_DARK};
            color: white;
            border-radius: 12px;
            border: none;
            padding: 10px 18px;
            font-weight: 700;
        }}
        div.stButton > button:hover {{
            background-color: {HM_PRIMARY};
            color: white;
        }}

        /* Inputs look */
        label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stRadio label {{
            font-weight: 700 !important;
            color: {HM_TEXT} !important;
        }}

        /* Progress bar */
        .stProgress > div > div > div {{
            background-color: {HM_PRIMARY_DARK};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header():
    st.markdown('<div class="hm-shell">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 6], vertical_alignment="center")

    with col1:
        # Subir tu logo como assets/logo.png
        try:
            st.image("assets/logo.png", width=120)
        except Exception:
            st.write("")

    with col2:
        st.markdown(
            """
            <div>
                <h1 class="hm-title">HausMate Match</h1>
                <p class="hm-sub">Encuentra tu match ideal en Madrid ✨</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def footer_close_shell():
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# Phone + Dedup
# ---------------------------
def normalize_phone(raw_phone: str, default_region: str = "ES"):
    raw_phone = (raw_phone or "").strip()
    if not raw_phone:
        return None, None, None
    try:
        if raw_phone.startswith("+"):
            p = phonenumbers.parse(raw_phone, None)
        else:
            p = phonenumbers.parse(raw_phone, default_region)

        if not phonenumbers.is_possible_number(p) or not phonenumbers.is_valid_number(p):
            return None, None, None

        e164 = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
        region = phonenumbers.region_code_for_number(p)
        country = p.country_code
        return e164, str(country), region
    except NumberParseException:
        return None, None, None


def make_dedupe_key(phone_e164: str):
    return hashlib.sha1(phone_e164.encode("utf-8")).hexdigest()


# ---------------------------
# Storage (CSV simple)
# ---------------------------
def load_store() -> pd.DataFrame:
    try:
        return pd.read_csv(DATA_PATH)
    except Exception:
        return pd.DataFrame()


def save_store(df: pd.DataFrame):
    Path("data").mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)


def upsert_store(row: dict):
    df = load_store()

    if df.empty:
        df = pd.DataFrame([row])
    else:
        if "dedupe_key" not in df.columns:
            df["dedupe_key"] = ""

        # ensure all row keys exist
        for k in row.keys():
            if k not in df.columns:
                df[k] = None

        mask = df["dedupe_key"] == row["dedupe_key"]
        if mask.any():
            df.loc[mask, list(row.keys())] = pd.DataFrame([row]).iloc[0].values
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    save_store(df)


# ---------------------------
# GeoJSON + Point-in-Polygon (pure python)
# ---------------------------
def ensure_geojson(local_path: str = LOCAL_GEOJSON_PATH):
    p = Path(local_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        urlretrieve(MADRID_GEOJSON_URL, str(p))


def _bbox_of_ring(ring):
    xs = [pt[0] for pt in ring]
    ys = [pt[1] for pt in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def _point_in_ring(x, y, ring):
    """
    Ray casting algorithm.
    ring: list of [lon, lat] points, closed or open.
    """
    inside = False
    n = len(ring)
    if n < 3:
        return False
    x0, y0 = ring[0]
    for i in range(1, n + 1):
        x1, y1 = ring[i % n]
        # check edge intersects ray
        if ((y0 > y) != (y1 > y)) and (x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-15) + x0):
            inside = not inside
        x0, y0 = x1, y1
    return inside


def _point_in_polygon(lon, lat, polygon_coords):
    """
    polygon_coords: list of rings
    First ring = outer, others = holes
    """
    outer = polygon_coords[0]
    if not _point_in_ring(lon, lat, outer):
        return False
    # holes
    for hole in polygon_coords[1:]:
        if _point_in_ring(lon, lat, hole):
            return False
    return True


@st.cache_data
def load_neighborhood_index():
    """
    Returns list of dicts:
      { name, geom_type, polygons, bboxes }
    where polygons is a list of polygons (each polygon = list of rings)
    """
    ensure_geojson(LOCAL_GEOJSON_PATH)
    with open(LOCAL_GEOJSON_PATH, "r", encoding="utf-8") as f:
        gj = json.load(f)

    features = gj.get("features", [])
    index = []

    for feat in features:
        props = feat.get("properties", {}) or {}
        name = props.get("name") or props.get("NAME") or props.get("barrio") or "—"
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])

        polygons = []
        bboxes = []

        if gtype == "Polygon":
            # coords = [ring1, ring2...]
            polygons.append(coords)
            bboxes.append(_bbox_of_ring(coords[0]))
        elif gtype == "MultiPolygon":
            # coords = [[poly1_rings], [poly2_rings], ...]
            for poly in coords:
                polygons.append(poly)
                bboxes.append(_bbox_of_ring(poly[0]))

        if polygons:
            index.append(
                {
                    "name": str(name),
                    "geom_type": gtype,
                    "polygons": polygons,
                    "bboxes": bboxes,
                }
            )

    return index


def barrio_from_click(lat, lon, neighborhood_index):
    """
    Given clicked lat/lon, return neighborhood name or None
    """
    x = lon
    y = lat

    for item in neighborhood_index:
        for poly, bb in zip(item["polygons"], item["bboxes"]):
            minx, miny, maxx, maxy = bb
            if x < minx or x > maxx or y < miny or y > maxy:
                continue
            if _point_in_polygon(x, y, poly):
                return item["name"]
    return None


def geojson_for_folium():
    ensure_geojson(LOCAL_GEOJSON_PATH)
    with open(LOCAL_GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------
# Scoring + WhatsApp
# ---------------------------
def calc_score(row: dict) -> tuple[int, dict]:
    score = 0
    breakdown = {}

    # Completitud (0-25)
    required = ["nombre", "telefono", "edad", "budget", "inicio", "fin"]
    complete = sum(1 for k in required if row.get(k))
    comp = round((complete / len(required)) * 25)
    score += comp
    breakdown["completitud"] = comp

    # Zonas (0-15)
    zonas = (row.get("zona") or "").split("|") if row.get("zona") else []
    zonas = [z for z in zonas if z and z != "—"]
    if len(zonas) == 0:
        zscore = 8
    elif len(zonas) == 1:
        zscore = 5
    elif 2 <= len(zonas) <= 4:
        zscore = 15
    else:
        zscore = 10
    score += zscore
    breakdown["zonas"] = zscore

    # Fechas (0-20)
    today = date.today()
    inicio = row.get("inicio")
    if inicio:
        days = (inicio - today).days
        if days <= 30:
            fscore = 20
        elif days <= 60:
            fscore = 15
        else:
            fscore = 10
    else:
        fscore = 0
    score += fscore
    breakdown["fechas"] = fscore

    # Requisitos (0-20)
    banos = row.get("banos_min")
    if banos is None:
        rscore = 8
    elif banos <= 1:
        rscore = 20
    elif banos == 2:
        rscore = 15
    else:
        rscore = 10

    maxc = row.get("max_compartir_con")
    budget = row.get("budget") or 0
    if maxc == 1 and budget and budget < 900:
        rscore = max(0, rscore - 6)

    score += rscore
    breakdown["requisitos"] = rscore

    # Operativo (0-20)
    ops = 0
    if row.get("telefono"):
        ops += 10
    if row.get("idioma"):
        ops += 5
    notas = (row.get("notas") or "").strip()
    if len(notas) >= 20:
        ops += 5
    score += ops
    breakdown["operativo"] = ops

    score = max(0, min(100, score))
    return score, breakdown


def whatsapp_message(row: dict) -> str:
    zonas = row.get("zona") or "—"
    return (
        f"Hola! Soy del equipo de HausMate Match 😊\n"
        f"Vi tu perfil: budget €{row.get('budget','—')}, zonas {zonas}, "
        f"fechas {row.get('inicio','—')}–{row.get('fin','—')}.\n"
        f"¿Te va bien si te comparto opciones que encajen contigo hoy?"
    )


def export_xlsx(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="leads")
    return output.getvalue()


# ---------------------------
# Wizard
# ---------------------------
def init_state():
    defaults = dict(
        step=0,
        nombre="",
        telefono_raw="",
        edad=25,
        genero="",
        pref_genero="",
        idioma="Español",
        zonas_selected=[],
        budget=1500,
        inicio=date.today(),
        fin=date.today(),
        max_compartir_con=2,
        banos_min=1,
        notas="",
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def stepper():
    steps = ["Perfil", "Preferencias", "Idioma", "Zonas", "Budget", "Fechas", "Convivencia", "Notas", "Final"]
    i = st.session_state.step
    st.progress(min(1.0, i / (len(steps) - 1)))
    st.caption(f"Paso {i+1}/{len(steps)} — {steps[i]}")


def nav_buttons(can_back=True, can_next=True, next_label="Continuar"):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if can_back and st.button("⬅️ Atrás", use_container_width=True):
            st.session_state.step = max(0, st.session_state.step - 1)
            st.rerun()
    with c3:
        if can_next and st.button(next_label, use_container_width=True):
            st.session_state.step = min(8, st.session_state.step + 1)
            st.rerun()


def render_map(geojson_obj):
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, control_scale=True)

    def style_fn(_):
        return {
            "fillColor": HM_PRIMARY,
            "color": HM_PRIMARY_DARK,
            "weight": 1,
            "fillOpacity": 0.18,
        }

    def highlight_fn(_):
        return {"weight": 3, "fillOpacity": 0.28}

    folium.GeoJson(
        geojson_obj,
        name="Barrios",
        style_function=style_fn,
        highlight_function=highlight_fn,
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Barrio:"]),
    ).add_to(m)

    return st_folium(m, height=520, width=None)


# ---------------------------
# Main
# ---------------------------
def main():
    inject_branding()
    init_state()
    header()
    stepper()

    st.markdown('<div class="hm-shell"><div class="hm-card">', unsafe_allow_html=True)

    # Preload neighborhood index (cached)
    try:
        nindex = load_neighborhood_index()
        gj = geojson_for_folium()
    except Exception as e:
        nindex = []
        gj = None
        st.error("No pude cargar el mapa de barrios automáticamente.")
        st.code(str(e))

    step = st.session_state.step

    # STEP 0
    if step == 0:
        st.subheader("Primero, lo básico 🙂")
        st.session_state.nombre = st.text_input("Nombre y apellido", value=st.session_state.nombre, placeholder="Ej. Sofía Martínez")
        st.session_state.telefono_raw = st.text_input("WhatsApp (con lada)", value=st.session_state.telefono_raw, placeholder="+34 6XXXXXXXX")
        st.caption("Usamos tu WhatsApp para coordinar opciones y visitas.")
        st.session_state.edad = st.number_input("Edad", min_value=16, max_value=99, value=int(st.session_state.edad))
        nav_buttons(can_back=False)

    # STEP 1
    elif step == 1:
        st.subheader("Sobre ti")
        st.session_state.genero = st.selectbox("Género", ["", "Hombre", "Mujer", "Otro", "Prefiero no decir"])
        st.session_state.pref_genero = st.selectbox("¿Con quién quieres vivir?", ["", "Solo hombres", "Solo mujeres", "Mixto", "Me da igual"])
        nav_buttons()

    # STEP 2
    elif step == 2:
        st.subheader("Idioma")
        st.session_state.idioma = st.radio("¿En qué idioma prefieres que te hablemos?", ["Español", "English"], horizontal=True)
        nav_buttons()

    # STEP 3 - Map
    elif step == 3:
        st.subheader("¿En qué barrios te gustaría vivir?")
        st.caption("Haz click en el mapa: detectamos el barrio y lo agregamos a tu selección.")

        if gj is None or not nindex:
            st.warning("Mapa no disponible. Intenta refrescar o revisa logs.")
        else:
            out = render_map(gj)

            if out and out.get("last_clicked"):
                lat = out["last_clicked"]["lat"]
                lon = out["last_clicked"]["lng"]
                barrio = barrio_from_click(lat, lon, nindex)
                if barrio:
                    if barrio in st.session_state.zonas_selected:
                        st.session_state.zonas_selected.remove(barrio)
                    else:
                        st.session_state.zonas_selected.append(barrio)

            if st.session_state.zonas_selected:
                st.markdown("**Seleccionados:**")
                pills = "".join([f"<span class='hm-pill'>{z}</span>" for z in st.session_state.zonas_selected])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.info("Selecciona uno o varios barrios en el mapa.")

            if st.button("No estoy seguro, recomiéndame"):
                st.session_state.zonas_selected = ["—"]
                st.rerun()

        nav_buttons()

    # STEP 4
    elif step == 4:
        st.subheader("Presupuesto mensual 💸")
        st.session_state.budget = st.number_input("Budget (€)", min_value=200, max_value=20000, value=int(st.session_state.budget), step=50)
        nav_buttons()

    # STEP 5
    elif step == 5:
        st.subheader("Fechas")
        st.session_state.inicio = st.date_input("Inicio", value=st.session_state.inicio)
        st.session_state.fin = st.date_input("Fin", value=st.session_state.fin)

        if st.session_state.fin < st.session_state.inicio:
            st.error("La fecha fin no puede ser antes que la fecha inicio.")
            nav_buttons(can_next=False)
        else:
            nav_buttons()

    # STEP 6
    elif step == 6:
        st.subheader("Convivencia")
        st.session_state.max_compartir_con = st.slider("Máximo de personas para compartir", 1, 6, int(st.session_state.max_compartir_con))
        st.session_state.banos_min = st.radio("Baños mínimos", [1, 2, 3, 4], horizontal=True)
        nav_buttons()

    # STEP 7
    elif step == 7:
        st.subheader("Notas ✍️")
        st.session_state.notas = st.text_area("Notas / comentarios", value=st.session_state.notas, height=120,
                                              placeholder="Ej. trabajo desde casa, no mascotas, necesito ascensor…")
        nav_buttons(next_label="Ver mi Match")

    # STEP 8
    elif step == 8:
        st.subheader("Listo ✨")

        phone_e164, country, region = normalize_phone(st.session_state.telefono_raw)
        if not phone_e164:
            st.error("Tu WhatsApp no parece válido. Usa formato +34 6XXXXXXXX.")
            if st.button("⬅️ Volver"):
                st.session_state.step = 0
                st.rerun()
        else:
            zona_str = "|".join(st.session_state.zonas_selected) if st.session_state.zonas_selected else "—"

            # 13 columnas exactas
            excel_row = {
                "nombre": st.session_state.nombre.strip(),
                "telefono": phone_e164,
                "edad": int(st.session_state.edad),
                "genero": st.session_state.genero,
                "pref_genero": st.session_state.pref_genero,
                "idioma": st.session_state.idioma,
                "zona": zona_str,
                "budget": int(st.session_state.budget),
                "inicio": st.session_state.inicio,
                "fin": st.session_state.fin,
                "max_compartir_con": int(st.session_state.max_compartir_con),
                "banos_min": int(st.session_state.banos_min),
                "notas": (st.session_state.notas or "").strip(),
            }

            score, breakdown = calc_score(excel_row)
            st.metric("Match Score", f"{score}/100")
            st.write("**Detalle:**", breakdown)

            st.text_area("Generate WhatsApp introduction message", value=whatsapp_message(excel_row), height=120)

            dedupe_key = make_dedupe_key(phone_e164)
            store_row = {
                **excel_row,
                "telefono_raw": st.session_state.telefono_raw,
                "telefono_country": country,
                "telefono_region": region,
                "dedupe_key": dedupe_key,
                "match_score": score,
                "score_breakdown": json.dumps(breakdown, ensure_ascii=False),
            }
            upsert_store(store_row)
            st.success("Guardado ✅ (sin duplicados).")

            df_store = load_store()
            export_cols = [
                "nombre", "telefono", "edad", "genero", "pref_genero", "idioma", "zona",
                "budget", "inicio", "fin", "max_compartir_con", "banos_min", "notas"
            ]
            if not df_store.empty and all(c in df_store.columns for c in export_cols):
                df_export = df_store[export_cols].copy()
            else:
                df_export = pd.DataFrame([excel_row], columns=export_cols)

            st.download_button(
                "⬇️ Descargar Excel (leads)",
                data=export_xlsx(df_export),
                file_name="hausmate_match_leads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

            if st.button("➕ Nuevo registro", use_container_width=True):
                st.session_state.step = 0
                st.session_state.nombre = ""
                st.session_state.telefono_raw = ""
                st.session_state.edad = 25
                st.session_state.genero = ""
                st.session_state.pref_genero = ""
                st.session_state.idioma = "Español"
                st.session_state.zonas_selected = []
                st.session_state.budget = 1500
                st.session_state.inicio = date.today()
                st.session_state.fin = date.today()
                st.session_state.max_compartir_con = 2
                st.session_state.banos_min = 1
                st.session_state.notas = ""
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
    footer_close_shell()


if __name__ == "__main__":
    main()
