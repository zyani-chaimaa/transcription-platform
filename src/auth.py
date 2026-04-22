import os
import streamlit as st
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

_provider_cfg_cache: dict | None = None


def _get_provider_cfg() -> dict:
    global _provider_cfg_cache
    if _provider_cfg_cache is None:
        _provider_cfg_cache = requests.get(GOOGLE_DISCOVERY_URL, timeout=10).json()
    return _provider_cfg_cache


def authenticate() -> dict | None:
    """
    Returns user dict {email, name, picture} if authenticated, else shows
    the login page and returns None.

    Auth strategy:
      1. Cloud IAP header (production) — handled at infrastructure level.
      2. Streamlit session state — user already completed OAuth this session.
      3. OAuth callback — ?code= param present in URL.
      4. Show login page.
    """
    user = _check_iap()
    if user:
        return user

    if "authenticated_user" in st.session_state:
        return st.session_state["authenticated_user"]

    params = st.query_params
    if "code" in params:
        user = _exchange_code(params["code"])
        if user:
            st.session_state["authenticated_user"] = user
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Authentication failed. Please try signing in again.")
            _render_login_page()
        return None

    _render_login_page()
    return None


def logout() -> None:
    st.session_state.pop("authenticated_user", None)
    iap_logout = "/_gcp_iap/clear_login_cookie"
    st.markdown(
        f'<meta http-equiv="refresh" content="0; url={iap_logout}">',
        unsafe_allow_html=True,
    )
    st.rerun()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_iap() -> dict | None:
    """Read the Google Cloud IAP injected header if present."""
    try:
        headers = st.context.headers
        iap_email = headers.get("X-Goog-Authenticated-User-Email", "")
        if iap_email:
            email = iap_email.split(":")[-1] if ":" in iap_email else iap_email
            return {
                "email": email,
                "name": email.split("@")[0].replace(".", " ").title(),
                "picture": None,
                "auth_via": "iap",
            }
    except Exception:
        pass
    return None


def _exchange_code(code: str) -> dict | None:
    """Exchange OAuth authorization code for user profile."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8501")

    if not client_id or not client_secret:
        st.error("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET env vars are not set.")
        return None

    cfg = _get_provider_cfg()

    token_resp = requests.post(
        cfg["token_endpoint"],
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    if not token_resp.ok:
        return None

    access_token = token_resp.json().get("access_token")
    if not access_token:
        return None

    userinfo_resp = requests.get(
        cfg["userinfo_endpoint"],
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if not userinfo_resp.ok:
        return None

    info = userinfo_resp.json()
    return {
        "email": info.get("email", ""),
        "name": info.get("name", info.get("email", "")),
        "picture": info.get("picture"),
        "auth_via": "oauth",
    }


def _build_auth_url() -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8501")
    cfg = _get_provider_cfg()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "online",
    }
    return cfg["authorization_endpoint"] + "?" + urlencode(params)


def _render_login_page() -> None:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        st.error(
            "**Configuration error:** `GOOGLE_CLIENT_ID` is not set. "
            "Copy `.env.example` to `.env` and fill in your credentials."
        )
        st.stop()

    auth_url = _build_auth_url()

    st.markdown(
        """
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            gap: 1.5rem;
        }
        .login-title {
            font-size: 2.4rem;
            font-weight: 700;
            color: #111827;
            margin: 0;
        }
        .login-subtitle {
            font-size: 1.1rem;
            color: #6b7280;
            margin: 0;
        }
        .google-btn {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 1rem;
            font-weight: 500;
            color: #374151;
            text-decoration: none;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: box-shadow 0.2s;
            cursor: pointer;
        }
        .google-btn:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .divider { width: 320px; border: none; border-top: 1px solid #e5e7eb; }
        .legal { font-size: 0.8rem; color: #9ca3af; text-align: center; max-width: 360px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="login-container">
            <p class="login-title">🎙️ Transcription Platform</p>
            <p class="login-subtitle">Transcribe audio files and recordings — instantly, privately.</p>
            <hr class="divider"/>
            <a class="google-btn" href="{auth_url}" target="_self">
                <svg width="20" height="20" viewBox="0 0 48 48">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                </svg>
                Sign in with Google
            </a>
            <p class="legal">
                By signing in you agree to use this platform in accordance with your
                company's data and acceptable-use policies. No audio or transcription
                data is stored on our servers.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()
