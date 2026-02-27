import { Card } from "./ui/card";

interface MadridMapProps {
  title: string;
  body: string;
}

export function MadridMap({ title, body }: MadridMapProps) {
  return (
    <Card className="map-card">
      <div className="map-header">
        <p className="kicker">Madrid</p>
        <h3 className="section-title" style={{ marginTop: "0.45rem" }}>
          {title}
        </h3>
        <p className="section-copy" style={{ marginTop: "0.55rem" }}>
          {body}
        </p>
      </div>
      <div className="map-frame">
        <div className="map-inner">
          <iframe
            className="map-iframe"
            loading="lazy"
            src="https://www.openstreetmap.org/export/embed.html?bbox=-3.9148%2C40.3121%2C-3.5422%2C40.5639&layer=mapnik&marker=40.4168%2C-3.7038"
            title="Madrid map"
          />
        </div>
      </div>
    </Card>
  );
}
