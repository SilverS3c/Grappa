pre-requirements:
```
minikube
```

Install Metallb:

```
helm repo add metallb https://metallb.github.io/metallb
helm install --create-namespace -n metallb metallb metallb/metallb
```
Configure Metallb LoadBalancer IP range (Allocate an ip range(virsh), and apply config file)

Install Traefik:
```
helm repo add traefik https://traefik.github.io/charts
helm repo update
kubectl create ns traefik-v2
helm install --namespace=traefik-v2 traefik traefik/traefik
```
Dashboard:
```
kubectl port-forward $(kubectl get pods --selector "app.kubernetes.io/name=traefik" --output=name) 9000:9000
```