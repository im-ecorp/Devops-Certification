mock_provider "kubernetes" {}

variables {
  db_password  = "test-password-only"
  kube_context = "test-context"
}

run "validate_basic_deployment" {
  command = plan

  assert {
    condition     = kubernetes_namespace.wp_namespace.metadata[0].name == "tf-k8s-basic-wordpress"
    error_message = "Namespace must be fixed for basic lab."
  }

  assert {
    condition     = kubernetes_service.wordpress.spec[0].type == "ClusterIP"
    error_message = "WordPress should only be exposed internally."
  }

  assert {
    condition     = contains(kubernetes_persistent_volume_claim.mysql_pvc.spec[0].access_modes, "ReadWriteOnce")
    error_message = "Database PVC must require ReadWriteOnce."
  }
}
