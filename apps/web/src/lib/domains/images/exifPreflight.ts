/**
 * Client-side GPS check before upload (server still validates).
 */

import exifr from "exifr";

import type { UploadFilePreflightResult } from "./types";

export const MISSING_GPS_MESSAGE =
	"This photo doesn't include embedded location data. Use your camera with location turned on—screenshots and some edited photos won't work.";

export const FILE_TOO_LARGE_MESSAGE = "This photo is too large. Use a file under 50MB.";

export const PANORAMA_TOO_LARGE_MESSAGE =
	"This panorama is too large to process. Export a smaller image and try again.";

export const ALLOWED_UPLOAD_EXTENSIONS = [".jpg", ".jpeg", ".png", ".heic"] as const;
const allowedUploadExtensionSet = new Set<string>(ALLOWED_UPLOAD_EXTENSIONS);

const EXIF_SLICE_BYTES = 512 * 1024;
const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;
const MAX_UPLOAD_DIMENSION = 17000;
const MAX_UPLOAD_PIXELS = 70_000_000;
const MAX_PROJECTED_FULL_WIDTH = 17000;

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

async function readImageDimensions(file: File): Promise<{ width: number; height: number } | null> {
	const objectUrl = URL.createObjectURL(file);
	const image = new Image();

	try {
		const result = await new Promise<{ width: number; height: number } | null>((resolve) => {
			image.onload = () => {
				resolve({
					width: image.naturalWidth,
					height: image.naturalHeight,
				});
			};
			image.onerror = () => resolve(null);
			image.src = objectUrl;
		});
		return result;
	} finally {
		URL.revokeObjectURL(objectUrl);
	}
}

async function imageGeometryError(file: File): Promise<string | null> {
	const dimensions = await readImageDimensions(file);
	if (!dimensions) return null;

	const { width, height } = dimensions;
	if (Math.max(width, height) > MAX_UPLOAD_DIMENSION) {
		return PANORAMA_TOO_LARGE_MESSAGE;
	}
	if (width * height > MAX_UPLOAD_PIXELS) {
		return PANORAMA_TOO_LARGE_MESSAGE;
	}
	if (Math.max(width, height * 2) > MAX_PROJECTED_FULL_WIDTH) {
		return PANORAMA_TOO_LARGE_MESSAGE;
	}

	return null;
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

	if (file.size > MAX_UPLOAD_BYTES) {
		return {
			preflightOk: false,
			preflightError: FILE_TOO_LARGE_MESSAGE,
		};
	}

	const geometryError = await imageGeometryError(file);
	if (geometryError) {
		return {
			preflightOk: false,
			preflightError: geometryError,
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
	if (detail.includes("File exceeds maximum size")) return FILE_TOO_LARGE_MESSAGE;
	if (detail.includes("Image dimensions exceed")) return PANORAMA_TOO_LARGE_MESSAGE;
	if (detail.includes("Image resolution exceeds")) return PANORAMA_TOO_LARGE_MESSAGE;
	if (detail.includes("Panorama projection exceeds")) return PANORAMA_TOO_LARGE_MESSAGE;
	return detail;
}
