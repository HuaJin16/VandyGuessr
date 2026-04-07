# OAuth Setup (Microsoft + Google)

This guide describes how to configure:

- Microsoft OAuth for Vanderbilt students
- Google OAuth for any Google account

Vanderbilt SSO admin access is not required; the backend enforces policy after login.

## Overview

- **App type**: Single-page application (SPA)
- **Tenant**: Multi-tenant (`common`)
- **Flow**: OAuth redirect flow
- **Access**: Validate Vanderbilt domain on Microsoft path; require valid verified Google identity on Google path
- **Profile data**: Name, email, profile photo (via Microsoft Graph)

## 1) Create an Azure AD App Registration

1. Go to the Azure portal: https://portal.azure.com
2. Open **Microsoft Entra ID** (Azure Active Directory).
3. Select **App registrations** > **New registration**.
4. Configure:
   - **Name**: `VandyGuessr`
   - **Supported account types**: **Accounts in any organizational directory**
     (multi-tenant)
   - **Redirect URI**:
     - Type: **Single-page application (SPA)**
     - URI (local dev): `http://localhost:5173/`
5. Click **Register**.

## 2) Capture App Identifiers

From the app's **Overview** page:

- **Application (client) ID** -> `VITE_MICROSOFT_CLIENT_ID` and
  `MICROSOFT_CLIENT_ID`
- **Directory (tenant) ID** -> not required for multi-tenant; use `common`

## 3) Configure Authentication

1. Open **Authentication** in the app registration.
2. Under **Platform configurations**, ensure you have a **Single-page
   application** entry.
3. Add redirect URIs for your environments:
   - Local dev: `http://localhost:5173/`
   - Production: `https://<your-frontend-domain>/`
4. Enable:
   - **Access tokens** (for MS Graph)
   - **ID tokens** (for sign-in)
5. Save changes.

## 4) Configure API Permissions

1. Open **API permissions**.
2. Click **Add a permission** > **Microsoft Graph** > **Delegated permissions**.
3. Add:
   - `openid`
   - `profile`
   - `email`
   - `User.Read`
4. Click **Add permissions**.

Note: These permissions do not require admin consent for basic profile access.

## 5) (Optional) Add Additional Redirect URIs

If you deploy to multiple environments, add all frontend URLs here. Microsoft
only allows redirects to registered URIs.

## 6) Vanderbilt Restriction Feature Flag

Because this is a multi-tenant app, **any Microsoft account** can authenticate with Microsoft. Whether those accounts are allowed into VandyGuessr is controlled by a feature flag.

Default behavior:

- `FEATURE_VANDERBILT_RESTRICTED_LOGINS=true`
- `VITE_FEATURE_VANDERBILT_RESTRICTED_LOGINS=true`
- The frontend only shows the Microsoft button.
- The backend enforces Vanderbilt-only access on the Microsoft path.

When both flags are set to `false`:

- The frontend also shows Google sign-in.
- The backend still validates Google tokens and requires `email_verified = true`.
- The Microsoft path remains available, but Vanderbilt-only enforcement is relaxed.

The Microsoft-path Vanderbilt check is:

```python
def is_vanderbilt_email(email: str) -> bool:
    return email.lower().endswith("@vanderbilt.edu")
```

If the email does not match while the restriction flag is enabled, reject the login and do not create a user.

## 7) Environment Variables

Add these variables to your environment:

### Backend

```bash
MICROSOFT_CLIENT_ID=your-azure-client-id
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FEATURE_VANDERBILT_RESTRICTED_LOGINS=true
```

### Frontend

```bash
VITE_MICROSOFT_CLIENT_ID=your-azure-client-id
VITE_MICROSOFT_REDIRECT_URI=http://localhost:5173/
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_FEATURE_VANDERBILT_RESTRICTED_LOGINS=true
```

Note: The tenant ID (`common`) is hardcoded in the application because the app always uses multi-tenant Microsoft authentication.

`GOOGLE_CLIENT_SECRET` is backend-only and must never be exposed to the frontend.

When Vanderbilt restriction is enabled, the frontend still accepts `VITE_GOOGLE_CLIENT_ID`, but the Google button stays hidden.

## 8) Google OAuth Setup

Use Google Identity Services (GIS) for the frontend and backend JWT verification.

1. Open Google Cloud Console -> APIs & Services -> Credentials.
2. Create an OAuth Client ID for a **Web application**.
3. Add authorized JavaScript origins:
   - `http://localhost:5173`
   - Your production frontend origin
4. Add authorized redirect URIs if required by your deployment flow.
5. Copy:
   - Client ID -> `VITE_GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_ID`
   - Client Secret -> `GOOGLE_CLIENT_SECRET` (backend only)
### Google Policy Enforced by Backend

- Token must be a valid Google ID token.
- `email_verified` must be true.
- Google sign-in should only be exposed in the frontend when `VITE_FEATURE_VANDERBILT_RESTRICTED_LOGINS=false`.

## 9) Fetching Profile Data and Photos

After login, use Microsoft Graph to fetch profile data and the avatar:

- **Profile**: `GET https://graph.microsoft.com/v1.0/me`
- **Photo**: `GET https://graph.microsoft.com/v1.0/me/photo/$value`

These endpoints are free for basic usage and are well within rate limits for
VandyGuessr. Recommended practice is to store the returned data in MongoDB and
avoid re-fetching on every request.

## 10) Rate Limits (Practical Notes)

Microsoft Graph rate limits for user profile and photo endpoints are generous
(typically ~10,000 requests per 10 minutes per app). VandyGuessr will be far
below these limits when fetching profile data only on login.

## 11) Troubleshooting

- **AADSTS50011**: Redirect URI mismatch
  - Ensure the exact redirect URI is registered in Azure.
- **Missing email**: Use `preferred_username` if `email` is absent.
- **Forbidden photo**: If photo access fails, fall back to initials/default.
