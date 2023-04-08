# pulumi-k8s-oracle

Provisioning of Oracle FreeTier instances for a free K8S cluster

Manage the cluster using: https://github.com/notdodo/pulumi-k8s

## Usage

### Requirements

1. [Pulumi](https://www.pulumi.com/docs/get-started/install/) installed on your system
2. [Pipenv](https://pipenv.pypa.io/en/latest/) installed on your system
3. An Oracle Cloud account with the correct permissions to create resources
   1. Also configure [Pulumi with the required secret for Oracle](https://www.pulumi.com/registry/packages/oci/installation-configuration/)
4. A Cloudflare account with a DNS zone API token

### Provisioning

The project will setup a single instance with the maximum of specs allowed by the Oracle FreeTier; if you have more accounts or want to create a multinode cluster configure the other Oralce accounts in your machine and edit accordingly the `Pulumi.yaml`

#### General

0. Edit the file `Pulumi.yaml` with the correct information about your instance specifications, network, and domain
1. Create at least 2 pair of wireguard private and public key to setup the site-to-site tunnel between nodes (required since we are using at least two different Oracle account)

#### Master node

0. Select the stack and the configuration for the master `pulumi stack select master`
1. Edit the file `Pulumi.master.yaml` with the correct information about your Oracle tenant, names and paths
2. If you want to customize the Kubernetes setup edit the file `cloud-init-master.yaml` on the section about the Yaml file for `kubeadm`
3. Run `pulumi up` and wait for the deployment (_N.B._: the network security group allow all ingress traffic; if this is not ideal for you change it)
4. Now you can SSH into the machine to fetch the `kubeconfig` file from `/etc/kubernetes/admin.conf`

#### Worker nodes

0. Select the stack and the configuration for the worker node `pulumi stack select worker`
1. Edit the file `Pulumi.worker.yaml` with the correct information about your Oracle tenant, names and paths
2. If you want to customize the instance setup editi the file `cloud-init-worker.yaml`
3. Make sure that your private key specified in the Pulumi stack configuration is correct and is allowed to access the master node; this is required to automatically join the cluster
4. Run `pulumi up` and wait for the deployment

## Troubleshooting

- You can SSH into the nodes using the `ssh_priv.key` generated during the provisioning
- Check the status of the WireGuard VPN sites
- Check the logs in `/var/log/cloud-init-output.log`
