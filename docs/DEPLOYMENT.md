# Deployment record

## GenLayer Studio

| Field | Value |
| --- | --- |
| Network | Studionet, chain ID 61999 |
| Contract | `AgentPactLive.py` from `contracts/agentpact.py` |
| Address | `0x4E046c60D373d0bf5e2a772F2Ee4EbD3b333D9Ea` |
| Deployment transaction | `0xe4e525d486d729dcc87dcef18839927d0d243467fec0b9adefd8e1c827e01eb8` |
| Consensus | Normal (full consensus); transaction FINALIZED |
| Read verification | `job_count()` returned `0` in Accepted state |

[Inspect the contract in Studio Explorer](https://explorer-studio.genlayer.com/address/0x4E046c60D373d0bf5e2a772F2Ee4EbD3b333D9Ea).

The published web interface uses this Studionet address for finalized reads. The production marketplace successfully read `job_count = 0` through `genlayer-js` 1.1.8 on September 25, 2026. The Studio account had 0 GEN, so a funded job, validator adjudication, appeal, and payout have **not** been exercised onchain. Hosted Studio does not support native token transfers to and from contracts. The web interface disables all writes for this reason.

## Bradbury

The contract is not deployed to Bradbury. This project targets Studionet for its present contract deployment and live reads. A network with native transfers will be required to exercise the full escrow lifecycle.
