---
date: 2026-01-03T00:00:00+01:00
title: "Blockchain API"
description: "Explorers, wallets, you name it"
imageFront: "images/blog/blockchain-api/blockchain-logo.png"
imageFrontHeight: "180"
imageHeader: "images/blog/blockchain-api/blockchain-header.jpg"
---

When you design a new blockchain explorer, commercial API or wallet backend, you should start with asking 2 questions : 

### What nodes can answer (high level) via standard JSON-RPC

UTXO chains (Bitcoin-like) :
- Blocks and transactions by hash/height.
- Mempool contents and individual outpoint state (spent/unspent) by txid+vout.
- Fee estimates and chain state.

EVM chains (Ethereum-like) :
- Point-in-time account state: balance, nonce, contract storage, code.
- Transactions and receipts by tx hash.
- Blocks by number, with full tx list if requested.
- Logs by filter over a block range (nodes typically index logs, but queries are range-based).

### What nodes cannot answer via standard JSON-RPC

UTXO chains :
- All transactions for a given address or xpub without scanning all blocks.
- Current balance for an arbitrary address without scanning all its txs/UTXOs.
- Address-level history, paging, or balance history over time.

EVM chains :
- Address-indexed transaction history (not available in standard JSON-RPC).
- Token lists and balances for an address without scanning logs or traces.
- Internal transactions for an address without tracing each block/tx.
- Address-level history paging or balance history over time.

Then you design indexing scheme with the bare minimum to be able to serve address balance or tx history queries efficiently :

### UTXO chains — missing relations

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

### EVM chains — missing relations

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

In short: nodes give you **point‑lookups** (by hash/height/account at a block), but they don’t give you **address‑indexed history, or token relationships**. 
Those are the core relations an explorer/wallet backend must build. Utxo node does not even give you balance of an arbitrary address.
