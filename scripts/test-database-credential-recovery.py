#!/usr/bin/env python3
"""Render actual reference chart; validate optional database Secret projections."""
import argparse
from pathlib import Path
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--helm", default="helm")
args = parser.parse_args()
chart = ROOT / "helm/gamestory-schneider-platform"


def render(environment, enabled=False, overrides=()):
    command = [args.helm, "template", "logai", str(chart), "--namespace", "68225-logai-uat",
               "-f", str(ROOT / "environments" / environment / "values.yaml")]
    if enabled:
        command += ["-f", str(ROOT / "environments/uat/database-credential-recovery.yaml")]
    command += list(overrides)
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return [r for r in yaml.safe_load_all(result.stdout) if r]


for environment in ("build", "release", "client-local", "dev-aws", "uat", "prod"):
    baseline = render(environment)
    enabled = render(environment, True)
    before = {r["metadata"]["name"]: r for r in baseline if r["kind"] == "Deployment"}
    after = {r["metadata"]["name"]: r for r in enabled if r["kind"] == "Deployment"}
    assert before.keys() == after.keys()
    for name, deployment in after.items():
        if not name.endswith("-logai-api"):
            assert deployment == before[name], "Recovery must affect only LogAI API"
            continue
        old_pod = before[name]["spec"]["template"]["spec"]
        pod = deployment["spec"]["template"]["spec"]
        container = pod["containers"][0]
        old_container = old_pod["containers"][0]
        assert pod["securityContext"] == old_pod["securityContext"]
        assert pod["securityContext"]["fsGroup"] == 10001
        assert container["securityContext"] == old_container["securityContext"]
        for probe in ("startupProbe", "readinessProbe", "livenessProbe"):
            assert container[probe] == old_container[probe]
        env = {item["name"]: item for item in container["env"]}
        assert env["DB_CREDENTIAL_REFRESH_ENABLED"]["value"] == "true"
        assert env["DATABASE_PASSWORD_FILE"]["value"] == "/var/run/secrets/logai-db/password"
        assert env["DB_CREDENTIAL_REFRESH_BACKOFF_SECONDS"]["value"] == "5"
        assert env["DB_CREDENTIAL_REFRESH_MAX_WAIT_SECONDS"]["value"] == "10"
        for item in old_container["env"]:
            if item["name"] != "DB_CREDENTIAL_REFRESH_ENABLED":
                assert env[item["name"]] == item
        assert not any(v["name"] == "db-credentials" for v in old_pod["volumes"])
        mount = next(m for m in container["volumeMounts"] if m["name"] == "db-credentials")
        assert mount == {"name": "db-credentials", "mountPath": "/var/run/secrets/logai-db", "readOnly": True}
        for mount_before in old_container["volumeMounts"]:
            assert mount_before in container["volumeMounts"]
        volume = next(v for v in pod["volumes"] if v["name"] == "db-credentials")
        secret = volume["secret"]
        assert secret["defaultMode"] == 0o440
        assert secret["secretName"] == env["DATABASE_URL"]["valueFrom"]["secretKeyRef"]["name"]
        assert secret["items"] == [{"key": "password", "path": "password"}]
        assert "subPath" not in str(container["volumeMounts"])
        assert not any("password" in key.lower() for key in deployment["spec"]["template"]["metadata"]["annotations"])

custom = render("uat", True, ["--set", "externalDatabase.existingSecret=logai-db-secret",
                              "--set", "externalDatabase.passwordKey=rotating-password"])
api = next(r for r in custom if r["kind"] == "Deployment" and r["metadata"]["name"].endswith("-logai-api"))
secret = next(v["secret"] for v in api["spec"]["template"]["spec"]["volumes"] if v["name"] == "db-credentials")
assert secret["secretName"] == "logai-db-secret"
assert secret["items"] == [{"key": "rotating-password", "path": "password"}]
print("PASS: six environments, disabled/enabled modes, Secret/key overrides, read-only directory mounts, fsGroup access, preserved probes/security and non-API workloads")
