# Ingress Nginx - Ingress Controller
To utilized Ingress inbound, you will need an ingress controller. For this, we'll use ingress-nginx instead of
Traefik.

>(REFERENCE: [https://github.com/kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx))

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Install Nginx as the Ingress controller
To install the Nginx ingress controller using Helm, run the following commands:

```shell
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx \
  --create-namespace
```

### Validate that NGinx is using the MetalLB IP address
Run the following command:

```shell
kubectl get services -n ingress-nginx
```