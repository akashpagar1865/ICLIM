terraform {
  required_version = ">= 1.15.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "iclim_rg" {
  name     = "iclim-rg"
  location = var.location
}

resource "azurerm_virtual_network" "iclim_vnet" {
  name                = "iclim-vnet"
  location            = azurerm_resource_group.iclim_rg.location
  resource_group_name = azurerm_resource_group.iclim_rg.name
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "default_subnet" {
  name                 = "default-subnet"
  resource_group_name  = azurerm_resource_group.iclim_rg.name
  virtual_network_name = azurerm_virtual_network.iclim_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "iclim_public_ip" {
  name                = "iclim-vm-ip"
  location            = azurerm_resource_group.iclim_rg.location
  resource_group_name = azurerm_resource_group.iclim_rg.name

  allocation_method = "Static"
  sku               = "Standard"
}

resource "azurerm_network_security_group" "iclim_nsg" {
  name                = "iclim-vm-nsg"
  location            = azurerm_resource_group.iclim_rg.location
  resource_group_name = azurerm_resource_group.iclim_rg.name

  security_rule {
    name      = "Allow-SSH"
    priority  = 1000
    direction = "Inbound"
    access    = "Allow"
    protocol  = "Tcp"

    source_port_range      = "*"
    destination_port_range = "22"

    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "iclim_nic" {
  name                = "iclim-vm-nic"
  location            = azurerm_resource_group.iclim_rg.location
  resource_group_name = azurerm_resource_group.iclim_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.default_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.iclim_public_ip.id
  }
}

resource "azurerm_network_interface_security_group_association" "iclim_nic_nsg" {
  network_interface_id      = azurerm_network_interface.iclim_nic.id
  network_security_group_id = azurerm_network_security_group.iclim_nsg.id
}

resource "azurerm_linux_virtual_machine" "iclim_vm" {
  name                = "iclim-vm"
  resource_group_name = azurerm_resource_group.iclim_rg.name
  location            = azurerm_resource_group.iclim_rg.location
  size                = "Standard_D2ls_v6"

  admin_username = "azureuser"

  network_interface_ids = [
    azurerm_network_interface.iclim_nic.id
  ]

  admin_ssh_key {
    username   = "azureuser"
    public_key = file("C:/Users/Sayali PC/.ssh/iclim_ed25519.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }

  disable_password_authentication = true
}