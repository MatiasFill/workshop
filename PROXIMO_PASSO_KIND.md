# Próximo passo: Kind + Helm

## Objetivo

Validar o deploy do projeto Oficina AI em um cluster Kubernetes local com Kind antes de adaptar para um ambiente real de cloud.

## Escopo

- manter o Helm já criado em `helm/oficina-ai`
- preparar configuração específica para Kind
- instalar o Ingress Controller do NGINX no cluster Kind
- aplicar o chart e validar os serviços
- verificar conectividade do backend com PostgreSQL e Redis
- confirmar acesso ao frontend e backend via localhost

## Tarefas planejadas

### 1. Preparar ambiente Kind

- instalar `kind`
- criar cluster local
- confirmar kubeconfig
- verificar `kubectl get nodes`

### 2. Preparar chart para Kind

- criar `values-kind.yaml`
- ajustar ingress para NodePort ou host local
- garantir que imagens estejam disponíveis localmente ou via registry local
- confirmar uso de `LoadBalancer` ou `NodePort`

### 3. Instalar ingress

- aplicar o manifesto do NGINX Ingress Controller
- confirmar que o ingress está pronto

### 4. Deploy da aplicação

```bash
helm upgrade --install oficina-ai ./helm/oficina-ai -n oficina-ai --create-namespace -f helm/oficina-ai/values-kind.yaml
```

### 5. Validar a aplicação

- `kubectl get pods -n oficina-ai`
- `kubectl get svc -n oficina-ai`
- `kubectl logs -n oficina-ai deploy/backend`
- `kubectl logs -n oficina-ai deploy/frontend`
- testar `/api/health`
- testar login e acesso ao frontend

## Observações

- O melhor ambiente para validar primeiro é Kind, porque é mais rápido e reproduz bem a estrutura de Kubernetes.
- Depois disso, o próximo ajuste será para um cluster real, como AKS, EKS ou GKE.
- O Helm atual já está em bom estado base para esse passo.

## Arquivos relacionados

- [RELATORIO_MUDANCAS.md](./RELATORIO_MUDANCAS.md)
- [helm/oficina-ai](./helm/oficina-ai)
- [k8s](./k8s)
