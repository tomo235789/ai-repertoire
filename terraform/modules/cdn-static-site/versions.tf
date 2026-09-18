terraform {
  required_version = ">= 1.9" # tftest の override_during = plan を使う
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0" }
  }
}
