import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { districtGroups } from "../lib/content";

interface MadridDistrictMapProps {
  selectedDistricts: string[];
  onToggleDistrict: (district: string) => void;
  title: string;
  body: string;
}

type LatLng = [number, number];

const districtPolygons: Record<string, LatLng[]> = {
  "Fuencarral-El Pardo": [
    [40.523, -3.836],
    [40.523, -3.72],
    [40.576, -3.72],
    [40.576, -3.836],
  ],
  Tetuán: [
    [40.452, -3.714],
    [40.452, -3.671],
    [40.476, -3.671],
    [40.476, -3.714],
  ],
  Chamberí: [
    [40.425, -3.714],
    [40.425, -3.671],
    [40.451, -3.671],
    [40.451, -3.714],
  ],
  Chamartín: [
    [40.452, -3.67],
    [40.452, -3.618],
    [40.492, -3.618],
    [40.492, -3.67],
  ],
  Centro: [
    [40.405, -3.714],
    [40.405, -3.682],
    [40.429, -3.682],
    [40.429, -3.714],
  ],
  Salamanca: [
    [40.424, -3.681],
    [40.424, -3.64],
    [40.457, -3.64],
    [40.457, -3.681],
  ],
  Retiro: [
    [40.402, -3.681],
    [40.402, -3.642],
    [40.423, -3.642],
    [40.423, -3.681],
  ],
  Arganzuela: [
    [40.374, -3.714],
    [40.374, -3.668],
    [40.404, -3.668],
    [40.404, -3.714],
  ],
  "Moncloa-Aravaca": [
    [40.43, -3.796],
    [40.43, -3.715],
    [40.505, -3.715],
    [40.505, -3.796],
  ],
  Latina: [
    [40.372, -3.793],
    [40.372, -3.715],
    [40.429, -3.715],
    [40.429, -3.793],
  ],
  Carabanchel: [
    [40.343, -3.759],
    [40.343, -3.695],
    [40.371, -3.695],
    [40.371, -3.759],
  ],
  Usera: [
    [40.36, -3.694],
    [40.36, -3.648],
    [40.39, -3.648],
    [40.39, -3.694],
  ],
  "Puente de Vallecas": [
    [40.371, -3.647],
    [40.371, -3.594],
    [40.406, -3.594],
    [40.406, -3.647],
  ],
  Moratalaz: [
    [40.392, -3.641],
    [40.392, -3.603],
    [40.424, -3.603],
    [40.424, -3.641],
  ],
  "Ciudad Lineal": [
    [40.423, -3.639],
    [40.423, -3.566],
    [40.474, -3.566],
    [40.474, -3.639],
  ],
  Hortaleza: [
    [40.474, -3.669],
    [40.474, -3.567],
    [40.535, -3.567],
    [40.535, -3.669],
  ],
  Villaverde: [
    [40.321, -3.731],
    [40.321, -3.669],
    [40.359, -3.669],
    [40.359, -3.731],
  ],
  "Villa de Vallecas": [
    [40.33, -3.669],
    [40.33, -3.545],
    [40.392, -3.545],
    [40.392, -3.669],
  ],
  Vicálvaro: [
    [40.37, -3.603],
    [40.37, -3.531],
    [40.424, -3.531],
    [40.424, -3.603],
  ],
  "San Blas-Canillejas": [
    [40.423, -3.565],
    [40.423, -3.492],
    [40.487, -3.492],
    [40.487, -3.565],
  ],
  Barajas: [
    [40.47, -3.611],
    [40.47, -3.485],
    [40.556, -3.485],
    [40.556, -3.611],
  ],
  Otros: [
    [40.318, -3.818],
    [40.318, -3.742],
    [40.37, -3.742],
    [40.37, -3.818],
  ],
};

const DISTRICT_GEOJSON_URL =
  "https://sigma.madrid.es/hosted/rest/services/CARTOGRAFIA/LIMITES_ADMINISTRATIVOS/MapServer/26/query?where=1%3D1&outFields=COD_DIS_TX%2CNOMBRE&returnGeometry=true&outSR=4326&f=geojson";

type GeoJsonFeature = GeoJSON.Feature<
  GeoJSON.Polygon | GeoJSON.MultiPolygon,
  { NOMBRE?: string; COD_DIS_TX?: string }
>;

type GeoJsonCollection = GeoJSON.FeatureCollection<
  GeoJSON.Polygon | GeoJSON.MultiPolygon,
  { NOMBRE?: string; COD_DIS_TX?: string }
>;

const groupColors: Record<string, string> = {
  central: "#d8f0f2",
  north: "#dfeef9",
  east: "#f7ead2",
  south: "#f8dede",
  west: "#e8e0f7",
};

const groupBorders: Record<string, string> = {
  central: "#5baeb6",
  north: "#739fd1",
  east: "#c99c41",
  south: "#d36f6f",
  west: "#8f79c2",
};

const districtToGroup = Object.fromEntries(
  districtGroups.flatMap((group) =>
    group.districts.map((district) => [district, group.key]),
  ),
) as Record<string, string>;

function normalizeKey(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, " ")
    .trim()
    .toUpperCase();
}

const districtNameMap = Object.fromEntries(
  [
    "Centro",
    "Arganzuela",
    "Retiro",
    "Salamanca",
    "Chamartín",
    "Tetuán",
    "Chamberí",
    "Fuencarral-El Pardo",
    "Moncloa-Aravaca",
    "Latina",
    "Carabanchel",
    "Usera",
    "Puente de Vallecas",
    "Moratalaz",
    "Ciudad Lineal",
    "Hortaleza",
    "Villaverde",
    "Villa de Vallecas",
    "Vicálvaro",
    "San Blas-Canillejas",
    "Barajas",
  ].map((district) => [normalizeKey(district), district]),
) as Record<string, string>;

function normalizeDistrictName(name?: string) {
  if (!name) return "";
  const trimmed = name.trim();
  return districtNameMap[normalizeKey(trimmed)] ?? trimmed;
}

export function MadridDistrictMap({
  selectedDistricts,
  onToggleDistrict,
  title,
  body,
}: MadridDistrictMapProps) {
  const [geoJsonData, setGeoJsonData] = useState<GeoJsonCollection | null>(null);
  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const defaultLayerRef = useRef<L.LayerGroup | null>(null);
  const selectedLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    let active = true;

    fetch(DISTRICT_GEOJSON_URL)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`GeoJSON request failed: ${response.status}`);
        }
        return response.json() as Promise<GeoJsonCollection>;
      })
      .then((data) => {
        if (active) {
          setGeoJsonData(data);
        }
      })
      .catch(() => {
        if (active) {
          setGeoJsonData(null);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!mapElementRef.current || mapRef.current) return;

    const map = L.map(mapElementRef.current, {
      center: [40.4168, -3.7038],
      zoom: 10,
      scrollWheelZoom: true,
      zoomControl: true,
      minZoom: 10,
      maxZoom: 14,
      maxBounds: [
        [40.25, -3.95],
        [40.67, -3.35],
      ],
      maxBoundsViscosity: 1,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", {
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);

    map.fitBounds(
      [
        [40.29, -3.90],
        [40.61, -3.47],
      ],
      { padding: [20, 20] },
    );

    mapRef.current = map;
    defaultLayerRef.current = L.layerGroup().addTo(map);
    selectedLayerRef.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
      defaultLayerRef.current = null;
      selectedLayerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const defaultLayer = defaultLayerRef.current;
    const selectedLayer = selectedLayerRef.current;
    if (!map || !defaultLayer || !selectedLayer) return;

    defaultLayer.clearLayers();
    selectedLayer.clearLayers();

    const getStyle = (district: string, selected: boolean) => {
      const groupKey = districtToGroup[district] ?? "central";
      return {
        color: selected ? "#0f172a" : groupBorders[groupKey],
        fillColor: groupColors[groupKey],
        fillOpacity: selected ? 0.88 : 0.62,
        opacity: selected ? 1 : 0.95,
        weight: selected ? 3.25 : 2.1,
      };
    };

    const bindDistrictLayer = (layer: L.Layer, district: string, selected: boolean) => {
      if (!("bindTooltip" in layer) || !("on" in layer)) return;

      (layer as L.Path).bindTooltip(district, {
        permanent: true,
        direction: "center",
        className: selected
          ? "district-map-tooltip district-map-tooltip-selected"
          : "district-map-tooltip",
      });

      (layer as L.Path).on("click", () => onToggleDistrict(district));
    };

    if (geoJsonData) {
      const buildLayer = (selected: boolean) =>
        L.geoJSON(geoJsonData as GeoJSON.GeoJsonObject, {
          filter: (feature) => {
            const district = normalizeDistrictName(
              (feature as GeoJsonFeature).properties?.NOMBRE,
            );
            return Boolean(district) && selectedDistricts.includes(district) === selected;
          },
          style: (feature) => {
            const district = normalizeDistrictName(
              (feature as GeoJsonFeature).properties?.NOMBRE,
            );
            return getStyle(district, selected);
          },
          onEachFeature: (feature, layer) => {
            const district = normalizeDistrictName(
              (feature as GeoJsonFeature).properties?.NOMBRE,
            );
            if (!district) return;

            bindDistrictLayer(layer, district, selected);
          },
        });

      buildLayer(false).addTo(defaultLayer);
      buildLayer(true).addTo(selectedLayer);
      return;
    }

    Object.entries(districtPolygons).forEach(([district, points]) => {
      const selected = selectedDistricts.includes(district);
      const polygon = L.polygon(points, getStyle(district, selected));

      bindDistrictLayer(polygon, district, selected);
      polygon.addTo(selected ? selectedLayer : defaultLayer);
    });
  }, [geoJsonData, onToggleDistrict, selectedDistricts]);

  return (
    <div className="district-map-card">
      <div className="district-map-header">
        <h4 className="district-map-title">{title}</h4>
        <p className="district-map-copy">{body}</p>
      </div>
      <div className="district-map-shell district-map-leaflet-shell">
        <div className="district-map-leaflet" ref={mapElementRef} />
      </div>
    </div>
  );
}
