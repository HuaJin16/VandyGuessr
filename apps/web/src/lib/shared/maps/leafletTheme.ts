import L from "leaflet";

export const CAMPUS_CENTER: L.LatLngExpression = [36.1435, -86.8034];
export const CAMPUS_ZOOM = 16;
export const CAMPUS_BOUNDS: L.LatLngBoundsExpression = [
	[36.05, -86.92],
	[36.25, -86.7],
];

const mapTileUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

const mapTileOptions: L.TileLayerOptions = {
	maxZoom: 19,
};

export function addCampusBaseLayer(map: L.Map) {
	return L.tileLayer(mapTileUrl, mapTileOptions).addTo(map);
}
