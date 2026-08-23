---
name: social-and-guest-auth
description: Standards for mobile social authentication (Google OIDC RSA, Facebook Graph API), hardware-bound guest sessions, seamless in-place account upgrading, and automated 90-day stale guest cleanup workers.
---

# Mobile Social & Guest Authentication Skill

## Overview
This skill documents authentication flows, cryptographic token verification, and subscriber session management for mobile OTT streaming applications.

---

## 1. Hardware-Bound Guest Sessions
- Allows anonymous users to launch the mobile app and browse immediately without signup.
- Generates a subscriber with `role="guest"` bound to `device_id`.
- Protected by 90-day automated cleanup worker to purge abandoned accounts.

---

## 2. In-Place Social Account Upgrades
When a guest subscriber signs in with Google (`id_token`) or Facebook (`access_token`):
- The existing guest row is updated in-place to `role="subscriber"`, attaching `email`, `first_name`, and social IDs.
- Preserves all historical watch progress, continue watching timestamps, likes, and saves without losing data.

---

## 3. Cryptographic Token Verification
- **Google OIDC**: Validates RSA cryptographic signatures against Google's public JSON Web Key Set (`https://www.googleapis.com/oauth2/v3/certs`) checking `aud == GOOGLE_CLIENT_ID` and `iss in ("accounts.google.com", "https://accounts.google.com")`.
- **Facebook Graph API**: Validates access tokens via Facebook Graph debug endpoint (`/debug_token`) verifying `app_id == FACEBOOK_APP_ID` and `is_valid == true`.
