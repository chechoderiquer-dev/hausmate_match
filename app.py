import streamlit as st
import pandas as pd
import hashlib
from datetime import date
from io import BytesIO

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

import geopandas as gpd
from shapely.geometry import Point

import folium
from streamlit_folium import st_folium


# ---------------------------
# Branding (HausMate)
# ---------------------------
HM_PRIMARY = "#86C1C9"
HM_PRIMARY_DARK = "#2F7E86"
HM_CREAM = "#ECE7E1"
HM_TEXT = "#0F2D30"
HM_BG = "#F7FBFB"


# ---------------------------
# Helpers
# ---------------------------
def inject_branding():
    st.set_page_config(page_title="HausMate Match", layout="wide")
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {HM_BG};
            color: {HM_TEXT};
        }}
        .hm-header {{
            background: {HM_PRIMARY};
            border-radius: 18px;
            padding: 18px 18px;
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 18px;
        }}
        .hm-title {{
            font-size: 28px;
            font-weight: 800;
            color: {HM_CREAM};
            margin: 0;
            line-height: 1.1;
        }}
        .hm-sub {{
            color: {HM_CREAM};
            opacity: 0.95;
            margin: 2px 0 0 0;
            font-size: 14px;
        }}
        .hm-card {{
            background: #fff;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 10px 22px rgba(0,0,0,0.06);
        }}
        .hm-pill {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(47,126,134,0.12);
            color: {HM_PRIMARY_DARK};
            margin-right: 8px;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 13px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def calc_score(data: dict) -> tuple[int, dict]:
    score = 0
    breakdown = {}

    # Completitud (0-25)
    required = ["nombre", "telefono", "edad", "budget", "inicio", "fin"]
    complete = sum(1 for k in required if data.get(k))
    comp_score = round((complete / len(required)) * 25)
    score += comp_score
    breakdown["completitud"] = comp_score

    # Zonas (0-15)
    zonas = (data.get("zona") or "").split("|") if data.get("zona") else []
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
    if data.get("inicio"):
        days = (data["inicio"] - today).days
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
    banos = data.get("banos_min")
    if banos is None:
        rscore = 8
    elif banos <= 1:
        rscore = 20
    elif banos == 2:
        rscore = 15
    else:
        rscore = 10

    maxc = data.get("max_compartir_con")
    budget = data.get("budget") or 0
    if maxc == 1 and budget and budget < 900:
        rscore = max(0, rscore - 6)

    score += rscore
    breakdown["requisitos"] = rscore

    # Operativo (0-20)
    ops = 0
    if data.get("telefono"):
        ops += 10
    if data.get("idioma"):
        ops += 5
    notas = (data.get("notas") or "").strip()
    if len(notas) >= 20:
        ops += 5
    score += ops
    breakdown["operativo"] = ops

    score = max(0, min(100, score))
    return score, breakdown


def whatsapp_message(data: dict) -> str:
    zonas = data.get("zona") or "—"
    return (
        f"Hola! Soy del equipo de HausMate Match 😊\n"
        f"Vi tu perfil: budget €{data.get('budget','—')}, zonas {zonas}, "
        f"fechas {data.get('inicio','—')}–{data.get('fin','—')}.\n"
        f"¿Te va bien si te comparto opciones que encajen contigo hoy?"
    )


@st.cache_data
def load_barrios_geojson(path="data/madrid_barrios.geojson") -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)

    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    possible = ["name", "NOMBRE", "BARRIO", "NOM_BAR", "BARRIO_MAY"]
    name_col = None
    for c in possible:
        if c in gdf.columns:
            name_col = c
            break

    if name_col is None:
        for c in gdf.columns:
            if gdf[c].dtype == "object":
                name_col = c
                break

    if name_col:
        gdf = gdf.rename(columns={name_col: "barrio_name"})

    if "barrio_name" not in gdf.columns:
        gdf["barrio_name"] = "Barrio"

    gdf["barrio_name"] = gdf["barrio_name"].astype(str)
    return gdf


def barrio_from_click(gdf: gpd.GeoDataFrame, lat: float, lon: float):
    p = Point(lon, lat)
    try:
        sindex = gdf.sindex
        possible_matches_index = list(sindex.intersection(p.bounds))
        candidates = gdf.iloc[possible_matches_index]
        match = candidates[candidates.contains(p)]
    except Exception:
        match = gdf[gdf.contains(p)]

    if len(match) == 0:
        return None
    return match.iloc[0]["barrio_name"]


def export_xlsx(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="leads")
    return output.getvalue()


# ---------------------------
# Simple store: CSV local
# ---------------------------
DATA_PATH = "data/leads_store.csv"


def load_store() -> pd.DataFrame:
    try:
        return pd.read_csv(DATA_PATH)
    except:
        return pd.DataFrame()


def save_store(df: pd.DataFrame):
    df.to_csv(DATA_PATH, index=False)


def upsert_store(row: dict):
    df = load_store()
    if df.empty:
        df = pd.DataFrame([row])
    else:
        if "dedupe_key" not in df.columns:
            df["dedupe_key"] = ""

        mask = df["dedupe_key"] == row["dedupe_key"]
        if mask.any():
            df.loc[mask, :] = pd.DataFrame([row]).iloc[0].values
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    save_store(df)


# ---------------------------
# App
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


def header():
    col1, col2 = st.columns([1, 5])
    with col1:
        try:
            st.image("assets/hausmate_logo.png", width=90)
        except:
            st.write("")
    with col2:
        st.markdown(
            """
            <div class="hm-header">
              <div>
                <p class="hm-title">HausMate Match</p>
                <p class="hm-sub">Encuentra tu match ideal en Madrid en 2 minutos ✨</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


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


def render_map(gdf):
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, control_scale=True)

    def style_fn(_):
        return {"fillColor": HM_PRIMARY, "color": HM_PRIMARY_DARK, "weight": 1, "fillOpacity": 0.18}

    def highlight_fn(_):
        return {"weight": 3, "fillOpacity": 0.28}

    folium.GeoJson(
        gdf.to_json(),
        name="Barrios",
        style_function=style_fn,
        highlight_function=highlight_fn,
        tooltip=folium.GeoJsonTooltip(fields=["barrio_name"], aliases=["Barrio:"]),
    ).add_to(m)

    return st_folium(m, height=520, width=None)


def main():
    inject_branding()
    init_state()
    header()
    stepper()

    st.markdown('<div class="hm-card">', unsafe_allow_html=True)

    try:
        barrios_gdf = load_barrios_geojson()
    except Exception:
        barrios_gdf = None

    step = st.session_state.step

    if step == 0:
        st.subheader("Primero, lo básico 🙂")
        st.session_state.nombre = st.text_input("Nombre y apellido", value=st.session_state.nombre)
        st.session_state.telefono_raw = st.text_input("WhatsApp (con lada)", value=st.session_state.telefono_raw, placeholder="+34 6XXXXXXXX")
        st.session_state.edad = st.number_input("Edad", min_value=16, max_value=99, value=int(st.session_state.edad))
        nav_buttons(can_back=False)

    elif step == 1:
        st.subheader("Sobre ti")
        st.session_state.genero = st.selectbox("Género", ["", "Hombre", "Mujer", "Otro", "Prefiero no decir"])
        st.session_state.pref_genero = st.selectbox("¿Con quién quieres vivir?", ["", "Solo hombres", "Solo mujeres", "Mixto", "Me da igual"])
        nav_buttons()

    elif step == 2:
        st.subheader("Idioma")
        st.session_state.idioma = st.radio("¿En qué idioma prefieres que te hablemos?", ["Español", "English"], horizontal=True)
        nav_buttons()

    elif step == 3:
        st.subheader("¿En qué barrios te gustaría vivir?")
        if barrios_gdf is None:
            st.warning("Sube el archivo data/madrid_barrios.geojson para activar el mapa.")
        else:
            out = render_map(barrios_gdf)
            if out and out.get("last_clicked"):
                lat = out["last_clicked"]["lat"]
                lon = out["last_clicked"]["lng"]
                barrio = barrio_from_click(barrios_gdf, lat, lon)
                if barrio:
                    if barrio in st.session_state.zonas_selected:
                        st.session_state.zonas_selected.remove(barrio)
                    else:
                        st.session_state.zonas_selected.append(barrio)

            if st.session_state.zonas_selected:
                pills = " ".join([f"<span class='hm-pill'>{z}</span>" for z in st.session_state.zonas_selected])
                st.markdown("**Seleccionados:**", unsafe_allow_html=True)
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.info("Selecciona uno o varios barrios en el mapa.")

            if st.button("No estoy seguro, recomiéndame"):
                st.session_state.zonas_selected = ["—"]
                st.rerun()

        nav_buttons()

    elif step == 4:
        st.subheader("Presupuesto mensual 💸")
        st.session_state.budget = st.number_input("Budget (€)", min_value=200, max_value=20000, value=int(st.session_state.budget), step=50)
        nav_buttons()

    elif step == 5:
        st.subheader("Fechas")
        st.session_state.inicio = st.date_input("Inicio", value=st.session_state.inicio)
        st.session_state.fin = st.date_input("Fin", value=st.session_state.fin)
        if st.session_state.fin < st.session_state.inicio:
            st.error("La fecha fin no puede ser antes que la fecha inicio.")
            nav_buttons(can_next=False)
        else:
            nav_buttons()

    elif step == 6:
        st.subheader("Convivencia")
        st.session_state.max_compartir_con = st.slider("Máximo de personas para compartir", 1, 6, int(st.session_state.max_compartir_con))
        st.session_state.banos_min = st.radio("Baños mínimos", [1, 2, 3, 4], horizontal=True)
        nav_buttons()

    elif step == 7:
        st.subheader("Notas ✍️")
        st.session_state.notas = st.text_area("Notas / comentarios", value=st.session_state.notas, height=120)
        nav_buttons(next_label="Ver mi Match")

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

            score, breakdown = calc_score({
                **excel_row,
                "inicio": st.session_state.inicio,
                "fin": st.session_state.fin,
            })

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
                "score_breakdown": str(breakdown),
            }
            upsert_store(store_row)
            st.success("Guardado ✅ (sin duplicados).")

            df_store = load_store()
            export_cols = [
                "nombre", "telefono", "edad", "genero", "pref_genero", "idioma", "zona",
                "budget", "inicio", "fin", "max_compartir_con", "banos_min", "notas"
            ]
            df_export = df_store[export_cols].copy() if all(c in df_store.columns for c in export_cols) else pd.DataFrame([excel_row])

            st.download_button(
                "⬇️ Descargar Excel (leads)",
                data=export_xlsx(df_export),
                file_name="hausmate_match_leads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

            if st.button("➕ Nuevo registro", use_container_width=True):
                for k in ["nombre", "telefono_raw", "edad", "genero", "pref_genero", "idioma", "budget", "inicio", "fin", "max_compartir_con", "banos_min", "notas"]:
                    if k in st.session_state:
                        if k in ["edad", "budget", "max_compartir_con", "banos_min"]:
                            continue
                        st.session_state[k] = "" if isinstance(st.session_state[k], str) else None
                st.session_state.zonas_selected = []
                st.session_state.step = 0
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
