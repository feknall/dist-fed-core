import asyncio
import logging

from .demo_agent import DemoAgent, CRED_FORMAT_INDY
from .utils import log_msg

LOGGER = logging.getLogger(__name__)


class EndorserAgent(DemoAgent):
    def __init__(self, http_port: int, admin_port: int, **kwargs):
        super().__init__(
            "Endorser.Agent." + str(admin_port),
            http_port,
            admin_port,
            prefix="Endorser",
            extra_args=[
                "--auto-accept-invites",
                "--auto-accept-requests",
            ],
            endorser_role="endorser",
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

    async def handle_connections(self, message):
        # inviter:
        conn_id = message["connection_id"]
        if message["state"] == "invitation":
            self.connection_id = conn_id

        # author responds to a multi-use invitation
        if message["state"] == "request":
            self.endorser_connection_id = message["connection_id"]
            if not self._connection_ready:
                self._connection_ready = asyncio.Future()

        # finish off the connection
        if message["connection_id"] == self.endorser_connection_id:
            if message["state"] == "active" and not self._connection_ready.done():
                self.log("Endorser Connected")
                self._connection_ready.set_result(True)

                # setup endorser meta-data on our connection
                log_msg("Setup endorser agent meta-data ...")
                await self.admin_POST(
                    "/transactions/"
                    + self.endorser_connection_id
                    + "/set-endorser-role",
                    params={"transaction_my_job": "TRANSACTION_ENDORSER"},
                )

    async def handle_basicmessages(self, message):
        self.log("Received message:", message["content"])


async def start_endorser_agent(
        start_port,
        genesis: str = None,
        genesis_txn_list: str = None,
        use_did_exchange: bool = True,
):
    # start mediator agent
    endorser_agent = EndorserAgent(
        start_port,
        start_port + 1,
        genesis_data=genesis,
        genesis_txn_list=genesis_txn_list,
    )
    await endorser_agent.register_did(cred_type=CRED_FORMAT_INDY)
    await endorser_agent.listen_webhooks(start_port + 2)
    await endorser_agent.start_process()

    log_msg("Endorser Admin URL is at:", endorser_agent.admin_url)
    log_msg("Endorser Endpoint URL is at:", endorser_agent.endpoint)
    log_msg("Endorser webhooks listening on:", start_port + 2)

    # get a reusable invitation to connect to this endorser
    log_msg("Generate endorser multi-use invite ...")
    endorser_agent.endorser_connection_id = None
    endorser_agent.endorser_public_did = None
    endorser_agent.use_did_exchange = use_did_exchange
    if use_did_exchange:
        endorser_connection = await endorser_agent.admin_POST(
            "/out-of-band/create-invitation",
            {"handshake_protocols": ["rfc23"]},
            params={
                "alias": "EndorserMultiuse",
                "auto_accept": "true",
                "multi_use": "true",
            },
        )
    else:
        # old-style connection
        endorser_connection = await endorser_agent.admin_POST(
            "/connections/create-invitation?alias=EndorserMultiuse&auto_accept=true&multi_use=true"
        )
    endorser_agent.endorser_multi_connection = endorser_connection
    endorser_agent.endorser_multi_invitation = endorser_connection["invitation"]
    endorser_agent.endorser_multi_invitation_url = endorser_connection["invitation_url"]

    endorser_agent_public_did = await endorser_agent.admin_GET("/wallet/did/public")
    endorser_did = endorser_agent_public_did["result"]["did"]
    endorser_agent.endorser_public_did = endorser_did

    return endorser_agent
