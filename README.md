# pulumi-k8s-oracle

Provisioning of Oracle FreeTier instance with a K8S cluster

## Usage

### Requirements

1. [Pulumi](https://www.pulumi.com/docs/get-started/install/) installed on your system
2. [Pipenv](https://pipenv.pypa.io/en/latest/) installed on your system
3. An Oracle Cloud account with the correct permissions to create resources
   1. Also configure [Pulumi with the required secret for Oracle](https://www.pulumi.com/registry/packages/oci/installation-configuration/)

### Provisioning

1. First you need to create the `Compartment` where the resource will be created:
   1. Run `OCI_TENANCY_ID=$(oci iam compartment list --all --compartment-id-in-subtree true --access-level ACCESSIBLE --include-root --raw-output --query "data[?contains(\"id\",'tenancy')].id | [0]")`
   2. Run `oci iam compartment create --compartment-id $OCI_TENANCY_ID --name K8SClusterCompartment --description "Compartment for the free instance"`
   3. The `name` parameter should match the one that you specify in the Pulumi stack config
   4. Copy the `id` on the output of the last command (i.e. `ocid1.compartment.oc1..aaaaoooo`)
   5. Run `pulumi config set pulumi-k8s-oracle:compartment_id ocid1.compartment.oc1..aaaaoooo` with the correct Compartment ID
2. If you want to customize the Kubernetes setup edit the file `cloud-init.yaml` on the section about the Yaml file for `kubeadm`
3. Once you got the `Compartment` in place run `pulumi up` and wait for the deployment (_N.B._: the network security group allow all ingress traffic; if this is not ideal for you change it)
4. Now you can SSH into the machine to fetch the `kubeconfig` file from `/etc/kubernetes/admin.conf`

## TODO

- setup CI with GHA
