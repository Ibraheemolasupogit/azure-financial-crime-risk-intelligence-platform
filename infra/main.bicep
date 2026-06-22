targetScope = 'subscription'

@description('Azure region for illustrative resources.')
param location string
@description('Short environment name such as dev, test, or prod.')
@allowed(['dev', 'test', 'prod'])
param environment string = 'dev'
@description('Globally unique workload prefix; do not include secrets.')
param namePrefix string
@description('Tags applied to all supported resources.')
param tags object = {
  workload: 'financial-crime-risk-intelligence'
  dataClassification: 'synthetic-only'
}

var resourceGroupName = '${namePrefix}-${environment}-rg'

module resourceGroup 'modules/resource-group-scope.bicep' = {
  name: 'resource-group'
  params: { name: resourceGroupName, location: location, tags: tags }
}

module platform 'modules/networking.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'networking'
  params: { location: location, namePrefix: namePrefix, environment: environment, tags: tags }
  dependsOn: [resourceGroup]
}

module storage 'modules/storage.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'storage'
  params: { location: location, namePrefix: namePrefix, environment: environment, tags: tags }
  dependsOn: [resourceGroup]
}

module eventHubs 'modules/event-hubs.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'event-hubs'
  params: { location: location, namePrefix: namePrefix, environment: environment, tags: tags }
  dependsOn: [resourceGroup]
}

module keyVault 'modules/key-vault.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'key-vault'
  params: { location: location, namePrefix: namePrefix, environment: environment, tags: tags }
  dependsOn: [resourceGroup]
}

module logs 'modules/log-analytics.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'logs'
  params: { location: location, namePrefix: namePrefix, environment: environment, tags: tags }
  dependsOn: [resourceGroup]
}

module appInsights 'modules/application-insights.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'app-insights'
  params: { location: location, namePrefix: namePrefix, environment: environment, workspaceId: logs.outputs.workspaceId, tags: tags }
}

module registry 'modules/container-registry.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'registry'
  params: { location: location, namePrefix: namePrefix, environment: environment, tags: tags }
  dependsOn: [resourceGroup]
}

module machineLearning 'modules/machine-learning.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'machine-learning'
  params: {
    location: location
    namePrefix: namePrefix
    environment: environment
    storageAccountId: storage.outputs.storageAccountId
    keyVaultId: keyVault.outputs.keyVaultId
    containerRegistryId: registry.outputs.registryId
    applicationInsightsId: appInsights.outputs.applicationInsightsId
    tags: tags
  }
}

module synapse 'modules/synapse.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'synapse'
  params: { location: location, namePrefix: namePrefix, environment: environment, storageAccountId: storage.outputs.storageAccountId, tags: tags }
}

module purview 'modules/purview-placeholder.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'purview-placeholder'
  params: { location: location, namePrefix: namePrefix, environment: environment, tags: tags }
}

module monitoring 'modules/monitoring.bicep' = {
  scope: resourceGroup(resourceGroupName)
  name: 'monitoring'
  params: { location: location, namePrefix: namePrefix, environment: environment, workspaceId: logs.outputs.workspaceId, tags: tags }
}

output resourceGroupName string = resourceGroupName
output deploymentNotice string = 'Illustrative scaffold only. Review placeholders, permissions, quotas, and networking before deployment.'
