# Install the Twuni private container registry in Kubernetes

>(NOTE: These instructions are derived from: [https://github.com/twuni/docker-registry.helm](https://github.com/twuni/docker-registry.helm))

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Create a password file for authentication to the Registry
Run the following commands to create a password file in your home directory.  The contents of this file will then be used when running
helm to add authentication to your Registry
```shell
sudo apt install apache2-utils
mkdir /home/hmuser/auth
htpasswd -B -b -c /home/hmuser/auth/htpasswd some-user some-password

### If the command above doesn't work, try this instead:
docker run --entrypoint htpasswd httpd:2 -Bbn user password > ./htpasswd
```



## Create a Secret for TLS certs
>(NOTE: View the README file under ../../certificate-authority/README.md for more
> details in the setup of a self-signed cert with included (bundled) CA cert.)

```shell 
kubectl create namespace container-registry
kubectl create secret tls heavymetal-cert-secret \
    --cert=tls.crt --key=tls.key \
    --namespace container-registry 
```

## Install Twuni via Helm

>(IMPORTANT!!!! recently, the `--set secrets.htpasswd` helm option is altering the encrypted password when it drops into a secret
> for some reason. The text from the file and the decoded secret won't match!!!.  In the meantime, just put the
> htpasswd in the overridden values.yaml file. This works.)

```shell
helm repo add twuni https://twuni.github.io/docker-registry.helm
helm upgrade --install --namespace container-registry --values value-overrides.yaml \
  twuni twuni/docker-registry 
```

## Testing the Container Registry from a client

### Login to the Container Registry from your client. 
From your client, run the following command to login to the Container Registry. 

>(NOTE: It's assumed that you've already installed the TLS certificates on the client)

```shell 
## Replace 'registry.heavymetalcloud.lan' with your own domain
docker login registry.heavymetalcloud.lan
```

### Push images to your local Container Registry Server
To push an image to your local Container Server, you'll first have to 'tag' the image using the URL of the
registry server, then perform the 'push' command.

`docker tag <IMAGE_NAME>:<VERSION> <REGISTRY_SERVER_URL:PORT/IMAGENAME>`
Here's an example:
```
docker tag exampleImage:1.0.0 registry.heavymetalcloud.lan/exampleImage
```

### Verify images were pushed to the private Container Registry
Run the following comnand to view all images on your local docker registry:
```
curl -X GET https://registry.heavymetalcloud.lan/v2/_catalog
```

### Remove an image from the private Container Registry
Run the following set of commands to remove an image from the container registry:
```
# First, determine the image name:
curl -X GET https://registry.heavymetalcloud.lan/v2/_catalog

# Next, Find the 'Docker-Content-Digest' header value:
curl -v -u <USERNAME>:<PASWORD> -H "Accept: application/vnd.docker.distribution.manifest.v2+json" -X HEAD https://registry.heavymetalcloud.lan/v2/<IMAGE_NAME_FROM_LAST_STEP>/manifests/<VERSION_GOES_HERE>

# Finally, using the 'Docker-Content-Digest' header, delete the image entry
curl -X DELETE -u <USERNAME>:<PASWORD> https://registry.heavymetalcloud.lan/v2/<IMAGE_NAME_FROM_LAST_STEP>/manifests/<DIGEST_GOES_HERE>
```

## Setup Kubernetes to use your Private Registry
### Setup a secret
First, you'll have to setup a secret with the login credentials for the docker
registry.

>(IMPORANT!!! This will have to be setup for each namespace that uses this registry!)

``` 
kubectl create secret docker-registry regcred \
    --namespace=<your-namespace> \
    --docker-server=<your-registry-server> \
    --docker-username=<your-name> --docker-password=<your-pword> \
    --docker-email=<your-email>
    
### For example: 
### (e-mail is optional)
kubectl create secret docker-registry regcred \
    --namespace=mytest \
    --docker-server=docker.heavymetalcloud.lan \
    --docker-username=hduser --docker-password=password
```

### (Option 1) Using Image Pull Secrets
Once the secret is setup in the namespace you want to deploy to, you can
add an `imagePullSecrets` section in the deployment/pod.

This is kind of tedious, so I would recommend option 2 below, for a more streamlined
approach.

Example Deployment with the ImagePullSecrets:
``` 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: mytest
spec:
  template:
    spec:
      containers:
        - name: my-app
          image: registry.heavymetalcloud.lan/my-app:latest
      imagePullSecrets:   ## <-- Use these two lines to setup the secret
        - name: regcred   ## <-- The secret from the last step
```

### (Option 2) Use the default service account
This option is easier, since you only have to apply it once per namespace. It makes
use of the Default serviceaccount to apply the `imagePullSecrets` to all apps.

>(IMPORTANT!  This has to be applied to all namespaces that will make use of this docker registry)

```
 kubectl patch serviceaccount default \
  -p "{\"imagePullSecrets\": [{\"name\": \"regcred\"}]}" \
  -n <your-namespace>
```

## Using the Private Registry with Helm
With the latest templates that Helm creates, a serviceAccount is created for the project by default.
Assuming you setup authentication to your registry using Option #2 above (Using the default serviceAccount) you'll
have to make the following changes in your `values.yaml` file for the chart:

>(NOTE: Another option would be to patch the service account created by helm with the `regcred` secret you created in
> previous steps.)

```yaml
serviceAccount:
  create: false
  name: "default"
```

## Proxy (Mirror) a public repo
If you have the proxy setup in your values.yaml file, for example:

```yaml
configData:
  version: 0.1
  proxy:
    enabled: true
    remoteurl: https://registry-1.docker.io
```

When pulling an image without a `namespace`, you will get an error that looks like this: 
`Error response from daemon: manifest for registry.heavymetalcloud.lan/nginx:latest not found: manifest unknown:`

The reason this happens, is the image you're trying to pull is `nginx` and doesn't have a leading namespace, like `mycorp/nginx`

For images that don't have the leading namespace, you'll have to prepend them with `library`. For example: `libary/nginx`

Here are some more examples to illustrate the point:
```shell
#### These examples will NOT work!!!!!
docker pull registry.heavymetalcloud.lan/nginx
docker pull registry.heavymetalcloud.lan/mysql

### These examples WILL work! because we're adding the `library` namespace
docker pull registry.heavymetalcloud.lan/library/nginx
docker pull registry.heavymetalcloud.lan/library/mysql
```

