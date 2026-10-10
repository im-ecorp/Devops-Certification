output "namespace" {
  description = "Dedicated namespace name."
  value       = kubernetes_namespace_v1.lab.metadata[0].name
}

output "deployments" {
  description = "Workload names, replicas, and rollout strategies."
  value = {
    mariadb = {
      name     = kubernetes_deployment_v1.mariadb.metadata[0].name
      replicas = kubernetes_deployment_v1.mariadb.spec[0].replicas
      strategy = kubernetes_deployment_v1.mariadb.spec[0].strategy[0].type
    }
    wordpress = {
      name     = kubernetes_deployment_v1.wordpress.metadata[0].name
      replicas = kubernetes_deployment_v1.wordpress.spec[0].replicas
      strategy = kubernetes_deployment_v1.wordpress.spec[0].strategy[0].type
    }
  }
}

output "persistent_volume_claims" {
  description = "PVC names, access modes, requested storage, and StorageClass."
  value = {
    for name, pvc in kubernetes_persistent_volume_claim_v1.data : name => {
      name               = pvc.metadata[0].name
      access_modes       = pvc.spec[0].access_modes
      storage            = pvc.spec[0].resources[0].requests["storage"]
      storage_class_name = pvc.spec[0].storage_class_name
    }
  }
}

output "services" {
  description = "Internal service names, types, and ports."
  value = {
    mariadb = {
      name = kubernetes_service_v1.mariadb.metadata[0].name
      type = kubernetes_service_v1.mariadb.spec[0].type
      port = kubernetes_service_v1.mariadb.spec[0].port[0].port
    }
    wordpress = {
      name = kubernetes_service_v1.wordpress.metadata[0].name
      type = kubernetes_service_v1.wordpress.spec[0].type
      port = kubernetes_service_v1.wordpress.spec[0].port[0].port
    }
  }
}
