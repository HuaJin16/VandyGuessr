/**
 * Client-side GPS check before upload (server still validates).
 */

import exifr from "exifr";

export const MISSING_GPS_MESSAGE =
	"This photo doesn't include embedded location data. Use your camera with location turned on—screenshots and some edited photos won't work.";

const EXIF_SLICE_BYTES = 512 * 1024;

function hasLatLng(gps: unknown): gps is { latitude: number; longitude: number } {
	if (!gps || typeof gps !== "object") return false;
	const lat = (gps as { latitude?: unknown }).latitude;
	const lng = (gps as { longitude?: unknown }).longitude;
	return (
		typeof lat === "number" &&
		typeof lng === "number" &&
		Number.isFinite(lat) &&
		Number.isFinite(lng)
	);
}

export async function fileHasGpsExif(file: File): Promise<boolean> {
	const head = file.slice(0, Math.min(file.size, EXIF_SLICE_BYTES));
	let buf = await head.arrayBuffer();
	let gps = await exifr.gps(buf);
	if (hasLatLng(gps)) return true;

	if (file.size > EXIF_SLICE_BYTES) {
		buf = await file.arrayBuffer();
		gps = await exifr.gps(buf);
		return hasLatLng(gps);
	}

	return false;
}

export function mapServerUploadError(detail: string | undefined): string {
	if (!detail) return "Upload failed.";
	if (detail.includes("missing GPS EXIF")) return MISSING_GPS_MESSAGE;
	return detail;
}
