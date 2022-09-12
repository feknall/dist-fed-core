import asyncio
import os
import random

from qrcode import QRCode
import json


from identity.base.support.demo_agent import DemoAgent
from identity.base.support.utils import log_timer, log_status, log_msg, log_json

TAILS_FILE_COUNT = int(os.getenv("TAILS_FILE_COUNT", 100))


class AriesAgent(DemoAgent):
    def __init__(
            self,
            ident: str,
            http_port: int,
            admin_port: int,
            prefix: str = "Aries",
            no_auto: bool = False,
            seed: str = None,
            aip: int = 20,
            endorser_role: str = None,
            revocation: bool = False,
            **kwargs,
    ):
        super().__init__(
            ident,
            http_port,
            admin_port,
            prefix=prefix,
            seed=seed,
            aip=aip,
            endorser_role=endorser_role,
            revocation=revocation,
            extra_args=(
                []
                if no_auto
                else [
                    "--auto-accept-invites",
                    "--auto-accept-requests",
                    "--auto-store-credential",
                ]
            ),
            **kwargs,
        )
        self.connection_id = None
        self._connection_ready = None
        self.cred_state = {}
        # define a dict to hold credential attributes
        self.last_credential_received = None
        self.last_proof_received = None

    async def detect_connection(self):
        await self._connection_ready
        self._connection_ready = None

    @property
    def connection_ready(self):
        return self._connection_ready.done() and self._connection_ready.result()

    async def handle_oob_invitation(self, message):
        print("handle_oob_invitation()")
        pass

    async def handle_out_of_band(self, message):
        print("handle_out_of_band()")
        pass

    async def handle_connection_reuse(self, message):
        # we are reusing an existing connection, set our status to the existing connection
        if not self._connection_ready.done():
            self.connection_id = message["connection_id"]
            self.log("Connected")
            self._connection_ready.set_result(True)

    async def handle_connection_reuse_accepted(self, message):
        # we are reusing an existing connection, set our status to the existing connection
        if not self._connection_ready.done():
            self.connection_id = message["connection_id"]
            self.log("Connected")
            self._connection_ready.set_result(True)

    async def handle_connections(self, message):
        print("handle_connections()")
        pass

    async def handle_issue_credential(self, message):
        print("handle_issue_credential()")
        pass

    async def handle_issue_credential_v2_0(self, message):
        print("handle_issue_credential_v2_0()")
        pass

    async def handle_issue_credential_v2_0_indy(self, message):
        print("handle_issue_credential_v2_0_indy()")
        pass

    async def handle_issue_credential_v2_0_ld_proof(self, message):
        print("handle_issue_credential_v2_0_ld_proof()")
        pass

    async def handle_issuer_cred_rev(self, message):
        print("handle_issuer_cred_rev()")
        pass

    async def handle_present_proof(self, message):
        print("handle_present_proof()")
        pass

    async def handle_present_proof_v2_0(self, message):
        print("handle_present_proof_v2_0()")
        pass

    async def handle_basicmessages(self, message):
        self.log("Received message:", message["content"])

    async def handle_endorse_transaction(self, message):
        self.log("Received transaction message:", message.get("state"))

    async def handle_revocation_notification(self, message):
        self.log("Received revocation notification message:", message)

    async def generate_invitation(
            self,
            use_did_exchange: bool,
            auto_accept: bool = True,
            display_qr: bool = False,
            reuse_connections: bool = False,
            wait: bool = False,
    ):
        self._connection_ready = asyncio.Future()
        with log_timer("Generate invitation duration:"):
            # Generate an invitation
            log_status(
                "#7 Create a connection to alice and print out the invite details"
            )
            invi_rec = await self.get_invite(
                use_did_exchange,
                auto_accept=auto_accept,
                reuse_connections=reuse_connections,
            )

        if display_qr:
            qr = QRCode(border=1)
            qr.add_data(invi_rec["invitation_url"])
            log_msg(
                "Use the following JSON to accept the invite from another demo agent."
                " Or use the QR code to connect from a mobile agent."
            )
            log_msg(
                json.dumps(invi_rec["invitation"]), label="Invitation Data:", color=None
            )
            qr.print_ascii(invert=True)

        # if wait:
        #     log_msg("Waiting for connection...")
        #     await self.detect_connection()

        return invi_rec

    async def input_invitation(self, invite_details: dict, wait: bool = False):
        self._connection_ready = asyncio.Future()
        with log_timer("Connect duration:"):
            connection = await self.receive_invite(invite_details)
            log_json(connection, label="Invitation response:")

        # if wait:
        #     log_msg("Waiting for connection...")
        #     await self.detect_connection()

    async def create_schema_and_cred_def(
            self, schema_name, schema_attrs, revocation, version=None
    ):
        with log_timer("Publish schema/cred def duration:"):
            log_status("#3/4 Create a new schema/cred def on the ledger")
            if not version:
                version = format(
                    "%d.%d.%d"
                    % (
                        random.randint(1, 101),
                        random.randint(1, 101),
                        random.randint(1, 101),
                    )
                )
            (_, cred_def_id,) = await self.register_schema_and_creddef(  # schema id
                schema_name,
                version,
                schema_attrs,
                support_revocation=revocation,
                revocation_registry_size=TAILS_FILE_COUNT if revocation else None,
            )
            return cred_def_id
