terraform {
  # 1.9 以上: tests/ が override_during = plan（mock の ARN を plan 時に固定）を使う
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
