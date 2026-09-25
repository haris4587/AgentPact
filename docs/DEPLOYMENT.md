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

This is a Studio deployment for contract execution validation. The Studio account had 0 GEN, so a funded job, validator adjudication, appeal, and payout have **not** been exercised onchain. Studio's interface also warns that its environment does not support token transfers. This address must not be entered into the Bradbury-only web interface.

## Bradbury

The contract is not deployed to Bradbury yet. The published frontend intentionally shows sample jobs and disables escrow writes. Before activating it: deploy with a funded Bradbury wallet, run a funded job lifecycle including a pinned evidence fetch and settlement, then set `VITE_CONTRACT_ADDRESS` for the production build. Record the final address and transaction here.
