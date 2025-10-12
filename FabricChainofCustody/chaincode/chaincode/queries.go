package chaincode

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

// ReadAsset retrieves a credential from the ledger by its ID.
func (s *SmartContract) ReadAsset(ctx contractapi.TransactionContextInterface, credentialID string) (*Asset, error) {
	assetJSON, err := ctx.GetStub().GetState(credentialID)
	if err != nil {
		return nil, fmt.Errorf("falha ao ler do world state: %v", err)
	}
	if assetJSON == nil {
		return nil, fmt.Errorf("a credencial %s não existe", credentialID)
	}

	var asset Asset
	err = json.Unmarshal(assetJSON, &asset)
	if err != nil {
		return nil, err
	}
	return &asset, nil
}

// AssetExists checks whether a credential with the specified ID exists in the ledger.
func (s *SmartContract) AssetExists(ctx contractapi.TransactionContextInterface, credentialID string) (bool, error) {
	assetJSON, err := ctx.GetStub().GetState(credentialID)
	if err != nil {
		return false, fmt.Errorf("falha ao ler do world state: %v", err)
	}
	return assetJSON != nil, nil
}