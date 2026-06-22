param location string
param namePrefix string
param environment string
param tags object
resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-${environment}-law'
  location: location
  tags: tags
  properties: { retentionInDays: 30, publicNetworkAccessForIngestion: 'Disabled', publicNetworkAccessForQuery: 'Disabled' }
}
output workspaceId string = workspace.id
