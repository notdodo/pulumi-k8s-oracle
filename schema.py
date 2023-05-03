from diagrams import Cluster, Diagram, Edge
from diagrams.generic.device import Tablet
from diagrams.generic.network import VPN
from diagrams.k8s.infra import Master, Node
from diagrams.oci.network import SecurityLists
from diagrams.saas.cdn import Cloudflare

graph_attr = {
    "layout":"dot",
    "splines":"curved",
    "bgcolor": "transparent",
    "beautify": "true",
    "center": "true",
}


with Diagram("", show=True, direction="LR", graph_attr=graph_attr,filename="pulumi_k8s_oracle"):
    with Cluster("Tenancy A"):
        with Cluster("k8sMasterCompartment"):
            with Cluster("Instance - 10.0.10.10"):
                master = Master("k8smaster")  
                master_wg = VPN("wireguard")
            master_sl = SecurityLists("SecurityList\n22/tcp;51000/udp")
    with Cluster("Tenancy B"):
        with Cluster("k8sWorkerCompartment"):
            with Cluster("Instance - 10.0.10.11"):
                worker = Node("k8sworker")
                worker_wg =  VPN("wireguard")
            worker_sl = SecurityLists("SecurityList\n22/tcp;51000/udp")
    cf = Cloudflare("k8s.thedodo.xyz")
    user = Tablet("user")
    user_wg = VPN("wireguard")
    master >> Edge(label="10.0.100.1/32") << master_wg
    master_wg >> Edge(label="wg0") << worker_wg
    worker >> Edge(label="10.0.100.2/32") << worker_wg
    cf - master_sl >> master
    worker_sl >> worker
    user - master_sl
    user - worker_sl
    user - user_wg >> Edge(label="wg0") << master_wg
    # cf - worker_sl >> worker_fw_in >> worker

