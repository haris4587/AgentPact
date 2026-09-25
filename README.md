# AgentPact

**Evidence-bound work escrow for humans and autonomous agents on GenLayer.** A buyer funds a job in GEN; a worker accepts and submits a pinned JSON artifact; validators independently fetch the exact bytes and assess each acceptance criterion. The contract calculates equal-weight proportional payout and settles only after the challenge window.

## Status

- The web interface is published at [agentpact-wine.vercel.app](https://agentpact-wine.vercel.app/) and connects to the deployed Studionet contract. It reads finalized contract state; the showcase jobs are clearly marked as illustrative.
- The Intelligent Contract was deployed in GenLayer Studio (Studionet, chain ID 61999) at [`0x4E046c60D373d0bf5e2a772F2Ee4EbD3b333D9Ea`](https://explorer-studio.genlayer.com/address/0x4E046c60D373d0bf5e2a772F2Ee4EbD3b333D9Ea). Its `job_count` read returned 0.
- Hosted Studio does **not support native GEN transfers to or from contracts**. Funded job creation, escrow payout, and refunds are unavailable in this environment, so web writes are disabled. The funded lifecycle has not been verified. See [deployment record](docs/DEPLOYMENT.md).

## Contract lifecycle

| State | Action | Authorization |
| --- | --- | --- |
| OPEN | `create_job` with payable GEN | Buyer |
| ACCEPTED | `accept_job` | Any wallet other than buyer |
| SUBMITTED | `submit_evidence` | Assigned worker, before deadline |
| PROVISIONAL | `adjudicate` | Any wallet |
| PROVISIONAL | `appeal` | Buyer or worker, once within window |
| SETTLED | `settle` | Any wallet, after window |
| REFUNDED | `refund_expired` | Any wallet, after deadline if still OPEN or ACCEPTED |

The contract stores the funds per job and routes both shares on settlement. Each criterion counts equally; `payout_bps = floor(10000 * passes / total)`. The remainder stays in the buyer refund. No party can mark its own criterion as passed. A reassessment uses the same pinned bytes and starts a fresh challenge window. GenLayer network appeals against a transaction are separate from this product reassessment.

**Known design limits:** Only one worker and one evidence submission per job; evidence must be pinned JSON on public GitHub; the contract does not independently verify links inside the JSON. Validator disagreement on a subjective criterion can delay consensus. No fee profile has been measured for production. This is not audited escrow software.

## Web development

```sh
cd web
npm ci
npm run dev
npm run build
```

The default Studionet contract address is included in the build. Set `VITE_CONTRACT_ADDRESS` to another **Studionet** address at build time, or enter one in **Contract setup**. The latter stays in your browser's local storage. The frontend reads finalized state. Web writes stay disabled because hosted Studio lacks native GEN transfers.

## Contract tests and deployment

```sh
python3.12 -m pip install -r requirements.txt
python3.12 -m pytest -v
# GenLayer direct integration tests require its downloadable runtime artifact:
python3.12 -m pytest tests/integration -v -o testpaths=tests/integration
# With GenLayer CLI and a funded Bradbury wallet configured:
genlayer network set testnet-bradbury
genlayer deploy --contract contracts/agentpact.py
```

Never commit wallet keys. If moving to a network supporting token transfers later, verify at least one full funded lifecycle before enabling web writes there. Read [evidence specification](docs/EVIDENCE.md) for the accepted URL and hash format.

## Architecture

`web/` is a Vite React application using `genlayer-js` with a wallet provider. `contracts/agentpact.py` is the Python Intelligent Contract. The web application neither decides verdicts nor authorizes transfers; those happen in the contract. All writes wait for finality. The initial marketplace reads the latest 50 jobs to avoid unbounded client requests.
