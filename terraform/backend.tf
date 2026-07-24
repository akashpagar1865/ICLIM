terraform {
  backend "azurerm" {
    resource_group_name  = "iclim-tfstate-rg"
    storage_account_name = "iclimtfstate1865"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}