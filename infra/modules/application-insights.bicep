param location string
param namePrefix string
param environment string
param workspaceId string
param tags object
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namePrefix}-${environment}-appi'
  location: location
  tags: tags
  kind: 'web'
  properties: { Application_Type: 'web', WorkspaceResourceId: workspaceId, DisableLocalAuth: true }
}
output applicationInsightsId string = appInsights.id
