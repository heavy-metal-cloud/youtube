# Open LDAP Installation
This guide describes the installing Open LDAP using the following helm chart:
- [https://github.com/jp-gouin/helm-openldap](https://github.com/jp-gouin/helm-openldap)

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Dependencies
You should have a DNS server (like `Unbound DNS`) to create the DNS entries required for OpenLDAP. You should also have
a self-signed wildcard cert and Certificate Authority, if you want to use TLS (recommended!)

You should already have your Platform server running with the following:
- K3s
- Longhorn for persistent storage
- Rancher (Manager)

## Install OpenLDAP using Helm
### Create the namespace
```shell
kubectl create namespace openldap
```

### Create a secret for TLS certs
```shell
kubectl create secret tls ldap-certs.heavymetalcloud.lan --cert=tls.crt --key=tls.key --namespace openldap
```

### Modify the Helm chart values
>(REFERENCE: [https://github.com/jp-gouin/helm-openldap/blob/master/values.yaml](https://github.com/jp-gouin/helm-openldap/blob/master/values.yaml))

A sample values file is in this directory, called [values-overrides.yaml](values-overrides.yaml)

The main sections to modify are listed below:

```yaml
global:
#...
  ldapDomain: "heavymetalcloud.lan"
#...
  adminUser: "admin"
  adminPassword: password
  configUser: "admin"
  configPassword: password

persistence:
  enabled: true
#...
  storageClass: "longhorn"

ltb-passwd:
  enabled : true
#...
  ingress:
    hosts:
      - "ssl-ldap2.heavymetalcloud.lan"
    ## Ingress cert
    tls:
      - secretName: ldap-certs.heavymetalcloud.lan
        hosts:
          - ssl-ldap2.heavymetalcloud.lan

phpldapadmin:
  enabled: true
#...
  ingress:
    ## Ingress Host
    hosts:
      - phpldapadmin.heavymetalcloud.lan
    ## Ingress cert
    tls:
     - secretName: ldap-certs.heavymetalcloud.lan
       hosts:
       - phpldapadmin.heavymetalcloud.lan
```

### Deploy the Helm Chart 
Run the following command:

```shell
helm repo add helm-openldap https://jp-gouin.github.io/helm-openldap/
helm upgrade --install --values value-overrides.yaml --namespace openldap openldap helm-openldap/openldap-stack-ha 
```

### Create a Load Balancer to expose OpenLDAP via port 389
```shell
cat <<-EOF | kubectl apply --namespace openldap -f -
apiVersion: v1
kind: Service
metadata:
  name: openldap-lb
spec:
  type: LoadBalancer
  selector:
    app.kubernetes.io/component: openldap
  ports:
  - protocol: TCP
    port: 389
    targetPort: 1389 ### (Note: the Pod ports use '1389' instead of '389')
EOF
```

### Create DNS entries
Create DNS entries for the following domains:
- phpldapadmin.heavymetalcloud.lan
- ssl-ldap2.heavymetalcloud.lan

In my case, both domains will point to `192.168.3.20` which is the MetalLB load balancer IP of the platform k3s cluster. Since I'm using
`Unbound DNS` in `OPNSense`, I'll update the DNS there in the `overrides` section