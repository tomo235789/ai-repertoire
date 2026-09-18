# バケットのオブジェクトを保持期間で自動的に移行・削除するライフサイクル規則。
# 移行・削除・非現行バージョン削除・未完了マルチパート中止を 1 つの規則にまとめる。

locals {
  # STANDARD_IA / ONEZONE_IA は作成から 30 日未満の移行を S3 が拒否する
  min_transition_days = contains(["STANDARD_IA", "ONEZONE_IA"], var.transition_storage_class) ? 30 : 1
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = var.bucket_name

  rule {
    id     = var.rule_id
    status = "Enabled"

    filter {
      prefix = var.prefix
    }

    dynamic "transition" {
      for_each = var.transition_days == null ? [] : [var.transition_days]
      content {
        days          = transition.value
        storage_class = var.transition_storage_class
      }
    }

    dynamic "expiration" {
      for_each = var.expiration_days == null ? [] : [var.expiration_days]
      content {
        days = expiration.value
      }
    }

    dynamic "noncurrent_version_expiration" {
      for_each = var.noncurrent_version_expiration_days == null ? [] : [var.noncurrent_version_expiration_days]
      content {
        noncurrent_days = noncurrent_version_expiration.value
      }
    }

    dynamic "abort_incomplete_multipart_upload" {
      for_each = var.abort_incomplete_multipart_days == null ? [] : [var.abort_incomplete_multipart_days]
      content {
        days_after_initiation = abort_incomplete_multipart_upload.value
      }
    }
  }

  lifecycle {
    precondition {
      condition     = var.transition_days == null || var.expiration_days == null || var.expiration_days > var.transition_days
      error_message = "expiration_days は transition_days より大きくすること（移行前に削除される規則は S3 が拒否する）。"
    }
    precondition {
      condition     = var.transition_days == null || var.transition_days >= local.min_transition_days
      error_message = "STANDARD_IA / ONEZONE_IA への移行は transition_days を 30 日以上にすること。"
    }
    precondition {
      condition     = var.transition_days != null || var.expiration_days != null || var.noncurrent_version_expiration_days != null || var.abort_incomplete_multipart_days != null
      error_message = "移行・削除・非現行削除・マルチパート中止のうち少なくとも 1 つを指定すること。"
    }
  }
}
