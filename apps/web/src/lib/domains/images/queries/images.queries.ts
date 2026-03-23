/**
 * Image / moderation query definitions.
 */

import { imagesService } from "../api/images.service";

export const imageQueries = {
	pendingModeration: () => ({
		queryKey: ["images", "moderation", "pending"] as const,
		queryFn: () => imagesService.listPendingModeration(),
	}),
};
