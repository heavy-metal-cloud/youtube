# Longhorn
Longhorn is a distributed storage system for Kubernetes

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Install Longhorn 

Use this method if you want a quick install and won't be using helm
>(NOTE: It's probably better to use the Helm install for more control over the initial settings)

>(REFERENCE: [https://docs.k3s.io/storage#setting-up-longhorn](https://docs.k3s.io/storage#setting-up-longhorn))

Run the following command:
```shell
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.10.1/deploy/longhorn.yaml
```

>(IMPORTANT!!!! You may have to update the `/etc/multipath.conf` mentioned in the troubleshooting section below if
> pods won't start. See the Troubleshooting sections.)

### (OPTIONAL) Mark the `longhorn` StorageClass as 'Default'
The `default` StorageClass should only be `longhorn` Run the following commands to view and change
StorageClass settings:

```shell
kubectl get storageclass
```

In my case, this produced output that looks like this:
```
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  25h
longhorn (default)     driver.longhorn.io      Delete          Immediate              true                   10m
```

As you can see, there are two `default` storage classes.
I want just the `longhorn` storage class to be default, in my case. So, I remove the `default` setting from the
`local-path` StorageClass, using the command below:

```shell
kubectl patch storageclass \
  local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

## Troubleshooting
### Pod won't start due to filesystem errors
If a pod doesn't start that uses a PVC, perform a `describe` and look at the events. You may see something
like this:
- ` MountVolume.MountDevice failed for volume "pvc-2de0978b-adc5-4d5c-8137-123148341d58"  │
│ : rpc error: code = Internal desc = format of disk "/dev/longhorn/pvc-2de0978b-adc5-4d5c-8137-123148341d58" failed: type:("ext4") target:("/var/lib/kubelet/plugins/ │
│ kubernetes.io/csi/driver.longhorn.io/de6b.../globalmount") options:("defaults") errcode:(exit status 1) out │
│ put:(mke2fs 1.46.4`
- `/dev/longhorn/pvc-2de... is apparently in use by the system; will not make a filesystem here! `

This page has some details: [https://longhorn.io/kb/troubleshooting-volume-with-multipath/](https://longhorn.io/kb/troubleshooting-volume-with-multipath/)

>(IMPORTANT! Before doing the following steps, try cleaning up unused block devices in the `Device Cleanup` section below, then
> try reinstalling Longhorn. Make sure to delete the `/dev/longhorn` directory after Longhorn is uninstalled)

Modify the `/etc/multipath.conf` file with the config below
```
blacklist {
    devnode "^sd[a-z0-9]+"
}
```

Next, restart the Multipath Daemon:
```shell
sudo systemctl restart multipathd.service

### View the Multipath settings:
sudo multipath -t
```

### LongHorn issues - Pod's won't start because the PVC's are not bound
Sometimes, Longhorn has run out of available storage and the PVC's will not bind. The easiest way
to troubleshoot this issue is using the Longhorn Frontend UI.

First, port forward into the UI. This will be in the `longhorn-system` namespace.
```shell
kubectl port-forward svc/longhorn-frontend 8000:8000 --namespace longhorn-system
```

You should now be able to access the Longhorn UI using: [http://localhost:8000](http://localhost:8000)

Click `Dashboard` from the main menu. You will probably see that some volumes are in a `Fault` state.
Click into this. You will probably see that some volumes are over allocated and need more free space.

From the main menu at the top, click `Node`.  There should now be a table with rows of nodes. There will
probably be only one row for your installation. Mine is called `platform01` from the Rancher cluster name.

- Click the dropdown menu on the right-hand side of the row.
- Select `Edit node and disks`
- **Storage Reserved** - Increase the value here.
- Click `Save`

At this point the PVC issues should start to clear up.

### LongHorn on a single machine should have replicas set to one
First, port forward into the UI. This will be in the `longhorn-system` namespace.
```shell
kubectl port-forward svc/longhorn-frontend 8000:8000 --namespace longhorn-system
```

You should now be able to access the Longhorn UI using: [http://localhost:8000](http://localhost:8000)
Click `Setting` -> `General` from the main menu.

- **Default Replica Count** - Set this to `1`
- Click the `Save` button

## Device Cleanup
### (OPTIONAL) Remove unused block devices from a previous Longhorn installation

>(REFERENCE: [https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/storage_administration_guide/removing_devices#removing_devices](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/storage_administration_guide/removing_devices#removing_devices))

```shell
# First switch to the root user
sudo su -

lsblk -f
### You should see devices here with no disk usage starting with `sd`

# echo 1 > /sys/block/<DEVICE_NAME>/device/delete
### For example:
echo 1 > /sys/block/sda/device/delete
```

## Teardown
To uninstall Longhorn, first perform the `Device Cleanup` above, then run the following commands:

```shell
helm uninstall longhorn -n longhorn-system
kubectl delete namespace longhorn-system

## If the namespace is stuck in a terminating state, run the following:
#### (REFERENCE: https://longhorn.io/docs/1.7.2/deploy/uninstall/#uninstalling-using-rancher-ui-or-helm-failed-i-am-not-sure-why)

kubectl delete ValidatingWebhookConfiguration longhorn-webhook-validator
kubectl delete MutatingWebhookConfiguration longhorn-webhook-mutator

NAMESPACE=longhorn-system
for crd in $(kubectl get crd -o jsonpath={.items[*].metadata.name} | tr ' ' '\n' | grep longhorn.io); do
  kubectl -n ${NAMESPACE} get $crd -o yaml | sed "s/\- longhorn.io//g" | kubectl apply -f -
  kubectl -n ${NAMESPACE} delete $crd --all
  kubectl delete crd/$crd
done

sudo rm -Rf /dev/longhorn
sudo rm -Rf /var/lib/longhorn
```

Finally, check the partitions and cleanup and dangling partitions as listed in the `Device Cleanup` section above:
```shell
lsblk -f
```