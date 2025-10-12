anoncreds_schema = {
    "name": "anoncred-forensic-cert",
    "version": "1.0.0",
    "description": "A certificate for a piece of forensic evidence.",
    "type": "AnoncredSchemaV1",
    "author": "did:prism:example",  # Must overwrite it!
    "tags": [
        "forensic",
        "evidence",
        "chain-of-custody"
    ],
    "schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1
            },
            "version": {
                "type": "string",
                "minLength": 1
            },
            "attrNames": {
                "type": "array",
                "items": {
                    "type": "string",
                    "minLength": 1
                },
                "minItems": 1,
                "maxItems": 125,
                "uniqueItems": True
            },
            "issuerId": {
                "type": "string",
                "minLength": 1
            },
        },
        "name": "Forensic Evidence Schema",
        "version": "1.0",
        "attrNames": [
            "expert_name",
            "issuing_judge_id",
            "evidence_hash",
            "authorization_level",
            "court_jurisdiction",
            "subject_did"
        ],
        "issuerId": "did:prism:example"  # Must overwrite it!
    },
    "required": [
        "name",
        "version"
    ],
    "additionalProperties": True
}