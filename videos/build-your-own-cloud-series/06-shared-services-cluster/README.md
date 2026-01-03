# Platform Server
The purpose of a platform server is to perform the core application functions required for your cloud.
These systems or applications would typically be outside of your Application's Kubernetes cluster, or potentially in
a 'shared' Kubernetes cluster. For this example, we will be using a well-equipped server for the core applications that will run in Kubernetes

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Hardware
### Kubernetes Server
For our Kubernetes server, we will need something a little more robust. This will be a shared server
that just runs on a single node, but can be expanded for high availability.  Since this machine will
run kubernetes and many apps it should have the following minimum specs:
- 8 core (16 threads)
- 32 GB or RAM or greater
- 512 GB or Hard drive space or greater.

## Operating System (Kubernetes)
In this example, I will be using Ubuntu 22.04 as the base operating system for Kubernetes. See the following document
for Ubuntu setup: [../ubuntu-server-setup/OPERATING_SYSTEM.md](../ubuntu-server-setup/OPERATING_SYSTEM.md)

On top of Ubuntu we will be installing k3s.

## Components
The Platform server has the following components

### Kubernetes (k3s)
A lightweight kubernetes cluster will also be installed on the Platform server. It will contain
the following applications:

- nginx (ingress controller)
- Longhorn (For persistent storage)
- Metal LB
- Container Registry
- Vault (Secrets Management)
- GitLab (Git Repo)
- Keycloak (IDP / Oauth 2.0)
- Open LDAP 
- Rancher (Manger Cluster)
- Minio (S3 compatible storage)
- Http Server for Pxe boot
- ArgoCD (optional, but helpful for gitops-based deployments)

## Installation Guide
Start with the following documents to set up the platform server:

1. [kubernetes/K3S_INSTALL.md](kubernetes/K3S_INSTALL.md)
2. [longhorn/README.md](longhorn/README.md)
3. [metal-lb/README.md](metal-lb/README.md)
4. [ingress-nginx/README.md](ingress-nginx/README.md)




