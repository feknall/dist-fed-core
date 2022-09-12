from identity.base.agent_container import AriesAgent


class ClientAgent(AriesAgent):
    def __init__(
            self,
            ident: str,
            http_port: int,
            admin_port: int,
            no_auto: bool = False,
            aip: int = 20,
            endorser_role: str = None,
            **kwargs,
    ):
        super().__init__(
            ident,
            http_port,
            admin_port,
            prefix="Client",
            no_auto=no_auto,
            seed=None,
            aip=aip,
            endorser_role=endorser_role,
            **kwargs,
        )
        self.connection_id = None
        self._connection_ready = None
        self.cred_state = {}

    async def detect_connection(self):
        await self._connection_ready
        self._connection_ready = None

    @property
    def connection_ready(self):
        return self._connection_ready.done() and self._connection_ready.result()
