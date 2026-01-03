# Metal LB
This document describes how to install MetalLB as a Load Balancer for your Kubernetes cluster. This 
service will allocate externally facing IP address to allow inbound access to the cluster.

>(REFERENCES: 
> - [https://metallb.universe.tf/installation/#installation-with-helm](https://metallb.universe.tf/installation/#installation-with-helm)
> - [https://metallb.io/configuration/#defining-the-ips-to-assign-to-the-load-balancer-services](https://metallb.io/configuration/#defining-the-ips-to-assign-to-the-load-balancer-services)
> - [https://metallb.io/configuration/#layer-2-configuration](https://metallb.io/configuration/#layer-2-configuration))

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)


## Install MetalLB as the Load balancer
Run the following command from a unix system.

>(IMPORTANT! Run these commands together!)

```shell
helm install \
  metallb oci://registry.suse.com/edge/metallb-chart \
  --namespace metallb-system \
  --create-namespace

while ! kubectl wait --for condition=ready -n metallb-system $(kubectl get\
 pods -n metallb-system -l app.kubernetes.io/component=controller -o name)\
 --timeout=10s; do
 sleep 2
done
```

Next, add the configurations (especially the IP address range)
```shell
cat <<-EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: ip-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.3.20-192.168.3.50
EOF

cat <<-EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: ip-pool-l2-adv
  namespace: metallb-system
spec:
  ipAddressPools:
  - ip-pool
EOF
```