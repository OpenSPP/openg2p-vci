import logging

from werkzeug.exceptions import Unauthorized

from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..models.openid_vci import (
    CredentialBaseResponse,
    CredentialErrorResponse,
    CredentialIssuerResponse,
    CredentialRequest,
    CredentialResponse,
    VCIBaseModel,
)

_logger = logging.getLogger(__name__)


class OpenIdVCIRestService(Component):
    _name = "openid_vci_base.rest.service"
    _inherit = ["base.rest.service"]
    _usage = "vci"
    _collection = "base.rest.openid.vci.services"
    _description = """
        OpenID for VCI API Services
    """

    @restapi.method(
        [
            (
                [
                    "/credential",
                ],
                "POST",
            )
        ],
        input_param=PydanticModel(CredentialRequest),
        output_param=PydanticModel(CredentialBaseResponse),
    )
    def post_credential(self, credential_request: CredentialRequest):
        token = request.httprequest.headers.get("Authorization", "").replace("Bearer", "", 1)
        if not token:
            raise Unauthorized("Invalid Bearer Token received.")
        try:
            # TODO: Split into smaller steps to better handle errors
            return CredentialResponse(
                **self.env["g2p.openid.vci.issuers"].issue_vc(credential_request.dict(), token.strip())
            )
        except Exception as e:
            _logger.exception("Error while handling credential request")
            # TODO: Remove this hardcoding
            return CredentialErrorResponse(
                error="invalid_credential_request",
                error_description=f"Error issuing credential. {e}",
                c_nonce="",
                c_nonce_expires_in=1,
            )

    @restapi.method(
        [
            (
                [
                    "/.well-known/openid-credential-issuer",
                ],
                "GET",
            )
        ],
        output_param=PydanticModel(CredentialIssuerResponse),
    )
    def get_openid_credential_issuers_all(self):
        return self.get_openid_credential_issuer()

    @restapi.method(
        [
            (
                [
                    "/.well-known/openid-credential-issuer/<string:issuer_name>",
                ],
                "GET",
            )
        ],
        output_param=PydanticModel(CredentialIssuerResponse),
    )
    def get_openid_credential_issuer(self, issuer_name=""):
        return CredentialIssuerResponse(
            **self.env["g2p.openid.vci.issuers"].get_issuer_metadata_by_name(issuer_name=issuer_name)
        )

    @restapi.method(
        [
            (
                [
                    "/.well-known/contexts.json",
                ],
                "GET",
            )
        ],
        output_param=PydanticModel(VCIBaseModel),
    )
    def get_openid_contexts_json(self):
        return VCIBaseModel(**self.env["g2p.openid.vci.issuers"].get_all_contexts_json())
