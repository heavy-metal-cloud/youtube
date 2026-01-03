# Build Your Own Cloud! - TLS
>(REFERENCES: This document is based on the follow repo from the Feisty Duck:
> - [https://github.com/ivanr/bulletproof-tls]()
> - [https://www.feistyduck.com/books/bulletproof-tls-and-pki/](https://www.feistyduck.com/books/bulletproof-tls-and-pki/))

This document walks through the shell operations in my video (https://www.youtube.com/@HeavyMetalCloud) covering TLS certificates. 

For my bare metal cloud, I'll be using a domain called `*.heavymetalcloud.lan`. The certificate
I'll be creating, is a wildcard cert that I'll use for multiple uses. For example:

www.heavymetalcloud.lan, vault.heavymetalcloud.lan, opnsense.heavymetalcloud.lan, etc.

>(IMPORTANT!!! The Root CA will have to be installed in the Truststore of any system trying to secure the 
> *.heavymetalcloud.lan domain)

The cert will have a chain of trust that includes three certificates:
- Root CA - (`root-ca.conf`) - This will be a self-signed Certificate Authority. This will be the top-level cert.
- Subordinate CA - (`sub-ca-conf`) - This is an intermediate cert that will sign the leaf certs. The issuer for this cert will be the Root CA.
- Leaf Cert - (`heavymetalcloud.lan.conf`) - This will be the cert for my domain that I want to protect, `*.heavymetalcloud.lan`. This  cert will be issued by the subordinate cert.

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Create the certs
### Directory Setup
```shell
### Create a directory for your certs. You can call this directory anything you want.
mkdir hmcloud
cd hmcloud

### Now create the sub-directories and files required
mkdir certs db private
chmod 700 private
touch db/index
openssl rand -hex 16 > db/serial
echo 1001 > db/crlnumber
```

### Copy config files to the base directory
>(NOTE: You should be in the `hmcloud/` directory)

Copy all `*.conf` files to the base directory

### CA cert
```shell
### Create the CSR and private key for the root CA Cert.
openssl req -new \
  -config root-ca.conf \
  -out root-ca.csr \
  -keyout private/root-ca.key
  
### (OPTIONAL) View the contents of the CSR
openssl req -in root-ca.csr -text -noout -verify
  
### Create the root certificate  
#### (NOTE: `-notext` removes the cert information at the top of the .crt file. You can remove
#### this option to view the full text and PEM cert in the .crt file)
openssl ca -selfsign \
  -config root-ca.conf \
  -in root-ca.csr \
  -out root-ca.crt \
  -extensions ca_ext \
  -notext
  
### (OPTIONAL) Let's inspect the certificate
openssl x509 -noout -text -in root-ca.crt
```

### Create Subordinate CA
```shell
### Create the CSR and private key for the Subordinate Cert.
openssl req -new \
  -config sub-ca.conf \
  -out sub-ca.csr \
  -keyout private/sub-ca.key

### Create the subordinate certificate  
#### (NOTE: `-notext` removes the cert information at the top of the .crt file. You can remove
#### this option to view the full text and PEM cert in the .crt file) 
openssl ca \
  -config root-ca.conf \
  -in sub-ca.csr \
  -out sub-ca.crt \
  -extensions sub_ca_ext \
  -notext
  
### (OPTIONAL) Let's inspect the certificate
openssl x509 -noout -text -in sub-ca.crt
```

### Create the Server cert
```shell
### Create the CSR and private key for the leaf Cert.
openssl req -new \
  -config multi-domain.heavymetalcloud.lan.conf \
  -out heavymetalcloud.lan.csr \
  -keyout private/heavymetalcloud-encrypted.lan.key
  
### Create the leaf certificate    
#### (NOTE: `-notext` removes the cert information at the top of the .crt file. You can remove
#### this option to view the full text and PEM cert in the .crt file)
openssl ca \
  -config sub-ca.conf \
  -in heavymetalcloud.lan.csr \
  -out heavymetalcloud.lan.crt \
  -extensions server_ext \
  -notext
  
### (OPTIONAL) Let's inspect the certificate
openssl x509 -noout -text -in heavymetalcloud.lan.crt
```

### (OPTIONAL) Decrypt the Private key for some uses
Some systems have issues using an encrypted private key. In those cases, you can decrypt your private key.

>(NOTE: I will be using a decrypted private key for the rest of my `Build your Own Cloud!` series)

```shell
openssl rsa -in private/heavymetalcloud-encrypted.lan.key -out private/heavymetalcloud.lan.key
```

## Certificate Bundling
>(NOTE: If you don't bundle your subordinate (intermediate) cert with the leaf cert, then you will
> have to load the subordinate cert in your trust store, along with the Root CA. This isn't ideal, so bundling
> is a good idea.)

For the certificate that you will be loading in your servers (web servers, etc.) It should
contain the following at a minimum:

- Leaf cert
- Subordinated Cert

To do this you can run the following command:
```shell
cat heavymetalcloud.lan.crt sub-ca.crt > heavymetalcloud.lan-combined.pem
```

You can also include the ROOT CA cert in the bundle. However, you will still have to load this
cert into your trust stores for your web browser or apps to trust it:

```shell
### (OPTIONAL)
cat heavymetalcloud.lan.crt sub-ca.crt root-ca.crt > heavymetalcloud.lan-bundled.pem
```

## Helpful commands
### View a single cert
```shell
openssl x509 -noout -text -in mycert.crt
```

### View a CRT or PEM file that contains multiple certs (bundled)
```shell
while openssl x509 -noout -text; do :; done < mycert-bundle.pem
```