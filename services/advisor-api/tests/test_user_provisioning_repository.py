from hive_sight_advisor_api.repositories.user_provisioning_repository import (
    UserProvisioningRepository,
)


def test_first_sign_in_provisions_a_user_workspace_and_owner_membership(
    postgres_connection,
) -> None:
    repository = UserProvisioningRepository(postgres_connection)

    identity = repository.find_or_provision(
        google_sub="sub-1", email="bea@example.com", display_name="Bea Keeper"
    )

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT google_sub, email, display_name FROM users WHERE id = %s", (identity.user_id,)
        )
        row = cursor.fetchone()
        assert row == ("sub-1", "bea@example.com", "Bea Keeper")

        cursor.execute(
            "SELECT id FROM workspaces WHERE id = %s", (identity.workspace_id,)
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            """
            SELECT role, status FROM workspace_memberships
            WHERE user_id = %s AND workspace_id = %s
            """,
            (identity.user_id, identity.workspace_id),
        )
        assert cursor.fetchone() == ("owner", "active")


def test_a_repeat_sign_in_with_the_same_sub_reuses_the_existing_user_and_workspace(
    postgres_connection,
) -> None:
    repository = UserProvisioningRepository(postgres_connection)

    first = repository.find_or_provision(
        google_sub="sub-1", email="bea@example.com", display_name="Bea Keeper"
    )
    second = repository.find_or_provision(
        google_sub="sub-1", email="bea@example.com", display_name="Bea Keeper"
    )

    assert second.user_id == first.user_id
    assert second.workspace_id == first.workspace_id

    with postgres_connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM users WHERE google_sub = %s", ("sub-1",))
        assert cursor.fetchone() == (1,)
        cursor.execute(
            "SELECT count(*) FROM workspace_memberships WHERE user_id = %s", (first.user_id,)
        )
        assert cursor.fetchone() == (1,)


def test_a_different_sub_gets_its_own_user_and_workspace(postgres_connection) -> None:
    repository = UserProvisioningRepository(postgres_connection)

    first = repository.find_or_provision(
        google_sub="sub-1", email="bea@example.com", display_name="Bea Keeper"
    )
    second = repository.find_or_provision(
        google_sub="sub-2", email="alex@example.com", display_name="Alex Apiary"
    )

    assert second.user_id != first.user_id
    assert second.workspace_id != first.workspace_id
