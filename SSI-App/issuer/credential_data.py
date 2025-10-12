from dataclasses import dataclass

@dataclass
class CredentialData:
    expert_name: str
    issuing_judge_id: str
    evidence_hash: str
    authorization_level: str
    court_jurisdiction: str
    subject_did: str