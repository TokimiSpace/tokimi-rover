# Security policy

Tokimi Rover V0.1 is a prototype, not a hardened or safety-certified product.
Its local access points and HTTP services do not currently provide
application-level authentication or TLS. The camera restart endpoint and rover
control surface must therefore be treated as trusted-local-network features.

Please report security issues privately to `ben@tokimi.space`. Include the
affected firmware, commit or archive identity, reproduction steps, impact, and
whether physical access or AP association is required. Avoid publishing working
control, restart, or denial-of-service exploits before a fix is available.

Never include real Wi-Fi credentials, private media, or personal network data
in an issue or pull request.
