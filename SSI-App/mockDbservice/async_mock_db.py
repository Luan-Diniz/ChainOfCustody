import asyncio

class AsyncMockDB:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._identities = {}
        self._trusted_issuers: list[str] = []  # Tree would have better perfomance
        self._credential_definition_guid = ("","") # tuple(credential_guid, connectionId) 
        self._verified_data = {}

    # No reason to create another connectionId in this PoC, even though in real life that is necessary
    async def update_credential_definition_guid(self, credential_definition_guid:str, connectionId:str) ->  None:
        async with self._lock:
            self._credential_definition_guid = (credential_definition_guid, connectionId)
    async def get_credential_definition_guid(self) ->  tuple[str,str]:
        async with self._lock:
            return self._credential_definition_guid

    async def add_identity(self, name: str, currentdid: str) -> None:
        """
            If non existent, adds a record {$name": {"current_did": str,
                                                     "older_dids: [], 
                                                    }
                                            }.

            Otherwise, just updates "current_did" and "older_dids".
        """
        async with self._lock:
            if name in self._identities:
                identity = self._identities[name]
                identity["older_dids"].append(identity["current_did"])
                identity["current_did"] = currentdid
            else:
                self._identities[name] = {"current_did": currentdid,
                                        "older_dids": []}


    async def get_identity(self, name: str) -> dict | None:
        async with self._lock:
            try:
                return self._identities[name]
            except KeyError:
                return None

    async def list_identities(self) -> list[dict[str, str|None]]:
        """
        Returns a list where each item is a dict containing the fields name,
        current_did and older_dids.
        """
        async with self._lock:
            return [{"name": name, **identity_data} 
                    for name, identity_data in self._identities.items()]

    async def get_trusted_issuers(self) -> list[str]:
        async with self._lock:
            return self._trusted_issuers

    async def add_trusted_issuer(self, issuer: str):
        async with self._lock:
            if issuer not in self._trusted_issuers:
                self._trusted_issuers.append(issuer)

    async def add_verified_data(self, identifier, verified_data):
        async with self._lock:
           self._verified_data[identifier] = verified_data
    async def get_verified_data(self, identifier):
        async with self._lock:
            if identifier not in self._verified_data:
                return None
            return self._verified_data[identifier]

    


    """
    Useful functions, but not are used in this PoC:

    async def delete_identity(self, name: str) -> bool:
    async def set_trusted_issuers(self, issuers: List[str]):
    async def remove_trusted_issuer(self, issuer: str):
    """