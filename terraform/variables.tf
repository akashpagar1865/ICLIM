variable "location" {
  description = "Azure Region"
  type        = string
  default     = "swedencentral"
}

variable "public_key_path" {
  description = "Path to the SSH public key"
  type        = string
}