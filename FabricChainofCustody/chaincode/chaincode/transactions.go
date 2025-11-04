package chaincode

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

// SmartContract defines the base structure for your chaincode.
type SmartContract struct {
	contractapi.Contract
}

// Asset represents a verifiable credential on the ledger.
type Asset struct {
	Status          string `json:"status"`            // "active" or "revoked"
	Timestamp       string `json:"timestamp"`         // ISO8601 format or Unix timestamp
	OwnerDID        string `json:"owner_did"`         // Credential owner's DID
	IssuerDID       string `json:"issuer_did"`        // Issuer's DID
	CredentialID    string `json:"credential_id"`     // Unique identifier of the credential
	CredentialHash  string `json:"credential_hash"`
	LastModifierDID string `json:"last_modifier_did"` // DID of the last modifier
	PreviousCredentialID string `json:"previous_credential_id"`
}


// CreateAsset creates a new credential on the ledger.
func (s *SmartContract) CreateAsset(
	ctx contractapi.TransactionContextInterface,
	credentialID string, status string, issuerDID string,
	ownerDID string, credentialHash string, timestamp string, previousCredentialID string) error {

	exists, err := s.AssetExists(ctx, credentialID)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("a credencial %s já existe", credentialID)
	}

	asset := Asset{
		CredentialID:         credentialID,
		Status:               status,
		IssuerDID:            issuerDID,
		OwnerDID:             ownerDID,
		CredentialHash:       credentialHash,
		Timestamp:            timestamp,
		LastModifierDID:      ownerDID,
		PreviousCredentialID: previousCredentialID,
	}
	assetJSON, err := json.Marshal(asset)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(credentialID, assetJSON)
}

// TransferOwnership updates the owner (OwnerDID) of an existing credential.
func (s *SmartContract) TransferOwnership(ctx contractapi.TransactionContextInterface,
	 	credentialID string, newOwnerDID string) error {

	asset, err := s.ReadAsset(ctx, credentialID)
	if err != nil {
		return err
	}

	asset.OwnerDID = newOwnerDID

	assetJSON, err := json.Marshal(asset)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(credentialID, assetJSON)
}


// RevokeAsset changes the status of a credential to "revoked".
func (s *SmartContract) RevokeAsset(ctx contractapi.TransactionContextInterface,
		credentialID string) error {
			
	asset, err := s.ReadAsset(ctx, credentialID)
	if err != nil {
		return err
	}

	asset.Status = "revoked"
	asset.Timestamp = time.Now().UTC().Format(time.RFC3339)

	assetJSON, err := json.Marshal(asset)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(credentialID, assetJSON)
}