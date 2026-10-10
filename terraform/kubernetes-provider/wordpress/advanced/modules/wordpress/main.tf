locals {
  database_name = "wordpress"
  database_user = "wordpress"
  labels = {
    mariadb = {
      "app.kubernetes.io/name"      = "mariadb"
      "app.kubernetes.io/part-of"   = "wordpress-practice"
      "app.kubernetes.io/component" = "database"
    }
    wordpress = {
      "app.kubernetes.io/name"      = "wordpress"
      "app.kubernetes.io/part-of"   = "wordpress-practice"
      "app.kubernetes.io/component" = "web"
    }
  }
}

resource "kubernetes_namespace_v1" "lab" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of"    = "wordpress-practice"
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

resource "random_password" "database" {
  length  = 32
  special = false
}

resource "random_password" "root" {
  length  = 32
  special = false
}

resource "kubernetes_secret_v1" "database" {
  metadata {
    name      = "wordpress-database"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
  }
  type = "Opaque"
  data = {
    database-password = random_password.database.result
    root-password     = random_password.root.result
  }
}

resource "kubernetes_persistent_volume_claim_v1" "data" {
  for_each = {
    mariadb   = var.database_storage_size
    wordpress = var.wordpress_storage_size
  }
  metadata {
    name      = "${each.key}-data"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
    labels    = local.labels[each.key]
  }
  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = var.storage_class_name
    resources {
      requests = { storage = each.value }
    }
  }
  # Avoid waiting for binding before a pod exists with WaitForFirstConsumer.
  wait_until_bound = false
}

resource "kubernetes_deployment_v1" "mariadb" {
  metadata {
    name      = "mariadb"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
    labels    = local.labels.mariadb
  }
  spec {
    replicas = 1
    strategy { type = "Recreate" }
    selector { match_labels = local.labels.mariadb }
    template {
      metadata { labels = local.labels.mariadb }
      spec {
        automount_service_account_token = false
        container {
          name  = "mariadb"
          image = "mariadb:11.4"
          port { container_port = 3306 }
          env {
            name  = "MARIADB_DATABASE"
            value = local.database_name
          }
          env {
            name  = "MARIADB_USER"
            value = local.database_user
          }
          env {
            name = "MARIADB_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.database.metadata[0].name
                key  = "database-password"
              }
            }
          }
          env {
            name = "MARIADB_ROOT_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.database.metadata[0].name
                key  = "root-password"
              }
            }
          }
          volume_mount {
            name       = "data"
            mount_path = "/var/lib/mysql"
          }
          resources {
            requests = { cpu = "100m", memory = "256Mi" }
            limits   = { cpu = "500m", memory = "512Mi" }
          }
          startup_probe {
            exec { command = ["healthcheck.sh", "--connect", "--innodb_initialized"] }
            period_seconds    = 10
            timeout_seconds   = 5
            failure_threshold = 30
          }
          readiness_probe {
            exec { command = ["healthcheck.sh", "--connect", "--innodb_initialized"] }
            period_seconds  = 10
            timeout_seconds = 5
          }
          liveness_probe {
            tcp_socket { port = 3306 }
            period_seconds    = 20
            timeout_seconds   = 5
            failure_threshold = 3
          }
        }
        volume {
          name = "data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.data["mariadb"].metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_deployment_v1" "wordpress" {
  metadata {
    name      = "wordpress"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
    labels    = local.labels.wordpress
  }
  spec {
    replicas = 1
    strategy { type = "Recreate" }
    selector { match_labels = local.labels.wordpress }
    template {
      metadata { labels = local.labels.wordpress }
      spec {
        automount_service_account_token = false
        container {
          name  = "wordpress"
          image = "wordpress:php8.3-apache"
          port { container_port = 80 }
          env {
            name  = "WORDPRESS_DB_HOST"
            value = "${kubernetes_service_v1.mariadb.metadata[0].name}:3306"
          }
          env {
            name  = "WORDPRESS_DB_NAME"
            value = local.database_name
          }
          env {
            name  = "WORDPRESS_DB_USER"
            value = local.database_user
          }
          env {
            name = "WORDPRESS_DB_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.database.metadata[0].name
                key  = "database-password"
              }
            }
          }
          volume_mount {
            name       = "data"
            mount_path = "/var/www/html"
          }
          resources {
            requests = { cpu = "100m", memory = "128Mi" }
            limits   = { cpu = "500m", memory = "512Mi" }
          }
          startup_probe {
            http_get {
              path = "/wp-login.php"
              port = 80
            }
            period_seconds    = 10
            timeout_seconds   = 5
            failure_threshold = 30
          }
          readiness_probe {
            http_get {
              path = "/wp-login.php"
              port = 80
            }
            period_seconds  = 10
            timeout_seconds = 5
          }
          liveness_probe {
            tcp_socket { port = 80 }
            period_seconds    = 20
            timeout_seconds   = 5
            failure_threshold = 3
          }
        }
        volume {
          name = "data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.data["wordpress"].metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "mariadb" {
  metadata {
    name      = "mariadb"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
    labels    = local.labels.mariadb
  }
  spec {
    type     = "ClusterIP"
    selector = local.labels.mariadb
    port {
      port        = 3306
      target_port = 3306
    }
  }
}

resource "kubernetes_service_v1" "wordpress" {
  metadata {
    name      = "wordpress"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
    labels    = local.labels.wordpress
  }
  spec {
    type     = "ClusterIP"
    selector = local.labels.wordpress
    port {
      port        = 80
      target_port = 80
    }
  }
}
