<p align="center">
  <img src="https://raw.githubusercontent.com/mcevoyinit/vellum/main/vellum-icon.svg" width="120" alt="Vellum" />
</p>

<h1 align="center">Vellum</h1>

<p align="center">
  Open protocol for multi-party enterprise workflows.
</p>

<p align="center">
  <a href="#what-vellum-is">What it is</a> &middot;
  <a href="#use-cases">Use cases</a> &middot;
  <a href="#quickstart">Quickstart</a> &middot;
  <a href="#architecture">Architecture</a> &middot;
  <a href="#modules">Modules</a>
</p>

---

Vellum defines the protocols, types, and configuration schemas for
schema-driven multi-party negotiation, persistence, integrity, and
identity. This repository ships the **public protocol surface** plus a
TypeScript/React UI SDK.

The vertical changes. The protocol doesn't.

A production runtime — consensus engine, field state machine, proposal
manager, orchestrator, sealing workflow — is available separately under
commercial license. Implement the protocols here against your own runtime,
or contact the maintainer.

## What Vellum Is

| Layer | What this repo provides |
|-------|-------------------------|
| **Negotiation** | Consensus rule schema, proposal types, store protocol, namespace adapter protocol, entity-type registry |
| **State Machine** | Generic config-driven finite state machine with pluggable transition validators |
| **Persistence** | Dynamic pipeline + protocol interfaces (type resolution, ID generation, validation, backend) |
| **Sealing** | Content hashing reference impl (SHA256 + canonical JSON) and seal authority protocol |
| **Identity** | Actor context, role-based access control primitives |
| **Middleware** | Idempotency, rate limiting, retry-with-backoff, audit pipeline hooks |
| **Events** | Typed event sourcing primitives, event stream protocol |
| **UI SDK** | React components and hooks for schema-driven forms, tables, and negotiation flows |

## Use Cases

Any domain where multiple parties negotiate terms and settle agreements on record.

| Domain | Parties | What they negotiate |
|--------|---------|---------------------|
| Securities Settlement | dealer, counterparty, custodian | settlement date, price, delivery method |
| Repo Agreements | repo desk, counterparty | repo rate, haircut, collateral, maturity |
| Insurance | insurer, reinsured, broker | premium, coverage, deductibles, exclusions |
| Syndicated Loans | lead arranger, participant banks, borrower | spread, covenants, drawdown |
| Real Estate & Leases | lessor, lessee | rent, term, break clause, fit-out, deposit |
| Healthcare Contracts | provider, payer | reimbursement rates, formulary, prior auth rules |
| Energy Trading | generator, offtaker | strike price, volume, delivery point, curtailment |
| Cross-Border Payments | originator, correspondent, beneficiary bank | FX rate, fees, compliance |

## Quickstart

Define a consensus rule schema and entity type. The protocol is what's
public; the engine that interprets it ships separately.

```python
from vellum.negotiation import (
    ConsensusConfig,
    ConsensusRule,
    EntityTypeConfig,
    register_entity_type,
)

# Declarative consensus rules — what fields require what approvers
config = ConsensusConfig(
    party_roles={"lessor", "lessee"},
    default_required_approvers={"lessor", "lessee"},
    default_authoritative_role="lessor",
)
config.add_rule(ConsensusRule(
    field_pattern="rent.*",
    required_approvers={"lessor", "lessee"},
    authoritative_role="lessee",
))

# Register your entity type
register_entity_type(EntityTypeConfig(
    graphql_type="LeaseAgreement",
    lifecycle_stages=["DRAFT", "NEGOTIATING", "SIGNED", "ACTIVE"],
    participant_fields={
        "lessor": ("lessorId", "lessor.id"),
        "lessee": ("lesseeId", "lessee.id"),
    },
    source_namespace_field="lessorId",
    field_path_mappings={},
))
```

Use the protocols (`ProposalStore`, `NamespaceAdapter`, `ContentHasher`,
`SealAuthority`, `PersistenceBackend`) to wire your own runtime.

## Install

```bash
pip install -e .
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Your Application                      │
│         (transport, auth, UI, chain submission)          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Vellum Protocol  (this repo)               │
├─────────────┬──────────────┬──────────────┬─────────────┤
│ Negotiation │ State Machine│   Sealing    │   Events    │
│   schema    │   schema     │   hashing    │  protocols  │
│   types     │   protocol   │   protocol   │   types     │
├─────────────┴──────────────┴──────────────┴─────────────┤
│              Identity  &  Persistence                   │
│                                                         │
│        Protocols, types, reference utilities            │
├─────────────────────────────────────────────────────────┤
│                    Middleware                            │
│                                                         │
│  Idempotency, rate limiting, retry, pipeline hooks      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│       Vellum Core Runtime  (commercial license)         │
│                                                         │
│  Consensus engine · Field state machine · Proposal      │
│  manager · Orchestrator · Sealing workflow              │
└─────────────────────────────────────────────────────────┘
```

## Modules

| Module | Purpose |
|--------|---------|
| `vellum.negotiation` | Consensus rule schema, proposal types, store protocol, entity registry |
| `vellum.statemachine` | Generic config-driven FSM with transition validators |
| `vellum.sealing` | SHA256 content hashing, seal protocol, verification types |
| `vellum.identity` | Actor context, RBAC primitives |
| `vellum.persistence` | Dynamic pipeline, type resolution, persistence protocols |
| `vellum.middleware` | Idempotency keys, rate limiting, retry with backoff, audit pipelines |
| `vellum.events` | Event sourcing, typed event streams, replay |
| `vellum.core` | Shared utilities |

## Requirements

Python >= 3.10.

## License

MIT — see [LICENSE](./LICENSE).

The Vellum Core runtime (consensus engine, orchestration, sealing workflow,
vertical templates) is shipped separately under a commercial license.
