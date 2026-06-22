param location string
param namePrefix string
param environment string
param storageAccountId string
param tags object
resource workspace 'Microsoft.Synapse/workspaces@2021-06-01' = {
  name: '${namePrefix}-${environment}-syn'
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    defaultDataLakeStorage: { accountUrl: 'https://${last(split(storageAccountId, '/'))}.dfs.core.windows.net', filesystem: 'synapse' }
    managedResourceGroupName: '${namePrefix}-${environment}-syn-managed-rg'
    publicNetworkAccess: 'Disabled'
    managedVirtualNetwork: 'default'
  }
}
output workspaceId string = workspace.id
