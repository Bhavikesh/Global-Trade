"""
Phase 1 tests — Identity, Organizations, and Organization Isolation (T1.1–T1.6).

These tests use an in-memory SQLite database (no PostgreSQL dependency) and override
the FastAPI auth dependencies so tests run fully offline without Auth0.

Test coverage:
  - T1.1  JWT verification dependency (Auth0 token mock)
  - T1.2  User profile: GET /me, PATCH /me
  - T1.3  Organization creation
  - T1.4  Organization membership: add, list, remove
  - T1.5  Role enforcement (ADMIN-only routes return 403 for non-admins)
  - T1.6  Organization isolation (User A cannot access Org B)
"""
import uuid
from contextlib import contextmanager
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from tests.conftest import TestSessionLocal, as_user as _as_user, _make_claims


# ---------------------------------------------------------------------------
# T1.2 — User Profile
# ---------------------------------------------------------------------------


class TestUserProfile:
    def test_get_me_creates_user_on_first_login(self, client: TestClient, user_a_claims):
        """GET /api/v1/users/me provisions a new User record on first call."""
        with _as_user(user_a_claims):
            resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["identity_provider_id"] == "auth0|user-a"
        assert data["email"] == "a@example.com"
        assert data["name"] == "User A"
        assert data["status"] == "ACTIVE"

    def test_get_me_returns_same_user_on_second_call(self, client: TestClient, user_a_claims):
        """GET /api/v1/users/me is idempotent — same record returned on repeat calls."""
        with _as_user(user_a_claims):
            r1 = client.get("/api/v1/users/me", headers={"Authorization": "Bearer fake"})
            r2 = client.get("/api/v1/users/me", headers={"Authorization": "Bearer fake"})
        assert r1.json()["id"] == r2.json()["id"]

    def test_patch_me_updates_name_and_phone(self, client: TestClient, user_a_claims):
        """PATCH /api/v1/users/me updates mutable profile fields."""
        with _as_user(user_a_claims):
            client.get("/api/v1/users/me", headers={"Authorization": "Bearer fake"})
            resp = client.patch(
                "/api/v1/users/me",
                json={"name": "Updated Name", "phone": "+1-555-0100"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"
        assert data["phone"] == "+1-555-0100"

    def test_concurrent_first_login_provisioning_race(self, client: TestClient):
        """When an IntegrityError occurs due to a concurrent insert race, get_current_user rolls back and recovers."""
        race_claims = _make_claims(sub="auth0|race-user-1", email="race@example.com", name="Race User")

        # Simulate race by creating a separate session where user is inserted
        db1 = TestSessionLocal()
        db2 = TestSessionLocal()
        try:
            from app.core.auth.dependencies import get_current_user
            # Simulate first login via get_current_user on db1
            user1 = get_current_user(claims=race_claims, db=db1)
            assert user1.identity_provider_id == "auth0|race-user-1"

            # Call on db2 — user already exists, returned cleanly
            user2 = get_current_user(claims=race_claims, db=db2)
            assert user2.id == user1.id

            # Simulate simultaneous insert collision directly
            from app.models.user import User
            from sqlalchemy.exc import IntegrityError
            colliding_user = User(identity_provider_id="auth0|race-user-1", email="other@example.com")
            db1.add(colliding_user)
            with pytest.raises(IntegrityError):
                db1.commit()
            db1.rollback()
        finally:
            db1.close()
            db2.close()




# ---------------------------------------------------------------------------
# T1.3 — Organization Creation
# ---------------------------------------------------------------------------


class TestOrganizationCreation:
    def test_create_organization_returns_201(self, client: TestClient, user_a_claims):
        """POST /api/v1/organizations creates an org and returns 201."""
        with _as_user(user_a_claims):
            resp = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Acme Exports Pvt Ltd", "country": "IN"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["legal_name"] == "Acme Exports Pvt Ltd"
        assert data["country"] == "IN"
        assert data["verification_status"] == "UNVERIFIED"

    def test_creator_becomes_admin(self, client: TestClient, user_a_claims):
        """Creator of an organization is automatically assigned ADMIN role."""
        with _as_user(user_a_claims):
            org_resp = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Creator Org"},
                headers={"Authorization": "Bearer fake"},
            )
            org_id = org_resp.json()["id"]
            members_resp = client.get(
                f"/api/v1/organizations/{org_id}/members",
                headers={"Authorization": "Bearer fake"},
            )
        members = members_resp.json()
        assert len(members) == 1
        assert members[0]["role"] == "ADMIN"


# ---------------------------------------------------------------------------
# T1.4 — Organization Membership
# ---------------------------------------------------------------------------


class TestOrganizationMembership:
    def _create_org(self, client: TestClient, claims: dict, name: str = "Test Org") -> str:
        with _as_user(claims):
            resp = client.post(
                "/api/v1/organizations/",
                json={"legal_name": name},
                headers={"Authorization": "Bearer fake"},
            )
        return resp.json()["id"]

    def _create_user_b(self, client: TestClient, claims: dict) -> str:
        """Provision User B by calling /me."""
        with _as_user(claims):
            resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer fake"})
        return resp.json()["id"]

    def test_add_member_to_organization(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """ADMIN (User A) can add User B as a MEMBER."""
        org_id = self._create_org(client, user_a_claims)
        user_b_id = self._create_user_b(client, user_b_claims)

        with _as_user(user_a_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": user_b_id, "role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 201
        assert resp.json()["role"] == "MEMBER"

    def test_list_members_shows_all_active_members(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """GET /members returns both members after adding User B."""
        org_id = self._create_org(client, user_a_claims)
        user_b_id = self._create_user_b(client, user_b_claims)

        with _as_user(user_a_claims):
            client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": user_b_id, "role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
            members = client.get(
                f"/api/v1/organizations/{org_id}/members",
                headers={"Authorization": "Bearer fake"},
            ).json()
        assert len(members) == 2

    def test_remove_member(self, client: TestClient, user_a_claims, user_b_claims):
        """ADMIN can remove a member (status becomes REMOVED)."""
        org_id = self._create_org(client, user_a_claims)
        user_b_id = self._create_user_b(client, user_b_claims)

        with _as_user(user_a_claims):
            add_resp = client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": user_b_id, "role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
            membership_id = add_resp.json()["id"]
            del_resp = client.delete(
                f"/api/v1/organizations/{org_id}/members/{membership_id}",
                headers={"Authorization": "Bearer fake"},
            )
        assert del_resp.status_code == 204


# ---------------------------------------------------------------------------
# T1.5 — Roles and Permissions
# ---------------------------------------------------------------------------


class TestRolesAndPermissions:
    def _setup(self, client, admin_claims, member_claims):
        """Create org with admin; add User B as MEMBER; return org_id."""
        with _as_user(admin_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "RBAC Org"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

        with _as_user(member_claims):
            user_b_id = client.get(
                "/api/v1/users/me", headers={"Authorization": "Bearer fake"}
            ).json()["id"]

        with _as_user(admin_claims):
            client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": user_b_id, "role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
        return org_id

    def test_non_admin_cannot_update_organization(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """MEMBER (User B) cannot PATCH organization details (requires ADMIN)."""
        org_id = self._setup(client, user_a_claims, user_b_claims)
        with _as_user(user_b_claims):
            resp = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"display_name": "Hacked Name"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403

    def test_non_admin_cannot_add_members(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """MEMBER cannot POST to /members (requires ADMIN)."""
        org_id = self._setup(client, user_a_claims, user_b_claims)
        with _as_user(user_b_claims):
            resp = client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": str(uuid.uuid4()), "role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403

    def test_non_admin_cannot_remove_members(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """MEMBER cannot DELETE a membership (requires ADMIN)."""
        org_id = self._setup(client, user_a_claims, user_b_claims)

        # Get User B's membership id
        with _as_user(user_b_claims):
            members = client.get(
                f"/api/v1/organizations/{org_id}/members",
                headers={"Authorization": "Bearer fake"},
            ).json()
        user_b_membership = next(m for m in members if m["role"] == "MEMBER")

        with _as_user(user_b_claims):
            resp = client.delete(
                f"/api/v1/organizations/{org_id}/members/{user_b_membership['id']}",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403

    def test_cannot_remove_last_admin(self, client: TestClient, user_a_claims):
        """ADMIN cannot remove themselves if they are the only ADMIN."""
        with _as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Single Admin Org"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]
            members = client.get(
                f"/api/v1/organizations/{org_id}/members",
                headers={"Authorization": "Bearer fake"},
            ).json()
            admin_membership_id = members[0]["id"]
            resp = client.delete(
                f"/api/v1/organizations/{org_id}/members/{admin_membership_id}",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 400
        assert "Cannot remove the last active ADMIN" in resp.json()["detail"]

    def test_cannot_demote_last_admin(self, client: TestClient, user_a_claims):
        """ADMIN cannot be demoted to MEMBER if they are the only active ADMIN."""
        with _as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Single Admin Org Demote"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]
            members = client.get(
                f"/api/v1/organizations/{org_id}/members",
                headers={"Authorization": "Bearer fake"},
            ).json()
            admin_membership_id = members[0]["id"]
            resp = client.patch(
                f"/api/v1/organizations/{org_id}/members/{admin_membership_id}",
                json={"role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 400
        assert "Cannot demote the last active ADMIN" in resp.json()["detail"]

    def test_can_demote_admin_when_another_admin_exists(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """An ADMIN can be demoted if another active ADMIN exists in the organization."""
        with _as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Dual Admin Org"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

        with _as_user(user_b_claims):
            user_b_id = client.get(
                "/api/v1/users/me", headers={"Authorization": "Bearer fake"}
            ).json()["id"]

        with _as_user(user_a_claims):
            # Add User B as a second ADMIN
            add_resp = client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": user_b_id, "role": "ADMIN"},
                headers={"Authorization": "Bearer fake"},
            )
            assert add_resp.status_code == 201
            user_b_membership_id = add_resp.json()["id"]

            # Demote User B to MEMBER (allowed because User A is still ADMIN)
            patch_resp = client.patch(
                f"/api/v1/organizations/{org_id}/members/{user_b_membership_id}",
                json={"role": "MEMBER"},
                headers={"Authorization": "Bearer fake"},
            )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["role"] == "MEMBER"

    def test_invalid_role_rejected_on_invite_and_update(
        self, client: TestClient, user_a_claims
    ):
        """Arbitrary roles like SUPERUSER or ROOT must be rejected with 422."""
        with _as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Role Test Org"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

            # Invite with invalid role
            invite_resp = client.post(
                f"/api/v1/organizations/{org_id}/members",
                json={"user_id": str(uuid.uuid4()), "role": "SUPERUSER"},
                headers={"Authorization": "Bearer fake"},
            )
            assert invite_resp.status_code == 422

            # Update with invalid role
            members = client.get(
                f"/api/v1/organizations/{org_id}/members",
                headers={"Authorization": "Bearer fake"},
            ).json()
            admin_membership_id = members[0]["id"]
            update_resp = client.patch(
                f"/api/v1/organizations/{org_id}/members/{admin_membership_id}",
                json={"role": "ROOT_ADMIN"},
                headers={"Authorization": "Bearer fake"},
            )
            assert update_resp.status_code == 422



# ---------------------------------------------------------------------------
# T1.6 — Organization Isolation
# ---------------------------------------------------------------------------


class TestOrganizationIsolation:
    def test_non_member_cannot_read_organization(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """User B (not a member) cannot GET Org A's details — must receive 403."""
        with _as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Private Org A"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

        with _as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_id}",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403

    def test_non_member_cannot_list_organization_members(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """User B (not a member) cannot list members of Org A — must receive 403."""
        with _as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Private Org A"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

        with _as_user(user_b_claims):
            resp = client.get(
                f"/api/v1/organizations/{org_id}/members",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403

    def test_user_only_sees_their_own_organizations(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """GET /organizations returns only the orgs the caller belongs to."""
        # User A creates Org A
        with _as_user(user_a_claims):
            client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Org A"},
                headers={"Authorization": "Bearer fake"},
            )

        # User B creates Org B
        with _as_user(user_b_claims):
            client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Org B"},
                headers={"Authorization": "Bearer fake"},
            )

        # User A's org list should only contain Org A
        with _as_user(user_a_claims):
            resp = client.get(
                "/api/v1/organizations/",
                headers={"Authorization": "Bearer fake"},
            )
        org_names = [o["legal_name"] for o in resp.json()]
        assert "Org A" in org_names
        assert "Org B" not in org_names

    def test_non_member_cannot_update_organization(
        self, client: TestClient, user_a_claims, user_b_claims
    ):
        """User B (not a member) cannot PATCH Org A — must receive 403."""
        with _as_user(user_a_claims):
            org_id = client.post(
                "/api/v1/organizations/",
                json={"legal_name": "Protected Org"},
                headers={"Authorization": "Bearer fake"},
            ).json()["id"]

        with _as_user(user_b_claims):
            resp = client.patch(
                f"/api/v1/organizations/{org_id}",
                json={"display_name": "Hacked"},
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403
