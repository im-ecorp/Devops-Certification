# 1. Isolate the practice environment in its own namespace
resource "kubernetes_namespace" "wp_namespace" {
  metadata {
    name = "tf-k8s-basic-wordpress"
  }
}

# 2. Store the database password as a Kubernetes Secret
resource "kubernetes_secret" "db_password" {
  metadata {
    name      = "mysql-pass"
    namespace = kubernetes_namespace.wp_namespace.metadata[0].name
  }

  data = {
    password = var.db_password
  }

  type = "Opaque"
}

# 3. Request persistent storage for the database
resource "kubernetes_persistent_volume_claim" "mysql_pvc" {
  metadata {
    name      = "mysql-pvc"
    namespace = kubernetes_namespace.wp_namespace.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "5Gi"
      }
    }
    storage_class_name = var.storage_class_name
  }
  # Wait until bound ensures the PVC binds when the Pod is scheduled (useful for local clusters)
  wait_until_bound = false
}

# 4. Request persistent storage for WordPress files
resource "kubernetes_persistent_volume_claim" "wp_pvc" {
  metadata {
    name      = "wp-pvc"
    namespace = kubernetes_namespace.wp_namespace.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "5Gi"
      }
    }
    storage_class_name = var.storage_class_name
  }
  wait_until_bound = false
}

# 5. Internal network service for the database
resource "kubernetes_service" "mysql" {
  metadata {
    name      = "wordpress-mysql"
    namespace = kubernetes_namespace.wp_namespace.metadata[0].name
  }
  spec {
    selector = {
      app  = "wordpress"
      tier = "mysql"
    }
    port {
      port = 3306
    }
    type = "ClusterIP" # Internal-only database service
  }
}

# 6. Database Deployment
resource "kubernetes_deployment" "mysql" {
  metadata {
    name      = "wordpress-mysql"
    namespace = kubernetes_namespace.wp_namespace.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app  = "wordpress"
        tier = "mysql"
      }
    }
    strategy {
      type = "Recreate" # Avoids two pods fighting for the ReadWriteOnce volume during updates
    }
    template {
      metadata {
        labels = {
          app  = "wordpress"
          tier = "mysql"
        }
      }
      spec {
        container {
          name  = "mysql"
          image = "mariadb:11.4"

          env {
            name  = "MARIADB_RANDOM_ROOT_PASSWORD"
            value = "yes"
          }
          env {
            name  = "MARIADB_DATABASE"
            value = "wordpress"
          }
          env {
            name  = "MARIADB_USER"
            value = "wordpress"
          }
          env {
            name = "MARIADB_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_password.metadata[0].name
                key  = "password"
              }
            }
          }

          port {
            container_port = 3306
            name           = "mysql"
          }

          volume_mount {
            name       = "mysql-persistent-storage"
            mount_path = "/var/lib/mysql"
          }
        }

        volume {
          name = "mysql-persistent-storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.mysql_pvc.metadata[0].name
          }
        }
      }
    }
  }
}

# 7. Internal network service for WordPress
resource "kubernetes_service" "wordpress" {
  metadata {
    name      = "wordpress"
    namespace = kubernetes_namespace.wp_namespace.metadata[0].name
  }
  spec {
    selector = {
      app  = "wordpress"
      tier = "frontend"
    }
    port {
      port = 80
    }
    type = "ClusterIP" # Do not expose externally (requires port-forwarding to access)
  }
}

# 8. WordPress Deployment
resource "kubernetes_deployment" "wordpress" {
  metadata {
    name      = "wordpress"
    namespace = kubernetes_namespace.wp_namespace.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app  = "wordpress"
        tier = "frontend"
      }
    }
    strategy {
      type = "Recreate"
    }
    template {
      metadata {
        labels = {
          app  = "wordpress"
          tier = "frontend"
        }
      }
      spec {
        container {
          name  = "wordpress"
          image = "wordpress:php8.3-apache"

          env {
            name  = "WORDPRESS_DB_HOST"
            value = "wordpress-mysql:3306"
          }
          env {
            name  = "WORDPRESS_DB_NAME"
            value = "wordpress"
          }
          env {
            name  = "WORDPRESS_DB_USER"
            value = "wordpress"
          }
          env {
            name = "WORDPRESS_DB_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_password.metadata[0].name
                key  = "password"
              }
            }
          }

          port {
            container_port = 80
            name           = "wordpress"
          }

          volume_mount {
            name       = "wordpress-persistent-storage"
            mount_path = "/var/www/html"
          }
        }

        volume {
          name = "wordpress-persistent-storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.wp_pvc.metadata[0].name
          }
        }
      }
    }
  }
}
