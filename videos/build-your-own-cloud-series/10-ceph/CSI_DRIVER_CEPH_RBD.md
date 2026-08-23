# CSI Driver set up for CephRBD (Block Level storage)
This document describes how to install and set up a Ceph CSI driver for Kubernetes. This will
leverage the existing Ceph used in Proxmox for High Availability (HA).  Ceph is then accessed out
of band from K8s. This is different from installing ceph directly in kubernetes using Rook.io.

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

>(NOTE: This is for volumes that are block level storage.  For volumes that act like a POSIX file system or (NFS) take 
> a look at the other README file: [CSI_DRIVER_CEPH_FS.md](CSI_DRIVER_CEPH_FS.md))

>(REFERENCES:
> - [https://kubesphere.io/docs/v3.4/installing-on-linux/persistent-storage-configurations/install-ceph-csi-rbd/](https://kubesphere.io/docs/v3.4/installing-on-linux/persistent-storage-configurations/install-ceph-csi-rbd/)
> - [https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/manage-clusters/create-kubernetes-persistent-storage/manage-persistent-storage/use-external-ceph-driver](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/manage-clusters/create-kubernetes-persistent-storage/manage-persistent-storage/use-external-ceph-driver))

## Depenedencies
At this point you should have a fully functional Proxmox cluster with Ceph. You should also have
VM's running with k3s Kubernetes installed. This Kubernetes cluster should be available using
`kubectl` (or similar). 

## CSI Driver Installation
### Gather configurations parameters
From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `proxmox01` - `Shell`

In the shell, run the following command:
```shell
ceph config generate-minimal-conf
```

The output should look something like this:
```
# minimal ceph.conf for 997c1560-0623-40b5-be2d-cea2ba357bb7
[global]
        fsid = 997c1560-0623-40b5-be2d-cea2ba357bb7
        mon_host = [v2:192.168.3.4:3300/0,v1:192.168.3.4:6789/0] [v2:192.168.3.5:3300/0,v1:192.168.3.5:6789/0] [v2:192.168.3.6:3300/0,v1:192.168.3.6:6789/0]
```

There are a few key pieces of information here. 
- **fsid** - You will apply this to the Helm values in the following sections
- **mon_host** - You will apply the IP/ports to the helm values, as well

Next, run this command from the Proxmox shell:
```shell
ceph auth get-key client.admin
```

The output should look something like this:
``` 
AQASJmpnkQgzMBAA/Lx29ahfBUG7Emk2ggVYqA==
```

This will be the client admin key that will also be applied to the Helm values configuration.

### Create an RBD Admin user
A user with Access to the RBD pool is required. To create the user and the User key, run the following command:

```shell
# ceph auth get-or-create-key client.<USER_NAME>> mds 'allow *' mgr 'allow *' mon 'allow *' osd 'allow * pool=<POOL_NAME>>' 
### For example:
ceph auth get-or-create-key client.myPoolAdmin mds 'allow *' mgr 'allow *' mon 'allow *' osd 'allow * pool=ceph-pool-01' 
```

The output should look something like this:
```
QVFDQlYzZG5nMWw5SmhBQWRzY0dnbm5vNm5wZW1BRGU3eTU3MHc9PQ==
```

You will need both the username ('myPoolAdmin' in this case) and the user key (shown above) in the values file for Helm.

### Install the Helm repo
You should run this command from a computer that has `KUBECONFIG` access to the k3s cluster. This is
the cluster where you will be installing the Ceph CSI driver.

```shell
helm repo add ceph-csi https://ceph.github.io/csi-charts
```

### Save the full helm values
To grab the full helm values files, run the following command or you can go to this URL: [https://github.com/ceph/ceph-csi/blob/devel/charts/ceph-csi-rbd/values.yaml](https://github.com/ceph/ceph-csi/blob/devel/charts/ceph-csi-rbd/values.yaml)

```shell
helm show values ceph-csi/ceph-csi-rbd
```

### Update values you want to override
Update the file located at: [ceph-csi-driver-values/value-overrides.yaml](ceph-csi-driver-values/cephfs/value-overrides.yaml)

The important lines are listed below. These values are referenced from the two commands we ran from the Proxmox shell:
```yaml
csiConfig:
  - clusterID: 997c1560-0623-40b5-be2d-cea2ba357bb7
    monitors:
      - 192.168.3.4:6789
      - 192.168.3.5:6789
      - 192.168.3.6:6789
secret:
  name: csi-cephrbd-secret
  userID: myPoolAdmin
  userKey: QVFDQlYzZG5nMWw5SmhBQWRzY0dnbm5vNm5wZW1BRGU3eTU3MHc9PQ==
  create: true
storageClass:
  create: true
  name: k8s-cephrbd
  clusterID: 997c1560-0623-40b5-be2d-cea2ba357bb7
  reclaimPolicy: Delete
  allowVolumeExpansion: true
  volumeNamePrefix: "csi-k8s-"
  provisionerSecret: csi-cephrbd-secret
  controllerExpandSecret: csi-cephrbd-secret
  nodeStageSecret: csi-cephrbd-secret
```

### Create the Namespace
```shell
kubectl create ns ceph-csi-rbd
```

### Install the helm chart using the override values
```shell
helm upgrade --install --namespace ceph-csi-rbd --values value-overrides.yaml ceph-csi-rbd ceph-csi/ceph-csi-rbd
```

## Testing
### Create a test PVC
The following file contains an example PVC: [ceph-csi-driver-values/cephrbd/example-cephrbd-pvc.yaml](ceph-csi-driver-values/cephrbd/example-cephrbd-pvc.yaml)

Run the following command:
```shell
kubectl apply -f ceph-csi-driver-values/cephrbd/example-cephrbd-pvc.yaml --namespace default
```

The PVC should be created with a status of `Bound`. You should also see the storage and allocation details.

## Troubleshooting
### A PVC will not bind
Try checking the logs of the `Deployment` and `Daemonset` for the CEPH CSI driver.  The pod logs should
give some insights into the issues.