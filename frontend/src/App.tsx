import { useAuth0 } from "@auth0/auth0-react";
import { useMemo } from "react";
import { createApiClient } from "./api/client";
import { config } from "./config";
import { Dashboard } from "./Dashboard";

export function App() {
  const { isAuthenticated, isLoading, loginWithRedirect, logout, getAccessTokenSilently, user } =
    useAuth0();

  const api = useMemo(
    () =>
      createApiClient(async () => {
        const token = await getAccessTokenSilently();
        if (!token) throw new Error("No access token available");
        return token;
      }, config.apiUrl),
    [getAccessTokenSilently],
  );

  return (
    <div className="mx-auto max-w-6xl p-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold">forgetme</h1>
        {isAuthenticated && (
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">{user?.email}</span>
            <button
              className="rounded border border-slate-300 px-3 py-1"
              onClick={() => void logout({ logoutParams: { returnTo: window.location.origin } })}
            >
              Log out
            </button>
          </div>
        )}
      </header>
      {isLoading ? (
        <p>Loading…</p>
      ) : isAuthenticated ? (
        <Dashboard api={api} />
      ) : (
        <button
          className="rounded bg-slate-900 px-4 py-2 text-white"
          onClick={() => void loginWithRedirect()}
        >
          Log in
        </button>
      )}
    </div>
  );
}
