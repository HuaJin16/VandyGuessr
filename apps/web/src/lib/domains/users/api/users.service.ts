/**
 * Users HTTP service.
 */

import { apiClient } from "$lib/shared/api/client";
import type { UpdateProfileRequest, User } from "../types";

export const usersService = {
	getMe: () => apiClient.get<User>("/v1/users/me").then((r) => r.data),

	updateProfile: (data: UpdateProfileRequest) =>
		apiClient.patch<User>("/v1/users/me", data).then((r) => r.data),
};
