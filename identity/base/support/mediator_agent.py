import asyncio

from identity.base.support.demo_agent import DemoAgent
from identity.base.support.utils import log_msg


class MediatorAgent(DemoAgent):
    def __init__(self, http_port: int, admin_port: int, **kwargs):
        super().__init__(
            "Mediator.Agent." + str(admin_port),
            http_port,
            admin_port,
            prefix="Mediator",
            mediation=True,
            extra_args=[
                "--auto-accept-invites",
                "--auto-accept-requests",
            ],
            seed=None,
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
        if message["connection_id"] == self.mediator_connection_id:
            if message["state"] == "active" and not self._connection_ready.done():
                self.log("Mediator Connected")
                self._connection_ready.set_result(True)

    async def handle_basicmessages(self, message):
        self.log("Received message:", message["content"])


async def start_mediator_agent(
    start_port, genesis: str = None, genesis_txn_list: str = None
):
    # start mediator agent
    mediator_agent = MediatorAgent(
        start_port,
        start_port + 1,
        genesis_data=genesis,
        genesis_txn_list=genesis_txn_list,
    )
    await mediator_agent.listen_webhooks(start_port + 2)
    await mediator_agent.start_process()

    log_msg("Mediator Admin URL is at:", mediator_agent.admin_url)
    log_msg("Mediator Endpoint URL is at:", mediator_agent.endpoint)
    log_msg("Mediator webhooks listening on:", start_port + 2)

    return mediator_agent


async def connect_wallet_to_mediator(agent, mediator_agent):
    # Generate an invitation
    log_msg("Generate mediation invite ...")
    mediator_agent._connection_ready = asyncio.Future()
    mediator_connection = await mediator_agent.admin_POST(
        "/connections/create-invitation"
    )
    mediator_agent.mediator_connection_id = mediator_connection["connection_id"]

    # accept the invitation
    log_msg("Accept mediation invite ...")
    connection = await agent.admin_POST(
        "/connections/receive-invitation", mediator_connection["invitation"]
    )
    agent.mediator_connection_id = connection["connection_id"]

    log_msg("Await mediation connection status ...")
    await mediator_agent.detect_connection()
    log_msg("Connected agent to mediator:", agent.ident, mediator_agent.ident)

    # setup mediation on our connection
    log_msg("Request mediation ...")
    mediation_request = await agent.admin_POST(
        "/mediation/request/" + agent.mediator_connection_id, {}
    )
    agent.mediator_request_id = mediation_request["mediation_id"]
    log_msg("Mediation request id:", agent.mediator_request_id)

    count = 3
    while 0 < count:
        await asyncio.sleep(1.0)
        mediation_status = await agent.admin_GET(
            "/mediation/requests/" + agent.mediator_request_id
        )
        if mediation_status["state"] == "granted":
            log_msg("Mediation setup successfully!", mediation_status)
            return mediator_agent
        count = count - 1

    log_msg("Mediation connection FAILED :-(")
    raise Exception("Mediation connection FAILED :-(")

