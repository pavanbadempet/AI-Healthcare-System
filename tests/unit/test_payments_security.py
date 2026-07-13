from unittest.mock import patch

from backend import auth, models, payments


def _create_user(db_session, username: str = "payment_user") -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


def test_payment_credentials_from_env():
    with patch.dict(
        "os.environ",
        {"RAZORPAY_KEY_ID": "rzp_live_key", "RAZORPAY_KEY_SECRET": "live_secret"},
        clear=True,
    ):
        assert payments.load_razorpay_credentials() == ("rzp_live_key", "live_secret")


def test_payment_credentials_missing_outside_testing_disables_gateway():
    with patch.dict("os.environ", {}, clear=True):
        assert payments.load_razorpay_credentials() == (None, None)


def test_payment_credentials_use_placeholders_only_during_tests():
    with patch.dict("os.environ", {"TESTING": "1"}, clear=True):
        assert payments.load_razorpay_credentials() == ("rzp_test_placeholder", "secret_placeholder")


def test_create_order_uses_server_side_plan_pricing(client, db_session):
    user = _create_user(db_session)

    with patch(
        "backend.payments.client.order.create",
        return_value={"id": "order_pro", "amount": 99900, "currency": "INR", "status": "created"},
    ) as create_order:
        response = client.post(
            "/payments/create-order",
            json={"plan_id": "pro", "amount": 1, "currency": "USD"},
            headers=_auth_headers(user.username),
        )

    assert response.status_code == 200
    create_order.assert_called_once()
    data = create_order.call_args.kwargs["data"]
    assert data["amount"] == 99900
    assert data["currency"] == "INR"
    assert data["notes"] == {"user_id": str(user.id), "plan": "pro"}


def test_create_order_rejects_unknown_plan(client, db_session):
    user = _create_user(db_session)

    with patch("backend.payments.client.order.create") as create_order:
        response = client.post(
            "/payments/create-order",
            json={"plan_id": "basic"},
            headers=_auth_headers(user.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid payment plan"
    create_order.assert_not_called()


def test_create_order_reports_unconfigured_gateway(client, db_session):
    user = _create_user(db_session, "unconfigured_gateway_user")

    with patch("backend.payments.client", None):
        response = client.post(
            "/payments/create-order",
            json={"plan_id": "pro"},
            headers=_auth_headers(user.username),
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Payment gateway is not configured"


def test_create_order_hides_gateway_error_details(client, db_session, caplog):
    user = _create_user(db_session, "gateway_create_user")
    sensitive_error = "Razorpay failure key_secret=secret_placeholder card=4111111111111111"
    caplog.set_level("ERROR", logger="backend.payments")

    with patch("backend.payments.client.order.create", side_effect=Exception(sensitive_error)):
        response = client.post(
            "/payments/create-order",
            json={"plan_id": "pro"},
            headers=_auth_headers(user.username),
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create payment order"
    assert sensitive_error not in str(response.json())
    assert "secret_placeholder" not in str(response.json())
    assert "4111111111111111" not in str(response.json())
    assert sensitive_error not in caplog.text
    assert "secret_placeholder" not in caplog.text
    assert "4111111111111111" not in caplog.text


def test_verify_payment_rejects_order_for_different_user(client, db_session):
    user = _create_user(db_session, "payer")
    other_user = _create_user(db_session, "other_payer")
    user_id = user.id

    with patch("backend.payments.client.utility.verify_payment_signature") as verify_signature, \
         patch(
             "backend.payments.client.order.fetch",
             return_value={
                 "id": "order_other",
                 "amount": 99900,
                 "currency": "INR",
                 "notes": {"user_id": str(other_user.id), "plan": "pro"},
             },
         ):
        response = client.post(
            "/payments/verify",
            json={
                "razorpay_order_id": "order_other",
                "razorpay_payment_id": "pay_123",
                "razorpay_signature": "sig_123",
                "plan_id": "pro",
            },
            headers=_auth_headers(user.username),
        )

    updated_user = db_session.get(models.User, user_id)
    assert response.status_code == 403
    assert response.json()["detail"] == "Payment order does not belong to current user"
    assert updated_user.plan_tier == "free"
    verify_signature.assert_called_once()


def test_verify_payment_derives_tier_from_verified_order(client, db_session):
    user = _create_user(db_session, "enterprise_payer")
    user_id = user.id

    with patch("backend.payments.client.utility.verify_payment_signature") as verify_signature, \
         patch(
             "backend.payments.client.order.fetch",
             return_value={
                 "id": "order_enterprise",
                 "amount": 249900,
                 "currency": "INR",
                 "notes": {"user_id": str(user.id), "plan": "enterprise"},
             },
         ):
        response = client.post(
            "/payments/verify",
            json={
                "razorpay_order_id": "order_enterprise",
                "razorpay_payment_id": "pay_456",
                "razorpay_signature": "sig_456",
            },
            headers=_auth_headers(user.username),
        )

    updated_user = db_session.get(models.User, user_id)
    assert response.status_code == 200
    assert response.json()["plan_tier"] == "clinic"
    assert updated_user.plan_tier == "clinic"
    assert updated_user.subscription_expiry is not None
    verify_signature.assert_called_once()


def test_verify_payment_reports_unconfigured_gateway(client, db_session):
    user = _create_user(db_session, "unconfigured_verify_user")

    with patch("backend.payments.client", None):
        response = client.post(
            "/payments/verify",
            json={
                "razorpay_order_id": "order_missing_gateway",
                "razorpay_payment_id": "pay_missing_gateway",
                "razorpay_signature": "sig_missing_gateway",
            },
            headers=_auth_headers(user.username),
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Payment gateway is not configured"


def test_verify_payment_hides_gateway_error_details(client, db_session, caplog):
    user = _create_user(db_session, "gateway_verify_user")
    sensitive_error = "Razorpay fetch failed key_secret=secret_placeholder payment=pay_sensitive"
    caplog.set_level("ERROR", logger="backend.payments")

    with patch("backend.payments.client.utility.verify_payment_signature") as verify_signature, \
         patch("backend.payments.client.order.fetch", side_effect=Exception(sensitive_error)):
        response = client.post(
            "/payments/verify",
            json={
                "razorpay_order_id": "order_gateway_fail",
                "razorpay_payment_id": "pay_sensitive",
                "razorpay_signature": "sig_789",
            },
            headers=_auth_headers(user.username),
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to verify payment"
    assert sensitive_error not in str(response.json())
    assert "secret_placeholder" not in str(response.json())
    assert "pay_sensitive" not in str(response.json())
    assert sensitive_error not in caplog.text
    assert "secret_placeholder" not in caplog.text
    assert "pay_sensitive" not in caplog.text
    verify_signature.assert_called_once()
