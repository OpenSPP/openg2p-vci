import json
import logging
from typing import Annotated

import pyjq as jq
from fastapi import APIRouter, Depends, Header
from werkzeug.exceptions import Unauthorized

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env
from odoo.addons.g2p_openid_vci.json_encoder import VCJSONEncoder

from ..schemas.openid_vci import (
    CredentialBaseResponse,
    CredentialErrorResponse,
    CredentialIssuerResponse,
    CredentialRequest,
    CredentialResponse,
    VCIBaseModel,
)

_logger = logging.getLogger(__name__)

openid_vci_router = APIRouter(tags=["openid vci"])


@openid_vci_router.post("/credential", responses={200: {"model": CredentialBaseResponse}})
def post_credential(
    credential_request: CredentialRequest,
    authorization: Annotated[str, Header()],
    env: Annotated[Environment, Depends(odoo_env)],
):
    token = authorization.removeprefix("Bearer")
    if not token:
        raise Unauthorized("Invalid Bearer Token received.")
    try:
        # TODO: Split into smaller steps to better handle errors
        return CredentialResponse(
            **env["g2p.openid.vci.issuers"].issue_vc(credential_request.model_dump(), token.strip())
        )
    except Exception as e:
        _logger.exception("Error while handling credential request")
        # TODO: Remove this hardcoding
        return CredentialErrorResponse(
            error="invalid_scope",
            error_description=f"Invalid Scope. {e}",
            c_nonce="",
            c_nonce_expires_in=1,
        )


@openid_vci_router.get(
    "/.well-known/openid-credential-issuer/{issuer_name}",
    responses={200: {"model": CredentialIssuerResponse}},
)
def get_openid_credential_issuer(
    issuer_name: str | None,
    env: Annotated[Environment, Depends(odoo_env)],
):
    search_domain = []
    if issuer_name:
        search_domain.append(("name", "=", issuer_name))
    vci_issuers = env["g2p.openid.vci.issuers"].sudo().search(search_domain).read()
    web_base_url = env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
    cred_configs = None
    for issuer in vci_issuers:
        issuer["web_base_url"] = web_base_url
        issuer = VCJSONEncoder.python_dict_to_json_dict(issuer)
        issuer_metadata = jq.first(issuer["issuer_metadata_text"], issuer)
        if isinstance(issuer_metadata, list):
            if not cred_configs:
                cred_configs = []
            cred_configs.extend(issuer_metadata)
        elif isinstance(issuer_metadata, dict):
            if not cred_configs:
                cred_configs = {}
            cred_configs.update(issuer_metadata)
    response = {
        "credential_issuer": web_base_url,
        "credential_endpoint": f"{web_base_url}/api/v1/vci/credential",
    }
    if isinstance(cred_configs, list):
        response["credentials_supported"] = cred_configs
    elif isinstance(cred_configs, dict):
        response["credential_configurations_supported"] = cred_configs
    return CredentialIssuerResponse(**response)


@openid_vci_router.get(
    "/.well-known/openid-credential-issuer", responses={200: {"model": CredentialIssuerResponse}}
)
def get_openid_credential_issuers_all(
    env: Annotated[Environment, Depends(odoo_env)],
):
    return get_openid_credential_issuer(issuer_name=None, env=env)


@openid_vci_router.get("/.well-known/contexts.json", responses={200: {"model": VCIBaseModel}})
def get_openid_contexts_json(
    env: Annotated[Environment, Depends(odoo_env)],
):
    web_base_url = env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
    context_jsons = env["g2p.openid.vci.issuers"].sudo().search([]).read(["contexts_json"])
    final_context = {"@context": {}}
    for context in context_jsons:
        context = context["contexts_json"].strip()
        if context:
            final_context["@context"].update(
                json.loads(context.replace("web_base_url", web_base_url))["@context"]
            )
    return VCIBaseModel(**final_context)
