import json
import os
from pathlib import Path

# Supported languages
DEFAULT_LANGUAGE = "en"
_CURRENT_LANGUAGE = None

MESSAGES = {
    "pt": {
        # General
        "error_status": "Ocorreu um erro. Status: {status}",
        "error_happened": "Ocorreu um erro: {error}",
        "exiting_program": "Saindo do programa...",
        "did_created": "DID criado: {did}",

        # Holder Interface - LogIn & Main Menu
        "holder_login_prompt": "(LogIn) Digite seu nome completo:\n",
        "holder_current_did": "Seu DID atual: {did}",
        "holder_name_not_registered": "Atenção! Nome não registrado no banco de dados.",
        "holder_create_a_did": "Crie um DID!",
        "holder_main_menu": """Selecione:
\t1. Criar DID.
\t2. Operação no Sistema de Cadeia de Custódia
\t0. Sair
""",
        "holder_did_updated": "DID atualizado no sistema.",
        "holder_need_did_and_cred": "Crie um DID antes! E tenha uma credencial para acesso!",

        # Holder Interface - Chain of Custody Operations Menu
        "holder_coc_menu": """Selecione:
\t1. Criar Evidência.
\t2. Atualizar Evidência.
\t3. Consulta metadados Cadeia de Custódia
\t4. Verificar Cadeia de Custódia e obter payloads
\t5. Mudar owner Cadeia de Custódia
\t0. Sair
""",
        "prompt_tags": "Digite tags (separadas por vírgula) se desejar, ou aperte enter: ",
        "prompt_evidence_hash": "Digite o hash da evidência: ",
        "prompt_answer_questions": "Responda...",
        "create_evidence_response": "Resposta CreateEvidence: {response}",
        "update_evidence_response": "Resposta UpdateEvidence: {response}",
        "transfer_ownership_response": "Resposta Transfer Ownership: {response}",
        "prompt_new_owner_did": "Digite o did do novo 'dono' da evidência: ",

        # Chain of Custody Inspection Output
        "chain_metadata_header": "Metadados da Cadeia de Custódia: ",
        "chain_start": "\n--- INÍCIO DA CADEIA DE CUSTÓDIA ---",
        "chain_link": "\n------------------ Elo {link_num} ------------------",
        "chain_db_record": "\n[+] Registro do Banco de Dados:",
        "chain_ledger_data": "\n[+] Dados do Ledger (Blockchain):",
        "chain_end": "\n------------------ FIM DA CADEIA ------------------\n",
        "chain_payloads_header": "Payloads da Cadeia de Custódia: ",
        "payloads_start": "----- INÍCIO PAYLOADS -----",
        "payloads_end": "----- FIM PAYLOADS -----",

        # Issuer Interface - Main Menu
        "issuer_main_menu": """Selecione:
\t1. Criar DID, Schema e Credential Definition.
\t2. Criar conexão e enviar para Holder.
\t3. Assinar Credencial
\t0. Sair
""",
        "issuer_did_trusted": "DID adicionado à lista de Issuers confiáveis!",
        "schema_created": "Schema criado: {schema}",
        "cred_def_created": "Credential Definition criado: {cred_def}",

        # Issuer Interface - Connection Option
        "issuer_connection_intro": "Para que a conexão prossiga e a credencial seja gerada responda...",
        "issuer_prompt_expert_name": "Qual o nome completo do perito que receberá a credencial? \n",
        "issuer_identity_found": "Sucesso! A identidade de '{name}' foi encontrada.",
        "issuer_identity_data": "   Dados: {data}",
        "issuer_identity_not_found": "A identidade '{name}' não foi encontrada no banco de dados. O perito precisa cadastrar um DID!",
        "issuer_prompt_connection_label": "Dê um rótulo para esta nova conexão: ",
        "mockdb_response_status": "MockDB respondeu com status: {status}",
        "invitation_sent_holder_status": "Convite enviado. Agente Holder respondeu com status: {status}",

        # Issuer Interface - Credential Issuance Option
        "issuer_ensure_invitation_accepted": "Esteja certo de que o perito aceitou sua solicitação.",
        "issuer_prompt_validity": "Qual será o tempo de validade da credencial gerada (em segundos)? ",
        "issuer_prompt_evidence_hash": "Qual o hash da evidência digital? ",
        "issuer_prompt_jurisdiction": "Digite a jurisdição do tribunal (ex: Comarca de Florianópolis, 4ª Vara Federal): ",
        "issuer_prompt_judge_id": "Qual seu identificador (id)? ",
        "access_levels_description": """ Níveis de Acesso 
\t0 (Restricted Read-only): Apenas alguns dados e metadados poderão ser lidos.
\t1 (Read-Only): Todos os dados da cadeia de custódia poderão ser visualizados
\t2 (Read and Write): Tem acesso à cadeia de custódia e pode adicionar dados.
\t99 (ADMIN): Acesso total para modificações, apenas deve ser usado em casos extremos.
            (Como para transferir a custódia de uma evidência de um perito que não está mais elegível 
            a utilizar este ecossistema a outro.)
""",
        "issuer_prompt_auth_level": "Qual o nível de acesso o perito terá à evidência (digite somente um número)? ",
        "offer_sent_holder_response": "Convite enviado. Agente Holder respondeu com: {response}",

        # Webhook Handler
        "webhook_received": "📩 Webhook recebido:",
        "connection_accepted": "Conexão aceita com {name}, de DID {did}",
        "verifier_accepted_data": "O Verifier aceitou os dados com sucesso.",
        "error_calling_verifier": "Erro ao chamar API do Verifier: {status} {text}",
    },

    "en": {
        # General
        "error_status": "An error occurred. Status: {status}",
        "error_happened": "Error happened: {error}",
        "exiting_program": "Exiting program...",
        "did_created": "DID created: {did}",

        # Holder Interface - LogIn & Main Menu
        "holder_login_prompt": "(LogIn) Enter your full name:\n",
        "holder_current_did": "Your current DID: {did}",
        "holder_name_not_registered": "Warning! Name not registered in the database.",
        "holder_create_a_did": "Create a DID!",
        "holder_main_menu": """Select an option:
\t1. Create DID.
\t2. Chain of Custody System Operation
\t0. Exit
""",
        "holder_did_updated": "DID updated in the system.",
        "holder_need_did_and_cred": "Create a DID first! And ensure you hold an access credential!",

        # Holder Interface - Chain of Custody Operations Menu
        "holder_coc_menu": """Select an option:
\t1. Create Evidence.
\t2. Update Evidence.
\t3. Query Chain of Custody Metadata
\t4. Verify Chain of Custody and retrieve payloads
\t5. Transfer Chain of Custody Ownership
\t0. Exit
""",
        "prompt_tags": "Enter tags (comma-separated) if desired, or press Enter: ",
        "prompt_evidence_hash": "Enter evidence hash: ",
        "prompt_answer_questions": "Answer the following questions...",
        "create_evidence_response": "CreateEvidence response: {response}",
        "update_evidence_response": "UpdateEvidence response: {response}",
        "transfer_ownership_response": "Transfer Ownership response: {response}",
        "prompt_new_owner_did": "Enter the DID of the new evidence owner: ",

        # Chain of Custody Inspection Output
        "chain_metadata_header": "Chain of Custody Metadata: ",
        "chain_start": "\n--- START OF CHAIN OF CUSTODY ---",
        "chain_link": "\n------------------ Link {link_num} ------------------",
        "chain_db_record": "\n[+] Database Record:",
        "chain_ledger_data": "\n[+] Ledger Data (Blockchain):",
        "chain_end": "\n------------------ END OF CHAIN ------------------\n",
        "chain_payloads_header": "Chain of Custody Payloads: ",
        "payloads_start": "----- START OF PAYLOADS -----",
        "payloads_end": "----- END OF PAYLOADS -----",

        # Issuer Interface - Main Menu
        "issuer_main_menu": """Select an option:
\t1. Create DID, Schema, and Credential Definition.
\t2. Create connection invitation and send to Holder.
\t3. Sign / Issue Credential
\t0. Exit
""",
        "issuer_did_trusted": "DID added to the list of trusted Issuers!",
        "schema_created": "Schema created: {schema}",
        "cred_def_created": "Credential Definition created: {cred_def}",

        # Issuer Interface - Connection Option
        "issuer_connection_intro": "To proceed with connection and credential generation, answer the following...",
        "issuer_prompt_expert_name": "What is the full name of the forensic expert receiving the credential?\n",
        "issuer_identity_found": "Success! Identity for '{name}' was found.",
        "issuer_identity_data": "   Data: {data}",
        "issuer_identity_not_found": "Identity '{name}' was not found in the database. The expert must register a DID first!",
        "issuer_prompt_connection_label": "Provide a label for this new connection: ",
        "mockdb_response_status": "MockDB responded with status: {status}",
        "invitation_sent_holder_status": "Invitation sent. Holder agent responded with status: {status}",

        # Issuer Interface - Credential Issuance Option
        "issuer_ensure_invitation_accepted": "Make sure the forensic expert has accepted your connection request.",
        "issuer_prompt_validity": "What is the validity period of the credential (in seconds)? ",
        "issuer_prompt_evidence_hash": "What is the digital evidence hash? ",
        "issuer_prompt_jurisdiction": "Enter the court jurisdiction: ",
        "issuer_prompt_judge_id": "What is your authority/judge identifier (ID)? ",
        "access_levels_description": """ Access Levels:
\t0 (Restricted Read-Only): Only selected metadata can be viewed.
\t1 (Read-Only): All chain of custody data and records can be viewed.
\t2 (Read and Write): Access to view and append evidence records.
\t99 (ADMIN): Full administrative access (reserved for exceptional overrides,
            such as transferring custody from an expert no longer eligible).
""",
        "issuer_prompt_auth_level": "What access level will the expert have for this evidence (enter number only)? ",
        "offer_sent_holder_response": "Credential offer sent. Holder agent responded with: {response}",

        # Webhook Handler
        "webhook_received": "📩 Webhook received:",
        "connection_accepted": "Connection accepted with {name}, DID: {did}",
        "verifier_accepted_data": "Verifier accepted the data successfully.",
        "error_calling_verifier": "Error calling verifier API: {status} {text}",
    }
}


def _find_config_file() -> Path | None:
    """Finds config.json in current directory or parent directories."""
    candidates = [
        Path.cwd() / "config.json",
        Path(__file__).resolve().parent / "config.json",
        Path(__file__).resolve().parent.parent / "config.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def get_language() -> str:
    """Gets the active language from config.json or environment variable."""
    global _CURRENT_LANGUAGE
    if _CURRENT_LANGUAGE:
        return _CURRENT_LANGUAGE

    # Environment variable has priority if set
    env_lang = os.environ.get("APP_LANG", "").lower().strip()
    if env_lang in MESSAGES:
        _CURRENT_LANGUAGE = env_lang
        return _CURRENT_LANGUAGE

    # Otherwise read from config.json
    config_file = _find_config_file()
    if config_file:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language", "").lower().strip()
                if lang in MESSAGES:
                    _CURRENT_LANGUAGE = lang
                    return _CURRENT_LANGUAGE
        except Exception:
            pass

    _CURRENT_LANGUAGE = DEFAULT_LANGUAGE
    return _CURRENT_LANGUAGE


def set_language(lang: str) -> None:
    """Sets the active language programmatically ('en' or 'pt')."""
    global _CURRENT_LANGUAGE
    if lang.lower().strip() in MESSAGES:
        _CURRENT_LANGUAGE = lang.lower().strip()


def t(key: str, **kwargs) -> str:
    """Translates a key into the configured language, interpolating kwargs."""
    lang = get_language()
    lang_dict = MESSAGES.get(lang, MESSAGES[DEFAULT_LANGUAGE])
    msg = lang_dict.get(key)
    
    # Fallback to default language if key missing in chosen language
    if msg is None:
        msg = MESSAGES[DEFAULT_LANGUAGE].get(key, key)
        
    if kwargs:
        try:
            return msg.format(**kwargs)
        except Exception:
            return msg
    return msg
