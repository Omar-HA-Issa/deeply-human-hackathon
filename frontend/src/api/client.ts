export const apiBaseUrl = "http://localhost:8000";

type ApiResponse<T> = {
	ok: boolean;
	error?: string;
} & T;

async function requestJson<T>(path: string, options: RequestInit = {}) {
	const response = await fetch(`${apiBaseUrl}${path}`, {
		credentials: "include",
		headers: {
			"Content-Type": "application/json",
			...(options.headers ?? {}),
		},
		...options,
	});

	const data = (await response.json()) as ApiResponse<T>;
	if (!response.ok || data.ok === false) {
		throw new Error(data.error || "Request failed");
	}
	return data;
}

export function getJson<T>(path: string) {
	return requestJson<T>(path, { method: "GET" });
}

export function postJson<T>(path: string, body?: Record<string, unknown>) {
	return requestJson<T>(path, {
		method: "POST",
		body: body ? JSON.stringify(body) : undefined,
	});
}
