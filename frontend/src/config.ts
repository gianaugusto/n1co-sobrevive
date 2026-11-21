function required(name: string): string {
  const value = import.meta.env[name] as string | undefined;
  if (!value) throw new Error(`Missing environment variable ${name} (see frontend/.env.example)`);
  return value;
}

export const config = {
  apiUrl: (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000",
  auth0Domain: () => required("VITE_AUTH0_DOMAIN"),
  auth0ClientId: () => required("VITE_AUTH0_CLIENT_ID"),
  auth0Audience: () => required("VITE_AUTH0_AUDIENCE"),
};
