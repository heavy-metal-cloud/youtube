# CSI Driver set up for CephFS (File system storage)
This document describes how to install and set up a Ceph CSI driver for Kubernetes. This will
leverage the existing Ceph used in Proxmox for High Availability (HA).  Ceph is then accessed out
of band from K8s. This is different from installing ceph directly in kubernetes using Rook.io.

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

>(NOTE: This is for volumes that act like a POSIX file system or (NFS). For block level storage, take
> a look at the other README file: [CSI_DRIVER_CEPH_RBD.md](CSI_DRIVER_CEPH_RBD.md))

>(REFERENCE: [https://devopstales.github.io/kubernetes/k8s-cephfs-storage-with-csi-driver/](https://devopstales.github.io/kubernetes/k8s-cephfs-storage-with-csi-driver/))

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

### Create a CephFS volume
We need to create a CephFS volume to store the PVC data.

From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `proxmox01` - `Shell`

In the shell, run the following command:
```shell
#ceph fs subvolumegroup create <VOLUME_NAME> <GROUP_NAME>
### For example:
ceph fs subvolumegroup create cephfs csi

### NOTE: In this case we already have a CephFS Volume created called `cephfs`
```

This will be the client admin key that will also be applied to the Helm values configuration.

### Install the Helm repo
You should run this command from a computer that has `KUBECONFIG` access to the k3s cluster. This is
the cluster where you will be installing the Ceph CSI driver.

```shell
helm repo add ceph-csi https://ceph.github.io/csi-charts
```

### Save the full helm values
To grab the full helm values files, run the following command or you can go to this URL: [https://github.com/ceph/ceph-csi/blob/devel/charts/ceph-csi-cephfs/values.yaml](https://github.com/ceph/ceph-csi/blob/devel/charts/ceph-csi-cephfs/values.yaml)

```shell
helm show values ceph-csi/ceph-csi-cephfs
```

### Update values you want to override
Update the file located at: [ceph-csi-driver-values/cephfs/value-overrides.yaml](ceph-csi-driver-values/cephfs/value-overrides.yaml)

The important lines are listed below. These values are referenced from the two commands we ran from the Proxmox shell:
```yaml
csiConfig:
  - clusterID: 997c1560-0623-40b5-be2d-cea2ba357bb7
    monitors:
      - 192.168.3.4:6789
      - 192.168.3.5:6789
      - 192.168.3.6:6789
    cephFS:
      subvolumeGroup: "csi"
secret:
  name: csi-cephfs-secret
  adminID: admin
  adminKey: AQASJmpnkQgzMBAA/Lx29ahfBUG7Emk2ggVYqA==
  create: true
storageClass:
  create: true
  name: k8s-cephfs
  clusterID: 997c1560-0623-40b5-be2d-cea2ba357bb7
  # (required) CephFS filesystem name into which the volume shall be created
  fsName: cephfs    ###### <----- NOTE!!!!! This line is VERY important, you should enter your cephFS volume here
  reclaimPolicy: Delete
  allowVolumeExpansion: true
  volumeNamePrefix: "csi-k8s-"
  provisionerSecret: csi-cephfs-secret
  controllerExpandSecret: csi-cephfs-secret
  nodeStageSecret: csi-cephfs-secret
```

### Create the Namespace
```shell
kubectl create ns ceph-csi-cephfs
```

### Install the helm chart using the override values
```shell
helm upgrade --install --namespace ceph-csi-cephfs --values value-overrides.yaml ceph-csi-cephfs ceph-csi/ceph-csi-cephfs
```

### Storage location in Ceph/Proxmox
From your Proxmox shell, you should now see the following directory, with any PVC that you create for
this StorageClass:

```shell
cd /mnt/pve/cephfs/volumes/csi
```

## Testing
### Create a test PVC
The following file contains an example PVC: [ceph-csi-driver-values/cephfs/example-cephfs-pvc.yaml](ceph-csi-driver-values/cephfs/example-cephfs-pvc.yaml)

Run the following command:
```shell
kubectl apply -f ceph-csi-driver-values/cephfs/example-cephfs-pvc.yaml --namespace default
```

The PVC should be created with a status of `Bound`. You should also see the storage and allocation details.

## Troubleshooting
### A PVC will not bind
Try checking the logs of the `Deployment` and `Daemonset` for the CEPH CSI driver.  The pod logs should
give some insights into the issues.