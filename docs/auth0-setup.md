# Auth0 setup

forgetme uses Auth0 to protect the API (access tokens, RS256) and to log users into the UI ([ADR 0010](adr/0010-auth0-authentication.md)).

## 1. API

*Applications → APIs → Create API*
- Identifier (audience): e.g. `https://api.forgetme.example` → `AUTH0_AUDIENCE`
- Enable **RBAC** and **Add Permissions in the Access Token**.
- Add permissions `forget:read` and `forget:write`.

## 2. Single Page Application

*Applications → Create Application → Single Page Web Applications*
- Allowed Callback URLs, Logout URLs, Web Origins: `http://localhost:5173`
- Copy the Client ID → `VITE_AUTH0_CLIENT_ID` (frontend), and your tenant domain → `AUTH0_DOMAIN` / `VITE_AUTH0_DOMAIN`.

## 3. Roles

Create roles (e.g. *Viewer* = `forget:read`, *Operator* = `forget:read` + `forget:write`) and assign them to users.

## Configuration

| Variable | Where | Example |
|---|---|---|
| `AUTH0_DOMAIN` | backend `.env` | `your-tenant.eu.auth0.com` |
| `AUTH0_AUDIENCE` | backend `.env` | `https://api.forgetme.example` |
| `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID`, `VITE_AUTH0_AUDIENCE` | `frontend/.env` | see `frontend/.env.example` |

The backend refuses to start without `AUTH0_DOMAIN` and `AUTH0_AUDIENCE`. There is deliberately no switch to disable authentication.
