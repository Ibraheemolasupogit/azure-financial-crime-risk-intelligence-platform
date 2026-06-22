param location string
param namePrefix string
param environment string
param tags object
resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: '${namePrefix}-${environment}-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: ['10.42.0.0/16'] }
    subnets: [
      { name: 'private-endpoints', properties: { addressPrefix: '10.42.1.0/24', privateEndpointNetworkPolicies: 'Disabled' } }
      { name: 'compute', properties: { addressPrefix: '10.42.2.0/24' } }
    ]
  }
}
// PLACEHOLDER: private endpoint resources and private DNS links depend on enabled services and subscription topology.
output virtualNetworkId string = vnet.id
