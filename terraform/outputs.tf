output "vm_public_ip" {
  description = "Public IP address of the ICLIM VM"

  value = azurerm_public_ip.iclim_vm_ip.ip_address
}