from identity.base.agent_container import AriesAgent


class IssuerAgent(AriesAgent):
    def __init__(
            self,
            ident: str,
            http_port: int,
            admin_port: int,
            no_auto: bool = False,
            endorser_role: str = None,
            revocation: bool = False,
            **kwargs,
    ):
        super().__init__(
            ident,
            http_port,
            admin_port,
            prefix="Issuer",
            no_auto=no_auto,
            endorser_role=endorser_role,
            revocation=revocation,
            **kwargs,
        )
        self.connection_id = None
        self._connection_ready = None
        self.cred_state = {}
        # TODO define a dict to hold credential attributes
        # based on cred_def_id
        self.cred_attrs = {}

    async def detect_connection(self):
        await self._connection_ready
        self._connection_ready = None

    @property
    def connection_ready(self):
        return self._connection_ready.done() and self._connection_ready.result()
