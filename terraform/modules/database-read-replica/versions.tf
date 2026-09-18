terraform {
  # validation ブロックで別の variable（replicate_source_db）を参照するため 1.9 以上
  required_version = ">= 1.9"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0" }
  }
}
