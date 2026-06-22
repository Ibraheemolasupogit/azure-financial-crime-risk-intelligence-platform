param location string
param namePrefix string
param environment string
param tags object
resource namespace 'Microsoft.EventHub/namespaces@2024-01-01' = {
  name: '${namePrefix}-${environment}-evhns'
  location: location
  tags: tags
  sku: { name: 'Standard', tier: 'Standard', capacity: 1 }
  properties: { publicNetworkAccess: 'Disabled', minimumTlsVersion: '1.2', zoneRedundant: false }
}
resource hub 'Microsoft.EventHub/namespaces/eventhubs@2024-01-01' = {
  parent: namespace
  name: 'synthetic-transactions'
  properties: { partitionCount: 4, messageRetentionInDays: 1 }
}
output namespaceId string = namespace.id
