---
date: 2026-01-03T00:00:00+01:00
title: "Blockchain API"
description: "Explorers, wallets, you name it"
imageFront: "images/blog/blockchain-api/blockchain-logo.png"
imageFrontHeight: "180"
imageHeader: "images/blog/blockchain-api/blockchain-header.png"
---

When you design a new blockchain explorer, commercial API, or wallet backend, start with two questions: **what can the node answer on its own** over standard JSON-RPC, and **what can't it**? Everything you end up building — the index — lives in the gap between the two.

## What the node can answer on its own

Out of the box, over standard JSON-RPC, the answer differs sharply by chain family.

#### UTXO chains (Bitcoin-like)
- Blocks and transactions by hash/height.
- Mempool contents and individual outpoint state (spent/unspent) by txid+vout.
- Fee estimates and chain state.

#### EVM chains (Ethereum-like)
- Point-in-time account state: balance, nonce, contract storage, code.
- Transactions and receipts by tx hash.
- Blocks by number, with full tx list if requested.
- Logs by filter over a block range (nodes typically index logs, but queries are range-based).

#### Rich-RPC chains (account-based — Solana, XRP, Stellar)
- Address → history, **served by the node itself**: Solana `getSignaturesForAddress` (paginated by signature cursor), XRP Ledger `account_tx`, Stellar Horizon `/accounts/{id}/transactions`.
- Address → token holdings, **served by the node itself**: Solana `getTokenAccountsByOwner` (every SPL token account of an owner), XRP `account_lines` (trust lines / issued-asset balances), Stellar account `balances` (native + assets in one call).
- Current balance of an arbitrary address directly — account ledgers keep balance as first-class state (`getBalance` / `account_info` / Horizon account `balances`), with no UTXO aggregation needed.

## What the node cannot answer

These are the address-level questions a plain node won't serve without scanning the whole chain.

#### UTXO chains
- All transactions for a given address or xpub without scanning all blocks.
- Current balance for an arbitrary address without scanning all its txs/UTXOs.
- Address-level history, paging, or balance history over time.

#### EVM chains
- Address-indexed transaction history (not available in standard JSON-RPC).
- Token lists and balances for an address without scanning logs or traces.
- Internal transactions for an address without tracing each block/tx.
- Address-level history paging or balance history over time.

#### Rich-RPC chains
- Comparatively little — the node already answers the address-indexed queries above. What's missing is mostly **enrichment**, not core relations: fiat pricing, human-readable labels, decoded instructions/memos, and cross-account analytics.

## The index you have to build

So you design an indexing scheme with the bare minimum to serve address-balance and tx-history queries efficiently — the relations the node won't give you, one set per chain family.

#### UTXO chains — missing relations
- **Address → Transactions**  
  Map any address (or xpub) to the set of txs that touch it, with ordering for paging.
- **Address → Current Balance**  
  Aggregate spendable UTXOs per address (and optionally per xpub/account).
- **UTXO Set (txid:vout → state)**  
  Track spend/unspent state for fast balance and spendability checks.
- **Address → History (time/height deltas)**  
  For balance history charts, first/last activity, and pagination.
- **xpub → Derived Addresses** (wallet layer)  
  Keypath-based derivation and grouping.

#### EVM chains — missing relations
- **Address → Transactions**  
  Map address to txs it sent/received (native transfers), with paging.
- **Address → Token Transfers**  
  Map (address, token) to all token transfer events, with ordering.
- **Address → Token Balances**  
  Maintain current ERC20/721/1155 balances without rescanning logs.
- **Contract → Holders / Holder Counts** (optional)  
  Useful for analytics and token pages.
- **Internal Transfers → Addresses**  
  Requires traces to index internal calls/transfers by address.
- **Address → Activity Summary**  
  First/last activity, counts, volumes, etc., for fast UI queries.

#### Rich-RPC chains — (almost) nothing to index

Here the assumption flips: the **node is already the address index**. Solana, XRP and Stellar are account-based ledgers whose native API exposes *address → history* and *owner → token holdings* as first-class queries — exactly the relations you would otherwise have to build yourself.

- **Address → Transactions / Token holdings**  
  *Provided by the node* (`getSignaturesForAddress` + `getTokenAccountsByOwner`; `account_tx` + `account_lines`; Horizon account endpoints). No secondary index required.
- **What's left for the backend**  
  The wallet backend — usually the holder of the address index — can here talk to the node (almost) directly and shrinks to an **enrichment + caching layer**: fiat rates, labels, decoded data, fan-out / rate-limit smoothing, and pagination ergonomics.

## In short

Nodes give you **point-lookups** — by hash, height, or account at a block — but not **address-indexed history or token relationships**. Those are the core relations an explorer or wallet backend must build; a UTXO node won't even give you the balance of an arbitrary address.

The exception is account-based, rich-RPC chains (Solana, XRP, Stellar): the node already serves address → history and owner → token holdings, so there the backend — usually the holder of that index — shrinks to an enrichment and caching layer. For those chains the expensive address-and-token index is **already paid for by the node**, and a heavyweight indexer adds little beyond enrichment — the opposite of the UTXO/EVM case, where it's mandatory.
