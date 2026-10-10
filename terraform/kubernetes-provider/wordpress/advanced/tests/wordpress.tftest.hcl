mock_provider "kubernetes" {}
mock_provider "random" {}

variables {
  kube_context = "mock-practice-context"
}

run "default_lab" {
  command = plan

  assert {
    condition     = output.namespace == "tf-k8s-practice"
    error_message = "The lab must use its dedicated default namespace."
  }
  assert {
    condition = length(output.deployments) == 2 && alltrue([
      for name, deployment in output.deployments : deployment.name == name && deployment.replicas == "1" && deployment.strategy == "Recreate"
    ])
    error_message = "Exactly WordPress and MariaDB must each have one replica and Recreate strategy."
  }
  assert {
    condition = length(output.persistent_volume_claims) == 2 && alltrue([
      for name, pvc in output.persistent_volume_claims : pvc.name == "${name}-data" && pvc.storage == "5Gi" && toset(pvc.access_modes) == toset(["ReadWriteOnce"])
    ])
    error_message = "Both applications must have separate 5Gi ReadWriteOnce PVCs."
  }
  assert {
    condition = length(output.services) == 2 && alltrue([
      for name, service in output.services : service.name == name && service.type == "ClusterIP"
    ]) && output.services.wordpress.port == 80 && output.services.mariadb.port == 3306
    error_message = "Only internal ClusterIP services on the expected ports are allowed."
  }
}

run "custom_storage_and_namespace" {
  command = plan
  variables {
    namespace              = "tf-wordpress-custom"
    storage_class_name     = "practice-storage"
    database_storage_size  = "8Gi"
    wordpress_storage_size = "3Gi"
  }
  assert {
    condition     = output.namespace == "tf-wordpress-custom"
    error_message = "The namespace override must reach the WordPress module."
  }
  assert {
    condition = output.persistent_volume_claims.mariadb.storage == "8Gi" && output.persistent_volume_claims.wordpress.storage == "3Gi" && alltrue([
      for pvc in output.persistent_volume_claims : pvc.storage_class_name == "practice-storage"
    ])
    error_message = "The PVC size and StorageClass overrides must reach both PVCs."
  }
}

run "reject_empty_context" {
  command = plan
  variables {
    kube_context = " "
  }
  expect_failures = [var.kube_context]
}
