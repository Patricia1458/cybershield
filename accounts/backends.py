from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    """Authenticates against User.email in addition to the default username lookup.

    Only User.email (plaintext) can be queried this way — Profile.encrypted_email
    is Fernet-encrypted, and Fernet ciphertext is randomized per encryption, so an
    exact-match DB lookup against it can never find a row even with the right
    plaintext. User.email remains the authoritative, queryable copy.

    Returns None (rather than raising) when the typed value isn't a known email,
    so Django falls through to the next backend in AUTHENTICATION_BACKENDS —
    normally ModelBackend, which matches on username. That fallback is what keeps
    username-only logins (e.g. seeded demo accounts) working unchanged.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(email__iexact=username)
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # Ambiguous — can't safely pick one. Let the username-based backend
            # in the chain have a go instead.
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
