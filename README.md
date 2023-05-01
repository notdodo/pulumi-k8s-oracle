# pulumi-k8s-oracle

Provisioning of a Kubernetes cluster on Oracle Cloud FreeTier

Manage the cluster using: https://github.com/notdodo/pulumi-k8s

## Usage

### Requirements

1. [Pulumi](https://www.pulumi.com/docs/get-started/install/) installed on your system
2. [Pipenv](https://pipenv.pypa.io/en/latest/) installed on your system
3. An Oracle Cloud account with the correct permissions to create resources
   1. Also configure [Pulumi with the required secret for Oracle](https://www.pulumi.com/registry/packages/oci/installation-configuration/)
4. A Cloudflare account with a DNS zone API token

![pulumi_k8s_oracle](https://user-images.githubusercontent.com/6991986/235491523-fdba862a-3118-45f9-bbbe-ae04d0d5284f.png)

### Provisioning

The project will setup a single instance with the maximum of specs allowed by the Oracle FreeTier; if you have more accounts or want to create a multinode cluster configure the other Oracle accounts in your machine and edit accordingly the `Pulumi.yaml` file.

#### General

0. Edit the file `Pulumi.yaml` with the correct information about your instance specifications, network, and domain
1. Create at least 2 pair of Wireguard private and public key to setup the site-to-site tunnel between nodes (required since we are using at least two different Oracle account)
2. The cluster will not bind to the external/public IP address so another pair of Wireguard keys is required to access the API server from you machine.

To connect to the cluster using your device setup a Wireguard configuration:

```
[Interface]
Address = 10.0.10.100/32
PrivateKey = <yourMachineWireguardPrivateKey>

[Peer]
AllowedIPs = 10.0.10.0/24,10.0.100.0/24
Endpoint = <yourPublicDomainOrIp>:51000
PersistentKeepAlive = 25
PublicKey = <masterNodeWireguardPublicKey>
```

#### Master node

0. Select the stack and the configuration for the master `pulumi stack select master`
1. Edit the file `Pulumi.master.yaml` with the correct information about your Oracle tenant, names and paths
2. If you want to customize the Kubernetes setup edit the file `cloud-init-master.yaml` on the section about the Yaml file for `kubeadm`
3. Run `pulumi up` and wait for the deployment (_N.B._: the network security group allows only ingress for SSH and Wireguard ports; if this is not ideal for you change it as you wish)
4. Now you can SSH into the machine to fetch the `kubeconfig` file from `/etc/kubernetes/admin.conf` using the SSH keys generate during the `pulumi up` command

#### Worker nodes

0. Select the stack and the configuration for the worker node `pulumi stack select worker`
1. Edit the file `Pulumi.worker.yaml` with the correct information about your Oracle tenant, names and paths
2. If you want to customize the instance setup editi the file `cloud-init-worker.yaml`
3. Run `pulumi up` and wait for the deployment

## Troubleshooting

- You can SSH into the nodes using the `ssh_priv.key` generated during the provisioning
- Check the status of the WireGuard VPN sites
- Check the logs in `/var/log/cloud-init-output.log`
- Use [k9s](https://github.com/derailed/k9s) to debug Kubernetes issues
- Restart the Wireguard VPN
- Check the network routes on all machines with `ip route`
