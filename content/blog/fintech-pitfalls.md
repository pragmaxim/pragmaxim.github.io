---
date: 2023-06-03T00:00:00+01:00
title: "Fintech Pitfalls"
description: "Reverse-engineering the money wheel"
imageFront: "images/blog/fintech-pitfalls/money-wheel-shadow.png"
imageFrontHeight: "200"
imageHeader: "images/blog/fintech-pitfalls/bank.png"
---

[Notes to my presentation](https://prezi.com/view/nPM9GQAVOodaZSFxKY9g/)

Any system that handles people's money has certain similarities that have materialized over time at least into : 
  - Ledger of Transactions submitted to the system in order to reallocate assets between entities, 
regardless of what assets and entities mean.
  - Reaching consensus on the state of the system (Account Balances) in order to settle transactions
  - Necessity of querying Account balances (in real-time) of possibly billions of entities who have made thousands of transactions
  - Having insights of what is happening (derived data views / Projections), often on hourly, daily, monthly, yearly basis
  - Sometimes tracking funds, etc. 

Complexity of effects that one Visa payment triggers in the banking system is mind-blowing and thus even finality of settling 
such transaction (reaching consensus in all involved systems) might take up to 3 days in international transfers.
That's why the payment Fee is usually ~ 2% on account of the merchant which is leading to more expensive goods.

This is the reason why banking system is moving to blockchain technology, slowly replacing the prehistoric systems running on mainframes.
New blockchain-enabled payment processors won't issue transaction to the old systems anymore when you buy groceries, it will be settled on blockchain,
the same way as electric cars will eventually replace cars with combustion engines.

Now, how to tame complexity of processing 1M txs/s while maintaining Account Balances consistent with Transaction log across all parties involved
and having some analytical insights? How to reach consensus fast and reduce finality to fraction of a second? Considering the fact that even if we design
a system to be both fast and fully ACID as with Event-Sourcing / CQRS where :
 - millions of actors are distributed in a cluster consuming transaction log, each maintaining its account state in memory
 - projections are made so we can answer queries from UI and provide some insights

```
                          ________________
                         |   Projections  |                              _______________
Insert Tx from UI -->  rest              rest --> Query Projections --> |               |
                         |  AccountState  |                             | UI & Insights |
Imports           --> queue              rest --> Query State       --> |_______________|
                         |_TransactionLog_|
```

It is still a centralized solution living in a single cluster. Most of the time we still interact with the outside world (eg. other banks, partners) so the
software needs to reach consensus for the settlement to happen. At this point it is clear that centralization does not make sense anymore, as new entities need
to join the system. Costs and time for settling one transaction increases exponentially as reaching consensus is a n^2 problem, so on blockchain network :
 - decentralized settlement of transactions allows new parties to join the system without too high overhead and costs
 - cryptographical proofs allow for safety, consistency, fast consensus and finality 
 - each node keeps a replica of transaction ledger with a persistent version of state of all accounts (ideally in merkle tree database)
 - projections must be done externally by subscribing and querying blockchain Node

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

This decentralized solution eventually replaces the current cooperation of Visa/Mastercard/Amex/Paypal/Stripe and Banks as we know it.
As all the parties involved would just focus on making Projections and data views that are important only for them, while blockchain being shared by all.
It will replace even non-financial day-to-day services and reduce the need for middlemen and manual, repetitive labor: smart-contracts for paper contracts.

There are many very tough challenges regardless of using blockchain or not, especially related to data persistence due to unbalanced data distribution,
so making ledger projections is hard. Can we persist transactions of Sharks and Whales the same way as transactions of small fish?
  - yes, but probably not to relational database where indexing is super-slow and some queries with JOIN take 10ms and some 10s
    - this eventually leads huge, sharded db clusters and to enforcing pagination until someone forgets and brings down the whole system
  - we probably need some KV store like Cassandra and use well-designed partitions
    - Whales usually don't fit into partitions so using hash/time/range based sub-partitioning is necessary, but indexing is very fast

Nonetheless, I am strongly convinced that unless Banks won't switch to blockchain technology, the increasing costs of maintaining the old systems will eventually
lead to their bankruptcy, the same way as : 
  - Kodak after digital cameras were invented
  - Nokia after smartphones were invented

as people can already make financial transaction for $0.01 Fee that is settled under one second.
