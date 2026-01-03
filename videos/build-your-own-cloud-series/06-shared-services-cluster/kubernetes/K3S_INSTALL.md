# K3S KUBERNETES Installation
This document describes the steps required to setup a K3s cluster. This will be used for Rancher and all other
foundational applications that will run on Kubernetes

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Dependencies
You should already have mini a computer running Ubuntu. Optionally, you should have an OPNSense (or PFSense) machine
providing DHCP, DNS, and any routing services.


## Install a k3s cluster 
>(REFERENCES:
> - [https://ranchermanager.docs.rancher.com/getting-started/quick-start-guides/deploy-rancher-manager/helm-cli](https://ranchermanager.docs.rancher.com/getting-started/quick-start-guides/deploy-rancher-manager/helm-cli)
    >)

>(IMPORTANT! By default, K3s installs clipper for the Load balancer and Traefik for Ingress. We will be using alternatives to
> these, so they are disabled during startup.)

On your server run the following command:
```shell
# curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik --disable servicelb" INSTALL_K3S_VERSION=<VERSION> sh -s - server --cluster-init
### For example:
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik --disable servicelb" \
  INSTALL_K3S_VERSION=v1.35.0+k3s1 sh -s - server --cluster-init 
```

### Copy the Kubeconfig into your home directory
```shell
mkdir .kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config

### Grant permissions to the Kubeconfig file
# sudo chown <USERNAME> config
### Example
sudo chown hmuser ~/.kube/config
sudo chown hmuser /etc/rancher/k3s/k3s.yaml
```

### Install Helm
```shell
sudo snap install helm --classic
```

### (OPTIONAL) Install k9s
K9s is a great tool for navigating and managing Kubernetes. To install k9s, run the
following command:
```shell
sudo snap install k9s --devmode
sudo ln -s /snap/k9s/current/bin/k9s /snap/bin/
```

### Install the cert manager using Helm
```shell
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.3/cert-manager.crds.yaml

helm repo add jetstack https://charts.jetstack.io

helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace
```

## Install the core sub-systems
### Install Longhorn for Persistent Storage
- [../longhorn/README.md](../longhorn/README.md)

### Install MetalLB as the Load balancer
- [../metal-lb/README.md](../metal-lb/README.md)

### Install Nginx as the Ingress controller
- [../ingress-nginx/README.md](../ingress-nginx/README.md)

## Troubleshooting
### (OPTIONAL) Disable Klipper
If you installed k3s using the default, and now want to disable Klipper to install MetalLb, you can do the following:

>(REFERENCE: [https://documentation.breadnet.co.uk/kubernetes/k3s/disable-klipper/](https://documentation.breadnet.co.uk/kubernetes/k3s/disable-klipper/)

From the server running k3s, modify the following file:

```shell
sudo vi /etc/systemd/system/k3s.service
```

It should look like this:
```
ExecStart=/usr/local/bin/k3s \
    server --disable servicelb \
```

Next, restart the service:
```shell
sudo systemctl daemon-reload && sudo systemctl restart k3s
```

At this point, you install MetalLB using the instructions further above.

## Teardown
To uninstall k3s, run the following command:
>(REFERENCE: [https://docs.k3s.io/installation/uninstall#uninstalling-servers](https://docs.k3s.io/installation/uninstall#uninstalling-servers))

```shell
/usr/local/bin/k3s-uninstall.sh
```