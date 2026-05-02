# Security Report

## Group Members

- Rashid Alkatheri - 230208843
- Ibrahim Karaja - 230208879
- Abdullah Al Tamsha - 230208916

## 1. Why Salting Is Necessary Against Rainbow Table Attacks

Password hashing is necessary because storing plaintext passwords creates immediate risk if the database is leaked. However, hashing alone is not enough when many users may choose common passwords.

A rainbow table is a precomputed lookup table of password hashes. Attackers build these tables by hashing many common passwords in advance. If a database stores unsalted hashes, the attacker can compare the stolen hashes against the rainbow table and quickly recover weak or reused passwords.

Salting prevents this shortcut. A salt is a random value added to each password before hashing. Because each user gets a different salt, the same password produces a different hash for each account. This means an attacker cannot use one precomputed rainbow table against every user in the database.

For example, without salts:

```text
password123 -> same hash for every user
```

With unique salts:

```text
password123 + saltA -> hashA
password123 + saltB -> hashB
```

bcrypt automatically generates and stores a salt as part of the final hash string. It is also intentionally slow, which makes large-scale brute force attacks more expensive.

## 2. Risks of Storing Sensitive Data Inside a JWT Payload

JWT payloads are not encrypted by default. A standard JWT is only Base64URL encoded and signed. The signature proves that the token was issued by the server and has not been modified, but anyone who has the token can decode the payload and read its contents.

Because of this, sensitive data should not be stored inside a JWT payload. Examples of data that should not be placed in a JWT include:

- Plaintext passwords
- Password hashes
- Credit card numbers
- National ID numbers
- Secret API keys
- Private recovery tokens
- Highly sensitive personal information

If sensitive data is placed in a JWT, it can leak through:

- Browser storage
- Server logs
- Reverse proxy logs
- Debug tools
- Network inspection on compromised devices
- Accidental sharing of tokens

JWTs should contain only the minimum information needed for authentication and authorization. For this project, the token should include the username, role, expiry time, issued-at time, and token ID. This follows the principle of least privilege by limiting the token to only the claims required by the backend.

Recommended JWT payload:

```json
{
  "sub": "alice",
  "role": "user",
  "exp": 1710000000,
  "iat": 1709996400,
  "jti": "unique-token-id"
}
```

The token should also have a short expiration time. Logout should blacklist the token ID so the token can be rejected before natural expiry.

## Least Privilege Summary

The system should grant each user only the permissions required for their role:

- Standard users can access only their profile.
- Admin users can access profile data and delete users.
- Admin-only routes must verify the role claim and must not rely on hidden frontend controls.
- Unauthorized admin-route attempts should return `403 Forbidden` and be logged to `security.log`.

This prevents a standard user from guessing admin URLs or forcing access to privileged backend actions.
