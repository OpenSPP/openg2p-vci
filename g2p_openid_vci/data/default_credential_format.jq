{
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        (.web_base_url + "/api/v1/vci/.well-known/contexts.json")
    ],
    "id": .vc_id,
    "type": ["VerifiableCredential", .issuer.credential_type],
    "issuer": .issuer.unique_issuer_id,
    "issuanceDate": .curr_datetime,
    "credentialSubject": {
        "vcVer": "VC-V1",
        "id": (.web_base_url  + "/api/v1/registry/individual/" + (.partner.id | tostring)),
        "name": [
            {
                "language": "eng",
                "value": (.partner.name // null)
            }
        ],
        "fullName": [
            {
                "language": "eng",
                "value": (.partner.name // null)
            }
        ],
        "gender": [
            {
                "language": "eng",
                "value": (.partner.gender // null)
            }
        ],
        "dateOfBirth": (.partner.birthdate // null),
        "email": (.partner.email // null),
        "phone": (.partner.phone // null),
        "addressLine1": [
            {
                "language": "eng",
                "value": .partner_address.street_address
            }
        ],
        "province": [
            {
                "language": "eng",
                "value": .partner_address.locality
            }
        ],
        "region": [
            {
                "language": "eng",
                "value": .partner_address.region
            }
        ],
        "postalCode": .partner_address.postal_code,
        "face": .partner_face,
        "UIN": .reg_ids["NATIONAL ID"]?.value
    }
}
