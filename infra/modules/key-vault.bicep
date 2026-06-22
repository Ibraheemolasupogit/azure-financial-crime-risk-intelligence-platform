param location string
param namePrefix string
param environment string
param tags object
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: take('${namePrefix}-${environment}-kv', 24)
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enablePurgeProtection: true
    enableSoftDelete: true
    publicNetworkAccess: 'Disabled'
  }
}
output keyVaultId string = vault.id
