---
date: 2023-06-03T00:00:00+01:00
title: "The Hitchhiker's Guide to Fintech"
description: "Reverse-engineering the money wheel"
imageFront: "images/blog/fintech-pitfalls/money-wheel-shadow.png"
imageFrontHeight: "200"
imageHeader: "images/blog/fintech-pitfalls/bank.png"
---

[Notes to my presentation](https://prezi.com/view/nPM9GQAVOodaZSFxKY9g/)

Banks has always been major influential drivers of the economy, depending on the level of regulation :
  - after World War II : 3 decades of strong regulation, fixed exchange and interest rates worldwide
      - provided some financial stability
  - 1970s - 2008 : deregulation probably boosted the massive techno-feudalism as we know it today
      - 1970s : Nixon shock, end of Bretton Woods system, floating exchange rates
      - 1980s : rise of derivatives, junk bonds, etc.
      - 1990s : rise of securitization, subprime mortgages, etc.
  - 2008+ : cooperation with governments to prevent another financial crisis
      - printing money out of thin air
          - increasing debts on account of future generations 
      - more space for speculations
          - amount of financial transactions is increasing exponentially especially since Web2.0 era and the rise of e-commerce

As a result, banking systems became unsustainable both economically (inflation, manipulations) and technologically (mainframes, queues, batch processing, consensus, etc.).
Bright minds like Satoshi Nakamoto have been trying to tackle these problems which is basically how blockchain technology was born.
It was the only idea that was built from the ground up instead of being a patch on top of the old system.

Complexity of effects that one Visa payment triggers in the banking system is mind-blowing and thus :
  - finality of settling such transaction (reaching consensus in all involved systems) might take up to 3 days in international transfers
  - the payment Fee is usually ~ 2% on account of the merchant which is leading to more expensive goods

New blockchain-enabled payment processors and gateways won't issue transaction to the old systems anymore when you make a payment,
it will be settled on blockchain, the same way as electric cars will eventually replace cars with combustion engines, as a consequence :
  - finality drops to a matter of seconds
  - fee drops to just fraction of a dollar

Any system that handles people's money has certain similarities that have materialized over time at least into : 
  - Ledger of Transactions submitted to the system in order to reallocate assets between entities, regardless of what assets and entities mean
  - Reaching consensus on the state of the system (Account Balances) in order to settle transactions
  - Necessity of querying Account balances (in real-time) of possibly billions of entities who have made thousands of transactions
  - Having insights of what is happening (derived data views / Projections), often on hourly, daily, monthly, yearly basis
  - Sometimes tracking funds, etc. 

Now, how to tame complexity of processing 1M txs/s while maintaining Account Balances consistent with Transaction log across all parties involved
and having some analytical insights? How to reach consensus fast and reduce finality to a second? 
  - without blockchain technology, this can currently be done only on a single cluster of machines with Event-Sourcing / CQRS where : 
      - millions of actors are distributed in a cluster consuming transaction log, each maintaining its account state in memory
      - projections are made so we can answer queries from UI and provide some insights

```
                            C L U S T E R
                          ________________
                         |   Projections  |                              _______________
Insert Tx from UI -->  rest              rest --> Query Projections --> |               |
                         |  AccountState  |                             | UI & Insights |
Imports           --> queue              rest --> Query State       --> |_______________|
                         |_TransactionLog_|
```

But it is still a centralized solution living in a single cluster. Most of the time we still interact with the outside world (eg. other banks, partners) so the
software needs to reach consensus for the settlement to happen. At this point it is clear that centralization does not make sense anymore, as new entities need
to join the system. Costs and time for settling one transaction increases exponentially as reaching consensus is a n^2 problem, so on blockchain network :
 - decentralized settlement of transactions allows new parties to join the system without too high overhead and costs
 - cryptographical proofs allow for safety, consistency, fast consensus and finality 
 - each node keeps a replica of transaction ledger with a persistent version of state of all accounts (ideally in merkle tree database)
 - projections must be done externally by subscribing and querying blockchain Node

```
                       NODE in a p2p Network  
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

Nonetheless, I am strongly convinced that unless Banks won't switch to blockchain technology, the increasing costs of maintaining the old systems will eventually
lead to their bankruptcy, the same way as : 
  - Kodak after digital cameras were invented
  - Nokia after smartphones were invented

Now, we live in a competitive environment, so what blockchain and what currency will be used? Probably the blockchain that allows for fastest consensus, finality and
overall throughput while maintaining small transaction fees, blockchain that is able to persist petabytes of data and live for decades without any serious downtime.
There will be probably many currencies used, as blockchains can be bridged, but mostly likely stablecoins pegged to National currency will be most useful.
Defi (Decentralized Finance) already replicated many of the financial services that traditional Bank provide. 

There are still a lot of very tough challenges regardless of using blockchain or not, especially related to data persistence due to data quantity and unbalanced distribution,
so persisting terabytes of ledger data and booting fresh node with it fast will always be a challenge, also making its blockchain data projections is hard. For example :
  - can we make projections of transactions made by Sharks and Whales the same way as transactions of small fish?
      - yes, but probably not to relational database where indexing is super-slow and some queries with JOIN take 10ms and some 10s
          - this eventually leads huge, sharded db clusters and to enforcing pagination until someone forgets and brings down the whole system
      - we probably need some KV store like Cassandra and use well-designed partitions
          - whales usually don't fit into partitions so using hash/time/range based sub-partitioning is necessary, but indexing is very fast
