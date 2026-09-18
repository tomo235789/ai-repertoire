variable "name" {
  description = "ポリシー名（アカウント内で一意。変更すると再作成）"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{1,128}$", var.name))
    error_message = "name は 1〜128 文字の英数字と + = , . @ _ - にすること。"
  }
}

variable "description" {
  description = "ポリシーの説明（後から変更すると再作成になる）"
  type        = string
  default     = "Read-only access"
}

variable "allowed_actions" {
  description = "許可する読み取りアクション。<service>:Get* / List* / Describe* で始まるものだけ受け付ける（例: s3:GetObject、s3:ListBucket、ec2:DescribeInstances）"
  type        = list(string)
  validation {
    condition     = length(var.allowed_actions) > 0
    error_message = "allowed_actions は 1 つ以上指定すること。"
  }
  validation {
    condition     = alltrue([for a in var.allowed_actions : can(regex("^[a-z0-9-]+:(Get|List|Describe)[A-Za-z0-9]*\\*?$", a))])
    error_message = "allowed_actions は <service>:Get… / List… / Describe… の読み取りアクションだけにすること（例: s3:GetObject、s3:List*、ec2:DescribeInstances）。"
  }
}

variable "resource_arns" {
  description = "読み取りを許可するリソース ARN。Describe* / List* のようにリソースレベル権限が無いアクションには [\"*\"] を渡す"
  type        = list(string)
  validation {
    condition     = length(var.resource_arns) > 0 && alltrue([for r in var.resource_arns : r == "*" || startswith(r, "arn:")])
    error_message = "resource_arns は 1 つ以上の ARN（arn:...）か \"*\" にすること。"
  }
}

variable "path" {
  description = "ポリシーの IAM パス"
  type        = string
  default     = "/"
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
