"""Local model tests for deterministic contract rules, with GenVM interfaces stubbed.
These are not validator-network integration tests; see tests/integration.
"""
import hashlib
import importlib.util
import json
import sys
import time
import types
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[2] / 'contracts' / 'agentpact.py'
SHA = '0123456789abcdef0123456789abcdef01234567'
URL = f'https://raw.githubusercontent.com/team/work/{SHA}/evidence.json'
BODY = b'{"summary":"A complete report"}'
DIGEST = hashlib.sha256(BODY).hexdigest()


class TreeMap(dict):
    def __class_getitem__(cls, key):
        return cls


class Message:
    sender_address = '0x' + '1' * 40
    value = 0


class Web:
    response = BODY
    status = 200

    def get(self, url):
        return types.SimpleNamespace(body=self.response, status_code=self.status)


class VM:
    UserError = ValueError
    class Return:
        def __init__(self, calldata):
            self.calldata = calldata

    def run_nondet_unsafe(self, fn, validator):
        result = fn()
        assert validator(self.Return(result))
        return result


class Prompt:
    response = {'passes': [True, False], 'reasons': ['Supported', 'Not supported']}

    def __call__(self, prompt, response_format):
        assert response_format == 'json'
        return self.response


@pytest.fixture
def model(monkeypatch):
    msg = Message()
    web = Web()
    prompt = Prompt()
    write = lambda f: f
    public = types.SimpleNamespace(write=write, view=write)
    public.write.payable = write  # function attrs support the decorator chain
    transfers = []
    def interface(cls):
        cls.__init__ = lambda self, address: setattr(self, 'address', address)
        cls.emit_transfer = lambda self, value: transfers.append((self.address, value))
        return cls
    gl = types.SimpleNamespace(
        Contract=object, public=public, message=msg,
        evm=types.SimpleNamespace(contract_interface=interface),
        nondet=types.SimpleNamespace(web=web, exec_prompt=prompt),
        eq_principle=types.SimpleNamespace(strict_eq=lambda fn: fn()), vm=VM(),
    )
    sdk = types.ModuleType('genlayer')
    sdk.gl, sdk.TreeMap, sdk.u256, sdk.Address = gl, TreeMap, int, str
    monkeypatch.setitem(sys.modules, 'genlayer', sdk)
    spec = importlib.util.spec_from_file_location('agentpact_model', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, msg, web, prompt, transfers


def create(model):
    module, msg, _, _, _ = model
    contract = module.AgentPact()
    msg.value = 10**18
    contract.create_job('Research brief', 'Research three analytics products',
                        json.dumps(['Supply three references', 'Explain tradeoffs clearly']),
                        'team/work', int(time.time()) + 86400, 3600)
    msg.value = 0
    return contract


def test_url_and_criterion_guardrails(model):
    module, _, _, _, _ = model
    assert module.pinned_url(URL)
    assert not module.pinned_url(URL.replace(SHA, 'main'))
    assert not module.pinned_url(URL.replace('raw.githubusercontent.com', 'evil.example'))
    with pytest.raises(ValueError, match='1–8'):
        module.validate_criteria('[]')
    with pytest.raises(ValueError, match='8–250'):
        module.validate_criteria('["short"]')


def test_create_accept_and_submission_permissions(model):
    _, msg, _, _, _ = model
    contract = create(model)
    job = json.loads(contract.get_job(0))
    assert job['reward_wei'] == str(10**18)
    with pytest.raises(ValueError, match='Buyer cannot accept'):
        contract.accept_job(0)
    msg.sender_address = '0x' + '2' * 40
    contract.accept_job(0)
    with pytest.raises(ValueError, match='pinned commit'):
        contract.submit_evidence(0, URL.replace(SHA, 'main'), DIGEST)
    contract.submit_evidence(0, URL, DIGEST)
    assert json.loads(contract.get_job(0))['status'] == 'SUBMITTED'
    with pytest.raises(ValueError, match='Only assigned worker'):
        contract.submit_evidence(0, URL, DIGEST)


def test_mismatched_bytes_cannot_be_adjudicated(model):
    _, msg, web, _, _ = model
    contract = create(model)
    msg.sender_address = '0x' + '2' * 40
    contract.accept_job(0)
    contract.submit_evidence(0, URL, DIGEST)
    web.response = b'{"summary":"tampered"}'
    with pytest.raises(ValueError, match='hash mismatch'):
        contract.adjudicate(0)
    web.response = BODY
    contract.adjudicate(0)
    job = json.loads(contract.get_job(0))
    assert job['passes'] == [True, False]
    assert job['payout_bps'] == 5000
    assert job['status'] == 'PROVISIONAL'


def test_appeal_is_one_round_and_party_only(model):
    _, msg, _, prompt, _ = model
    contract = create(model)
    msg.sender_address = '0x' + '2' * 40
    contract.accept_job(0)
    contract.submit_evidence(0, URL, DIGEST)
    contract.adjudicate(0)
    msg.sender_address = '0x' + '3' * 40
    with pytest.raises(ValueError, match='Only a party'):
        contract.appeal(0)
    msg.sender_address = '0x' + '1' * 40
    prompt.response = {'passes': [True, True], 'reasons': ['Yes', 'Yes']}
    contract.appeal(0)
    assert json.loads(contract.get_job(0))['payout_bps'] == 10000
    with pytest.raises(ValueError, match='No appeal available'):
        contract.appeal(0)


def test_settlement_sends_proportional_shares_once(model):
    _, msg, _, _, transfers = model
    contract = create(model)
    buyer = msg.sender_address
    worker = '0x' + '2' * 40
    msg.sender_address = worker
    contract.accept_job(0)
    contract.submit_evidence(0, URL, DIGEST)
    contract.adjudicate(0)
    with pytest.raises(ValueError, match='Settlement not available'):
        contract.settle(0)
    job = json.loads(contract.get_job(0))
    job['challenge_until'] = int(time.time()) - 1
    contract.jobs[0] = json.dumps(job)
    contract.settle(0)
    assert transfers == [(worker, 5 * 10**17), (buyer, 5 * 10**17)]
    assert contract.locked[0] == 0
    with pytest.raises(ValueError, match='Settlement not available'):
        contract.settle(0)


def test_expiry_refunds_buyer(model):
    _, msg, _, _, transfers = model
    contract = create(model)
    buyer = msg.sender_address
    job = json.loads(contract.get_job(0))
    job['deadline'] = int(time.time()) - 1
    contract.jobs[0] = json.dumps(job)
    contract.refund_expired(0)
    assert transfers == [(buyer, 10**18)]
    assert json.loads(contract.get_job(0))['status'] == 'REFUNDED'
    assert contract.locked[0] == 0
