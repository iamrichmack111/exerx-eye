from pathlib import Path
from exerx_eye.db import ExerxEye


def test_username_only_account_and_export(tmp_path: Path):
    db = ExerxEye(tmp_path / "v8.db")
    uid = db.create_user("localuser", "hash")
    user = db.user_by_login("localuser")
    assert user is not None
    assert user["username"] == "localuser"
    assert db.user_by_login(user["email"]) is None
    bundle = db.user_export_bundle(uid)
    assert bundle["account"]["username"] == "localuser"
    assert "email" not in bundle["account"]
    assert db.schema_version() >= 7
    db.close()
