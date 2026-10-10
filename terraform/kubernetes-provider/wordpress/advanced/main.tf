module "wordpress" {
  source = "./modules/wordpress"
  providers = {
    kubernetes = kubernetes
    random     = random
  }

  namespace              = var.namespace
  storage_class_name     = var.storage_class_name
  database_storage_size  = var.database_storage_size
  wordpress_storage_size = var.wordpress_storage_size
}
