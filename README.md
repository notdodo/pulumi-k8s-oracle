# pulumi-k8s-oracle

Provisioning of Oracle FreeTier instance with a K8S cluster

Manage the cluster using: https://github.com/notdodo/pulumi-k8s

## Usage

### Requirements

1. [Pulumi](https://www.pulumi.com/docs/get-started/install/) installed on your system
2. [Pipenv](https://pipenv.pypa.io/en/latest/) installed on your system
3. An Oracle Cloud account with the correct permissions to create resources
   1. Also configure [Pulumi with the required secret for Oracle](https://www.pulumi.com/registry/packages/oci/installation-configuration/)
4. A Cloudflare account with a DNS zone API token

### Provisioning

#### Master node

1. `pulumi stack select k8s-master`
2. If you want to customize the Kubernetes setup edit the file `cloud-init-master.yaml` on the section about the Yaml file for `kubeadm`
3. Run `pulumi up` and wait for the deployment (_N.B._: the network security group allow all ingress traffic; if this is not ideal for you change it)
4. Now you can SSH into the machine to fetch the `kubeconfig` file from `/etc/kubernetes/admin.conf`
