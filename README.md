# FastAPI ACL + JWT (API Keys)

FastAPI app with:

- **JWT auth** (Bearer tokens)
- **API keys as JWTs** (minted tokens with a `jti` tracked in DB for revocation)
- **ACL** via **Users → Roles → Permissions**

## Quickstart

### 1) Install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure

Copy `.env.example` to `.env` and adjust as needed (or export env vars in your shell).

### 3) Run

```bash
uvicorn app.main:app --reload
```

API docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Bootstrapping an admin user

If there are **no users** yet, create the first admin:

```bash
curl -X POST http://127.0.0.1:8000/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change-me"}'
```

Then login:

```bash
curl -X POST http://127.0.0.1:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=change-me"
```

Use the returned `access_token` as:

```bash
curl http://127.0.0.1:8000/items \
  -H "Authorization: Bearer <TOKEN>"
```

## Default roles/permissions

On startup the app seeds:

- Roles: `admin`, `user`
- Permissions: `admin:manage`, `items:read`, `items:write`

`admin` gets all permissions. `user` gets `items:read`.

