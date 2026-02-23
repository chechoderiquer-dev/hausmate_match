import os
from pathlib import Path
from urllib.request import urlretrieve

MADRID_BARRIOS_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/madrid.geojson"

def ensure_barrios_geojson(local_path: str = "data/madrid_barrios.geojson"):
    """
    If local GeoJSON does not exist, download it from a public source.
    This avoids needing to download anything on the user's laptop.
    """
    p = Path(local_path)
    p.parent.mkdir(parents=True, exist_ok=True)  # create data/ if missing

    if not p.exists():
        urlretrieve(MADRID_BARRIOS_URL, str(p))

@st.cache_data
def load_barrios_geojson(path="data/madrid_barrios.geojson") -> gpd.GeoDataFrame:
    ensure_barrios_geojson(path)

    gdf = gpd.read_file(path)

    # Ensure CRS is WGS84
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Normalize the barrio name column
    # Click-that-hood uses "name" in properties
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

    if name_col and name_col != "barrio_name":
        gdf = gdf.rename(columns={name_col: "barrio_name"})

    if "barrio_name" not in gdf.columns:
        gdf["barrio_name"] = "Barrio"

    gdf["barrio_name"] = gdf["barrio_name"].astype(str)
    return gdf
