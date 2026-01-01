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
where you can attach up to ~ 34 NVMe gen 5 drives mostly through Asus Hyper M.2 x16 Gen 5 and passive bifurcation 
(not RAID0, because it only helps with sequential writes).

They would mount all drives under `/mnt` from `0 - x` like `/mnt/{0,1,2,3,4,...}/{eth,avax,btc,ada}/db_files`.

And they would write an indexer in Rust with sharding by address. Non-address data (block or tx hashes, etc.) go to `0` 
partition/dir and address data go to `1 - x` partitions/dirs. This linearly increases both indexing throughput and 
also querying throughput if you have many users. You can also scale-up as you go, you simply start with sharding over all 
potential ssd slots `0 - 30` with only `4` drives and mount new drives to `4 - 30` places later, you just need to `rsync`
the data from the mount point as it would get hidden.

This is what's coming in the rewrite of [redbit](https://github.com/pragmaxim-com/redbit), where I currently indexed whole
Ethereum including all tokens on my old PCI gen 3 server under 24 hours with 4 shards/ssds. Otherwise it would take 4 days.
Querying times for the hottest addresses under 1ms because balances are pre-aggregated and transaction history paginated.