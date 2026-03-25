/**
 * Image / moderation query definitions.
 */

import { imagesService } from "../api/images.service";

export const imageQueries = {
	pendingModeration: () => ({
		queryKey: ["images", "moderation", "pending"] as const,
		queryFn: () => imagesService.listPendingModeration(),
	}),
	tour: (environment: "any" | "indoor" | "outdoor") => ({
		queryKey: ["images", "tour", environment] as const,
		queryFn: () => imagesService.listTour(environment),
	}),
};
