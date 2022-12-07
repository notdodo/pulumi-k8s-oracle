# pulumi-k8s-oracle

Provisioning of Oracle FreeTier instance with a K8S cluster

## Usage

### Requirements

1. [Pulumi](https://www.pulumi.com/docs/get-started/install/) installed on your system
2. [Pipenv](https://pipenv.pypa.io/en/latest/) installed on your system
3. An Oracle Cloud account with the correct permissions to create resources
   1. Also configure Pulumi with the required secret for Oracle

### Provisioning

1. First you need to create the `Compartment` where the resource will be created:
   1. open the `__main__.py` and comment all below line 11
   2. run `pulumi up` and wait the creation of the resource
2. Once you got the `Compartment` in place, restore the `__main__.py` content and run `pulumi up`.

## TODO

- use `cloud-init` to setup Kube on the startup or at least install required packages
- connect to SSH using Pulumi to startup the K8S cluster
- setup CI with GHA
