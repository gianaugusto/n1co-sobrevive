import { Auth0Provider } from "@auth0/auth0-react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { config } from "./config";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Auth0Provider
      domain={config.auth0Domain()}
      clientId={config.auth0ClientId()}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: config.auth0Audience(),
        scope: "openid profile email",
      }}
      cacheLocation="memory"
    >
      <App />
    </Auth0Provider>
  </StrictMode>,
);
