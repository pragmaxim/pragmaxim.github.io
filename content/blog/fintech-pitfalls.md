---
date: 2023-06-04T00:00:00+01:00
title: "Fintech Pitfalls"
description: "Reverse-engineering the money wheel"
imageFront: "images/blog/fintech-pitfalls/money-wheel-shadow.png"
imageFrontHeight: "200"
imageHeader: "images/blog/fintech-pitfalls/bank.png"
---

[Notes to my presentation](https://prezi.com/view/nPM9GQAVOodaZSFxKY9g/)

Any system that handles people's money has certain similarities that have materialized over time
at least into : 
  - Ledger of Transactions submitted to the system in order to reallocate assets between entities, 
regardless of what assets and entities mean.
  - Necessity of querying Account balances (in real-time) of possibly millions of entities who have made thousands of transactions 
  - Having insights of what is happening on hourly, daily, monthly, yearly basis
  - Sometimes tracking funds, etc. 

Now, how to tame complexity of performing a billion calculations fast while maintaining Account Balances consistent with Transactions
and allow for providing insights?

Considering the fact that even if we design a system to be both fast and fully ACID, like :
  - event-sourcing / CQRS (Distributed)
     - millions of actors are distributed in a cluster consuming transaction log, each maintaining its account state in memory
     - projections are made so we can answer queries from UI and provide some insights
     - very long research and development to make bullet-proof Tx processing system
```
                          ________________
                         |   Projections  |                              _______________
Insert Tx from UI -->  rest              rest --> Query Projections --> |               |
                         |  AccountState  |                             | UI & Insights |
Imports           --> queue              rest --> Query State       --> |_______________|
                         |_TransactionLog_|
```
We still do not have any guarantee that account balances are valid unless we have a cryptographical proof of that :
  - blockchains (Decentralized)
     - each node keeps a replica of transaction ledger with a persistent version of state of all accounts
     - [Substrate](https://substrate.io) is probably the best, customizable, out of the box blockchain framework if you know Rust
       - if we plugin a custom Transaction that suits our needs, we do not even need to use smart-contracts
     - harder to make projections, must be done externally
```
                          ________________
                         |                |                       ____
Insert Tx from UI -->  rest             rest --> Query Txs   --> |    |
                         |  AccountState  |                      | UI |
Imports           --> queue             rest --> Query State --> |____|
                         |___Blockchain___|
                                 |
                       Subscribe | Rollup/Merge
                           ______v_______
                          |              |
                          |  Projections |  
                          |______________|
```
And how do we actually deal with unbalanced data distribution? Can we persist transactions of Sharks and Whales the same way
as transactions of small fish?
  - yes, but probably not to relational database, so that some queries with JOIN take 10ms and some 10s and indexing is super-slow
    - this eventually leads to enforcing pagination until someone forgets and brings down the whole system
  - we probably need some KV store like Cassandra and use well-designed partitions
    - Whales usually don't fit into partitions so using hash/time/range based sub-partitioning is necessary

These are so far the most sophisticated ways of maintaining consistency between transaction log and account balances
while persisting data in a way that allows for real-time queries.
