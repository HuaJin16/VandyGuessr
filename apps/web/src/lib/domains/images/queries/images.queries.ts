/**
 * Image / moderation query definitions.
 */

import { imagesService } from "../api/images.service";
import type { TourEnvironment } from "../types";

export const imageQueries = {
	pendingModeration: () => ({
		queryKey: ["images", "moderation", "pending"] as const,
		queryFn: () => imagesService.listPendingModeration(),
	}),
	tour: (environment: TourEnvironment) => ({
		queryKey: ["images", "tour", environment] as const,
		queryFn: () => imagesService.listTour(environment),
	}),
};
