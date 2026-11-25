# Kubearc Notes

Starter app for the **Kubernetes for DevOps** course (Kubearc Academy). A small Flask app with Postgres
that every session builds on: image (S10) → Helm chart (S11) → GitHub Actions (S12) → Argo CD (S13) →
HPA and scheduling (S14) → security (S15) → monitoring (S16) → EKS (S17) → demo day (S18).

## Endpoints

| Path | What |
| --- | --- |
| `/` | Web page: list and add notes |
| `/api/notes` | Notes as JSON, plus env, version and Pod name |
| `POST /notes` | Add a note (`{"text": "…"}` or form field `text`) |
| `/healthz` | Liveness: the process answers (never checks the DB) |
| `/readyz` | Readiness: 200 only if the database answers |
| `/metrics` | Prometheus metrics: `notes_http_requests_total`, `notes_http_request_seconds`, `notes_created_total` |

## Settings (environment)

`APP_ENV`, `APP_TITLE`, `APP_VERSION`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
Without `DB_HOST` notes are kept in memory, so the image runs anywhere.

## Run it

```bash
docker build -t kubearc-notes:1.0.0 .
docker run --rm -p 8080:8080 kubearc-notes:1.0.0
curl localhost:8080/healthz
```

Tests: `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt && pytest -q`

## Deploy

- Plain manifests (S10): set your image in `k8s/30-app.yaml`, then `kubectl apply -f k8s/`
- Helm (S11+): set `image.repository` in `helm/kubearc-notes/values.yaml`, then
  `helm install notes-dev ./helm/kubearc-notes -n notes-dev --create-namespace`
- CI/CD (S12): `.github/workflows/ci-cd.yaml`
- GitOps (S13): `argocd/notes-dev.yaml`, `argocd/notes-prod.yaml`

Replace `YOU` with your GitHub user name (lower case) everywhere.
