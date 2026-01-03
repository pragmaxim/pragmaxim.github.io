---
date: 2026-01-01T00:00:00+01:00
title: "Bruteforce Chain Catch-Up"
description: "Chinese way of solving hard problems"
imageFront: "images/blog/bruteforce-chain-catch-up/bruteforce-logo.png"
imageFrontHeight: "180"
imageHeader: "images/blog/bruteforce-chain-catch-up/bruteforce-header.png"
---

New year, new blog post! As the Chinese are slowly coming for us, it is time to study their techniques.
They usually identify a weak spot and use brute-force to tame it. So, what is the weak spot of most blockchain
wallets or explorers? It is definitely disk IO bottleneck, so how would Chinese solve it? 

They would buy a solid board like [ASUS Pro WS WRX90E-SAGE SE](https://smicro.cz/asus-pro-ws-wrx90e-sage-se-amd-wrx90-90mb1fw0-m0eay0)
where you can attach up to ~ 32 NVMe gen 5 drives mostly through Asus Hyper M.2 x16 Gen 5 and passive bifurcation 
(not RAID0, because it only helps with sequential writes). WRX90 + Threadripper Pro:
- CPU provides 128 PCIe 5.0 lanes 
- An NVMe drive needs x4
- 32 drives × 4 = 128 lanes

They would mount all drives under `/mnt` from `0 - x` like `/mnt/{0,1,2,3,4,...}/{eth,avax,btc,ada}/db_files`.
And they would write an indexer in Rust with sharding by address. Non-address data (block or tx hashes, etc.) go to `0` 
partition/dir and address data go to `1 - x` partitions/dirs. This linearly increases both indexing throughput and 
also querying throughput if you have many users. You can also scale-up as you go, you simply start with sharding over all 
potential ssd slots `0 - 16` with only `4` drives and mount new drives to `4 - 16` places later, you just need to `rsync`
the data from the mount point as it would get hidden.

My testing results show that real indexing throughput is almost doubling with each additional shard but there
is probably a reasonable limit of 16 Rocksdb instances. Unless you have a really powerful Threadripper and 128GB+ of the fastest ddr5 RAM.

Note that this can be done with EVM block chains in parallel, one writer thread per address shard.
In UTXO chains, parallelization is not easy due to prevouts resolution, crossing async boundary is not feasible.
So UTXO chains are better off with Rocksdb because it is doing sorting and compaction work with background threads and
sharding still helps, eventhough executed serially. EVM chains work great both with BTree engines and LSM Tree engines
and that's where you see literally linear scaling with sharding if you have enough CPU cores and RAM.

What about replication in case an ssd dies. We simply need to manually rsync that partition from a healthy server indexed at the same
height, eg. rest-api call to endpoint `/maintenance/pause/at/{height}` => rsync partition => `/maintenance/resume/at/{height}`.
So 2 servers are minimum, otherwise you cannot recover from a disk failure.

This is what's coming in the rewrite of [redbit](https://github.com/pragmaxim-com/redbit), where I currently indexed whole
Ethereum including all tokens on my old PCI gen 3 server under 24 hours with 4 shards/ssds. Otherwise it would take 4 days.
Querying times for the hottest addresses under 1ms because balances are pre-aggregated and transaction history paginated.