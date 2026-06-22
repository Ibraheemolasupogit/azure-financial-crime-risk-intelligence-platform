param location string
param namePrefix string
param environment string
param workspaceId string
param tags object
resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${namePrefix}-${environment}-ag'
  location: 'global'
  tags: tags
  properties: { groupShortName: 'fcir-alerts', enabled: true }
}
// PLACEHOLDER: alert recipients and service-specific diagnostic settings require approved operational routing.
output actionGroupId string = actionGroup.id
output logAnalyticsWorkspaceId string = workspaceId
