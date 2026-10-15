variable "location" {
  description = "Azure Region"
  type        = string
  default     = "swedencentral"
}

variable "allowed_ssh_cidr" {
  description = "The only address range allowed to SSH to the VM, e.g. the GitHub runner's IP as x.x.x.x/32"
  type        = string

  validation {
    condition     = !contains(["*", "0.0.0.0/0", "Internet", "Any"], var.allowed_ssh_cidr)
    error_message = "SSH must not be open to the whole internet. Use a single IP like 203.0.113.10/32."
  }
}
