param location string
param namePrefix string
param environment string
param tags object
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: take(replace('${namePrefix}${environment}acr', '-', ''), 50)
  location: location
  tags: tags
  sku: { name: 'Premium' }
  properties: { adminUserEnabled: false, publicNetworkAccess: 'Disabled', policies: { retentionPolicy: { days: 7, status: 'enabled' } } }
}
output registryId string = registry.id
