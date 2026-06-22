param location string
param namePrefix string
param environment string
param tags object
// PLACEHOLDER: Purview collections, scans, credentials, and role assignments require tenant-specific governance decisions.
resource account 'Microsoft.Purview/accounts@2021-12-01' = {
  name: '${namePrefix}-${environment}-purview'
  location: location
  tags: union(tags, { configurationStatus: 'placeholder' })
  identity: { type: 'SystemAssigned' }
  properties: { publicNetworkAccess: 'Disabled' }
}
output purviewAccountId string = account.id
