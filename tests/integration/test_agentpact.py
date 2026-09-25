import hashlib
import json
import time
import pytest

CONTRACT = "contracts/agentpact.py"
SHA = "0123456789abcdef0123456789abcdef01234567"
URL = f"https://raw.githubusercontent.com/team/work/{SHA}/evidence.json"
BODY = b'{"summary":"Implemented all requested items","artifacts":["report.md"]}'
DIGEST = hashlib.sha256(BODY).hexdigest()
CRITERIA = json.dumps(["Deliver a report with cited sources", "Include a summary of results"])


def funded_job(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    direct_vm.value = 10**18
    contract.create_job("Research brief", "Research three open source analytics tools", CRITERIA,
                        "team/work", int(time.time()) + 86400, 3600)
    direct_vm.value = 0
    return contract


def test_escrow_assignment_and_immutable_submission(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = funded_job(direct_vm, direct_deploy)
    job = json.loads(contract.get_job(0))
    assert job["reward_wei"] == str(10**18)
    assert job["status"] == "OPEN"
    with direct_vm.prank(job["buyer"]):
        with direct_vm.expect_revert("Buyer cannot accept"):
            contract.accept_job(0)
    with direct_vm.prank(direct_alice):
        contract.accept_job(0)
    assert json.loads(contract.get_job(0))["status"] == "ACCEPTED"
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("Only assigned worker"):
            contract.submit_evidence(0, URL, DIGEST)
    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("pinned commit"):
            contract.submit_evidence(0, "https://raw.githubusercontent.com/team/work/main/evidence.json", DIGEST)
        contract.submit_evidence(0, URL, DIGEST)
        with direct_vm.expect_revert("Only assigned worker"):
            contract.submit_evidence(0, URL, DIGEST)
    assert json.loads(contract.get_job(0))["evidence_sha256"] == DIGEST


def test_independent_verdict_and_hash_binding(direct_vm, direct_deploy, direct_alice):
    contract = funded_job(direct_vm, direct_deploy)
    with direct_vm.prank(direct_alice):
        contract.accept_job(0)
        contract.submit_evidence(0, URL, DIGEST)
    direct_vm.mock_web(r"raw.githubusercontent.com/team/work/", {"status": 200, "body": "altered"})
    with direct_vm.expect_revert("Evidence hash mismatch"):
        contract.adjudicate(0)
    direct_vm.clear_mocks()
    direct_vm.mock_web(r"raw.githubusercontent.com/team/work/", {"status": 200, "body": BODY.decode()})
    direct_vm.mock_llm(r"Assess work evidence", '{"passes":[true,false],"reasons":["Source present","Summary missing"]}')
    contract.adjudicate(0)
    job = json.loads(contract.get_job(0))
    assert job["payout_bps"] == 5000
    assert job["status"] == "PROVISIONAL"
    assert direct_vm.run_validator() is True


def test_invalid_criteria_and_zero_escrow(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("Fund the escrow"):
        contract.create_job("Research brief", "Research three open source analytics tools", CRITERIA,
                            "team/work", int(time.time()) + 86400, 3600)
    direct_vm.value = 10**18
    with direct_vm.expect_revert("Provide 1–8 criteria"):
        contract.create_job("Research brief", "Research three open source analytics tools", "[]",
                            "team/work", int(time.time()) + 86400, 3600)
