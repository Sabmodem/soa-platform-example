# Service Oriented Platform - Agent Instructions

## Quickstart

```bash
docker compose -f ./docker-compose.core.yml up -d
docker compose -f ./docker-compose.services.yml up -d
```

Access: `http://localhost:80`
Test credentials: `abc:abc` (has access), `bca:bca` (no access)

## Architecture

- **Gateway**: OpenResty nginx at port 80
- **Auth**: Keycloak (port 8080) + OPA (port 8181) + PostgreSQL
- **Frontend**: Vue 3 + Vuetify with Module Federation (main-ui)
- **Services**: filestorage (FastAPI backend + Vue frontend)

## Development Commands

### Frontend (main-ui or filestorage-ui)
```bash
cd core/main-ui           # or services/filestorage/filestorage-ui
npm install
npm run dev              # Vite dev server
npm run build            # Production build
npm run lint             # ESLint fix
```

### API (filestorage-api)
```bash
cd services/filestorage/filestorage-api
# Uses FastAPI with uvicorn
```

### Full stack
```bash
docker compose -f ./docker-compose.core.yml up -d
docker compose -f ./docker-compose.services.yml up -d
```

### Stop all
```bash
docker compose -f ./docker-compose.core.yml down
docker compose -f ./docker-compose.services.yml down
```

## Key Conventions

- Module federation loads service UIs into main-ui at runtime
- OPA enforces all API authorization (no client-side route protection in test version)
- Nginx config mounted from `core/nginx/` and service nginx dirs
- OPA policies at `core/opa/policies/authz.rego`
- Keycloak realm imported from `realm-export.json`

## Security Notes

- No client-side route protection in test version (API protected by OPA only)
- Use `abc:abc` account for testing filestorage service
- OPA checks token validity, expiration, and role-based access per path
