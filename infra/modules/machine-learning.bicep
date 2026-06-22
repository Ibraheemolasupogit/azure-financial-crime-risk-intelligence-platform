param location string
param namePrefix string
param environment string
param storageAccountId string
param keyVaultId string
param containerRegistryId string
param applicationInsightsId string
param tags object
resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: '${namePrefix}-${environment}-mlw'
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    storageAccount: storageAccountId
    keyVault: keyVaultId
    containerRegistry: containerRegistryId
    applicationInsights: applicationInsightsId
    publicNetworkAccess: 'Disabled'
  }
}
output workspaceId string = workspace.id
