/**
 * Users HTTP service.
 */

import { apiClient } from "$lib/shared/api/client";
import type { UpdateProfileDto, User } from "../types";

export const usersService = {
	getMe: () => apiClient.get<User>("/v1/users/me").then((r) => r.data),

	updateProfile: (data: UpdateProfileDto) =>
		apiClient.patch<User>("/v1/users/me", data).then((r) => r.data),

	getById: (id: string) => apiClient.get<User>(`/v1/users/${id}`).then((r) => r.data),
};
