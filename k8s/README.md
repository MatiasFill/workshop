# Kubernetes

Este diretório contém uma versão do projeto em Kubernetes para o mesmo stack do Compose:

- PostgreSQL
- Redis
- Backend FastAPI
- Frontend Vite

## Build e push das imagens

Antes de aplicar os manifests, gere e publique as imagens no seu registry:

```bash
docker build -t your-registry/oficina-ai-backend:latest ./backend
docker build -t your-registry/oficina-ai-frontend:latest ./frontend
docker push your-registry/oficina-ai-backend:latest
docker push your-registry/oficina-ai-frontend:latest
```

Depois ajuste os valores em `backend.yaml` e `frontend.yaml` para o registry correto.

## Aplicar no cluster

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

## Verificar

```bash
kubectl get pods -n oficina-ai
kubectl get svc -n oficina-ai
kubectl logs -n oficina-ai deploy/backend
kubectl logs -n oficina-ai deploy/frontend
```

Se o cluster tiver o Ingress Controller do NGINX habilitado, o app passa a ficar em `http://oficina.local/`.
