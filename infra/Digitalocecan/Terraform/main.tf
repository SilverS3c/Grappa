terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# Set the variable value in *.tfvars file
# or using -var="do_token=..." CLI option
variable "do_token" {}
variable "kubeconfig_filename" {}

# Configure the DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

resource "digitalocean_kubernetes_cluster" "grappa-cluster" {
  name = "grappa-cluster"
  region = "nyc3"
  version = "latest"

  node_pool {
    name = "worker-pool"
    size = "s-2vcpu-4gb"
    node_count = 2
  }
}

resource "local_file" "kubeconfig" {
  content = digitalocean_kubernetes_cluster.grappa-cluster.kube_config[0].raw_config
  filename = var.kubeconfig_filename
}

output "cluster_ip" {
  value = digitalocean_kubernetes_cluster.grappa-cluster.endpoint
}

output "kubectl_command" {
  value = "helm --kubeconfig=${var.kubeconfig_filename} install grappa-infra ../Helm"
}