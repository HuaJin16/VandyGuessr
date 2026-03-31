/**
 * Client-side GPS check before upload (server still validates).
 */

import exifr from "exifr";

import type { UploadFilePreflightResult } from "./types";

export const MISSING_GPS_MESSAGE =
	"This photo doesn't include embedded location data. Use your camera with location turned on—screenshots and some edited photos won't work.";

export const ALLOWED_UPLOAD_EXTENSIONS = [".jpg", ".jpeg", ".png", ".heic"] as const;
const allowedUploadExtensionSet = new Set<string>(ALLOWED_UPLOAD_EXTENSIONS);

const EXIF_SLICE_BYTES = 512 * 1024;

function getFileExtension(filename: string): string {
	if (!filename.includes(".")) return "";
	return `.${filename.split(".").pop()?.toLowerCase() ?? ""}`;
}

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

export async function preflightUploadFile(file: File): Promise<UploadFilePreflightResult> {
	if (!allowedUploadExtensionSet.has(getFileExtension(file.name))) {
		return {
			preflightOk: false,
			preflightError: "Use a JPEG, PNG, or HEIC photo.",
		};
	}

	try {
		const ok = await fileHasGpsExif(file);
		return {
			preflightOk: ok,
			preflightError: ok ? "" : MISSING_GPS_MESSAGE,
		};
	} catch {
		return {
			preflightOk: false,
			preflightError: "Could not read this file. Try another photo.",
		};
	}
}

export function mapServerUploadError(detail: string | undefined): string {
	if (!detail) return "Upload failed.";
	if (detail.includes("missing GPS EXIF")) return MISSING_GPS_MESSAGE;
	return detail;
}
