export class ApiConnectionError extends Error {
  path?: string;

  constructor(path?: string) {
    super("Backend connection unavailable. Demo data may be incomplete.");
    this.name = "ApiConnectionError";
    this.path = path;
  }
}

export function safeApiMessage(error: unknown): string {
  if (error instanceof ApiConnectionError) {
    return error.message;
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return "Unable to load this clinical operations view.";
}
