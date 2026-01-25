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

	const payload = await response.text();
	let data: ApiResponse<T>;
	try {
		data = JSON.parse(payload) as ApiResponse<T>;
	} catch {
		const statusLabel = response.ok ? "ok" : `status ${response.status}`;
		throw new Error(`API returned non-JSON response (${statusLabel}).`);
	}
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
