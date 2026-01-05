---
date: 2026-01-01T00:00:00+01:00
title: "Bruteforce Chain Catch-Up"
description: "Chinese way of solving hard problems"
imageFront: "images/blog/bruteforce-chain-catch-up/bruteforce-logo.png"
imageFrontHeight: "180"
imageHeader: "images/blog/bruteforce-chain-catch-up/bruteforce-header.png"
---

New year, new blog post! The Chinese are known for large scale operations, let's study their techniques.
They usually identify a weak spot and use brute-force and resources to solve it. I am not saying it's lovely but
it is efficient. So, what is the weak spot of most blockchain wallets or explorers? It is definitely disk IO bottleneck. 
And what is the brute-force and resources necessary to solve it? Effiecient storage. Chain sizes vary from tens of GBs up to many TBs. 
In my opition, the solution is sharding by `(address,asset_id)`, such that each chain is indexed in hours, not days. 
This way the explorers and wallets can evolve without suffering from binary lock-in and inability to reindex chains quickly. 
Chains evolve, explorers and wallets need to evolve too, it is a marathon :
- BCH : 1 shard
- BTC : 4 shards
- ETH : 12 shards

They would buy a solid board like [ASUS Pro WS WRX90E-SAGE SE](https://smicro.cz/asus-pro-ws-wrx90e-sage-se-amd-wrx90-90mb1fw0-m0eay0)
where you can attach up to ~ 32 NVMe gen 5 drives mostly through Asus Hyper M.2 x16 Gen 5 and passive bifurcation 
(not RAID0, because it only helps with sequential writes). WRX90 + Threadripper Pro :
- CPU provides 128 PCIe 5.0 lanes 
- An NVMe drive needs x4
- 32 drives × 4 = 128 lanes

They would mount all drives under `/mnt` from `0 - x` like `/mnt/{g,0,1,2,3,4,...}/{eth,avax,btc,ada}/db_files`.
And they would write an indexer in Rust with sharding by address. Non-address data (block or tx hashes, etc.) go to `g` as global
partition/dir and address data go to `0 - x` partitions/dirs. This at least sub-linearly ~ `y = 0.6x` increases both indexing throughput and 
also querying throughput if you have many users. You can also scale-up as you go, you simply start with sharding over all 
potential ssd slots `0 - 16` with only `4` drives and mount new drives to `4 - 16` places later, you just need to `rsync`
the data from the mount point as it would get hidden.

My testing results show that real indexing throughput is almost doubling with each additional shard but there
is probably a reasonable limit of 16 Rocksdb instances. Unless you have a really powerful Threadripper and 128GB+ of the fastest ddr5 RAM.

Note that this can be done with EVM block chains in parallel, one writer thread per `(address, asset_id)` shard.
In UTXO chains, parallelization is not easy due to prevouts resolution, crossing async boundary is not feasible.
So UTXO chains are better off with Rocksdb because it is doing sorting and compaction work with background threads and
sharding still helps, eventhough executed serially. EVM chains work great both with BTree engines and LSM Tree engines
and that's where you see sub-linear ~ `y = 0.6x` scaling with sharding if you have enough CPU cores and RAM.

What about replication in case an ssd dies? 2 servers are minimum, otherwise you cannot recover from a disk failure.
We simply need to manually rsync that partition from a healthy server indexed at the same height, eg. rest-api calls pause/resume endpoints :  
- `/maintenance/pause/at/{height}`
- rsync partition 
- `/maintenance/resume/at/{height}`

What about atomicity? 
- Definitely SIGTERM friendly, it is quote trivial to make atomicity guarantees besides hardware crashes or power outages
- crash/outage is solved by checking last blocks on startup and validating that address balances matches the history, if not, reindex last N blocks
- comparing address tx history with balances in last hundreds of blocks on startup reveals any corruption or inconsistency,
  if balances of almost 1M of arbitrary addresses are correct, we may assume the rest is correct too.

What about address distribution, locality, hotspots, parallel write skew?
- skew is mitigated by not sharding by `address` only, but by `(address, asset_id)` with fan‑out merge at query time
- the more shards the better because it reduces the chances of multiple hot addresses or assets colliding in the same shard
  that's why we see sub-linear scaling with more shards `y = 0.6x`
- occasionally there are batches with insane amount of token transfers of the same `(address, asset_id)` and that shard is overloaded, 
  that imho cannot be solved and that makes it only sub-linear instead of linear scaling, because that overloaded shard worker  
  is running on average 40% longer than others, however we don't have to be worried too much about cooling down the hardware
- source of the skew : stable coins (issuer/treasury addresses), airdrops, CEX hot wallets, AMM pools, bridge/gateway contracts, mining pools

Bottom line, eventhough some people reject sharding for blockchains due to specific address distribution problems, I believe that
if you put one ssd under 100% load for a week, it will probably die very soon and you will just cause new problems,
whereas putting 16 ssds under 40% load for a day of indexing does not really make any harm to them, especially when even user queries
are distributed over all ssds.

With that being said, I am quite sure that I am reinventing distributed databases here and next steps would be rebalancing and what not,
however my philosophy is simply to pick the minimal and right principles for taming extreme complexity of allowing many users to 
query even arbitrary mining pool, dex or exchange addresses with millions of value transfers in real-time. 

This is what's coming in the rewrite of [redbit](https://github.com/pragmaxim-com/redbit), where I currently indexed whole
Ethereum including all tokens on my old PCI gen 3 server under 24 hours with 8 shards/ssds. Otherwise it would take 4 days.
Querying times for the hottest addresses under 1ms because balances are pre-aggregated and transaction history paginated.
I could basically reuse 7 years old sloppy server and compete with new one for $10k. 