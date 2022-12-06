# pulumi-k8s-oracle

Provisioning of Oracle FreeTier instance with a K8S cluster

## Usage

### Requirements

1. [Pulumi](https://www.pulumi.com/docs/get-started/install/) installed on your system
2. [Pipenv](https://pipenv.pypa.io/en/latest/) installed on your system
3. An Oracle Cloud account with the correct permissions to create resources
   1. Also configure Pulumi with the required secret for Oracle

### Provisioning

Once you got all the requirements simply drop into the pipenv shell and run `pulumi up`.

## TODO

- actually create the instance (ref. https://blog.ediri.io/pulumi-oci-provider-how-to-create-a-minecraft-arm-instance-on-oracle-cloud-infrastructure)
  - check if it is compliance with the free tier
- use `cloud-init` to setup Kube on the startup or at least install required packages
- connect to SSH using Pulumi to startup the K8S cluster
- setup CI with GHA
