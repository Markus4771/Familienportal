function b64urlToBytes(value) {
  const padding = '='.repeat((4 - value.length % 4) % 4);
  const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}

function bytesToB64url(value) {
  const bytes = new Uint8Array(value);
  let binary = '';
  bytes.forEach(b => binary += String.fromCharCode(b));
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function registrationOptions(options) {
  options.challenge = b64urlToBytes(options.challenge);
  options.user.id = b64urlToBytes(options.user.id);
  if (options.excludeCredentials) options.excludeCredentials = options.excludeCredentials.map(item => ({...item, id: b64urlToBytes(item.id)}));
  return options;
}

function authenticationOptions(options) {
  options.challenge = b64urlToBytes(options.challenge);
  if (options.allowCredentials) options.allowCredentials = options.allowCredentials.map(item => ({...item, id: b64urlToBytes(item.id)}));
  return options;
}

function credentialToJSON(credential) {
  const response = credential.response;
  const result = {
    id: credential.id,
    rawId: bytesToB64url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment,
    clientExtensionResults: credential.getClientExtensionResults(),
    response: { clientDataJSON: bytesToB64url(response.clientDataJSON) }
  };
  if (response.attestationObject) result.response.attestationObject = bytesToB64url(response.attestationObject);
  if (response.authenticatorData) result.response.authenticatorData = bytesToB64url(response.authenticatorData);
  if (response.signature) result.response.signature = bytesToB64url(response.signature);
  if (response.userHandle) result.response.userHandle = bytesToB64url(response.userHandle);
  if (response.getTransports) result.response.transports = response.getTransports();
  return result;
}
