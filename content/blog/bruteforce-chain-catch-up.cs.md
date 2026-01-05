---
date: 2026-01-01T00:00:00+01:00
title: "Bruteforce indexing blockchainu"
description: "Čínský způsob řešení těžkých problémů"
imageFront: "images/blog/bruteforce-chain-catch-up/bruteforce-logo.png"
imageFrontHeight: "180"
imageHeader: "images/blog/bruteforce-chain-catch-up/bruteforce-header.png"
---

Nový rok, nový blogový příspěvek! Jak se na nás Číňané pomalu tlačí, je čas
studovat jejich techniky. Obvykle najdou slabé místo a zkrotí ho hrubou
silou. Tak jaké je slabé místo většiny blockchainových peněženek nebo
explorerů? Určitě úzké hrdlo diskového IO a diametrálně odlišná velikost chainů od pár GBs
přes mnoho TBs. Jak by to řešili Čiňané? Pomocí shardingu, každý chain naindexovaný do pár hodin, né dnů :
- BCH : 1 shard
- BTC : 4 shards
- ETH : 12 shards

Koupili by pořádnou základní desku jako [ASUS Pro WS WRX90E-SAGE SE](https://smicro.cz/asus-pro-ws-wrx90e-sage-se-amd-wrx90-90mb1fw0-m0eay0)
na kterou lze připojit až ~32 NVMe Gen5 disků, hlavně přes Asus Hyper M.2 x16
Gen5 a pasivní bifurkaci (ne RAID0, protože pomáhá jen se sekvenčními
zápisy). WRX90 / Threadripper Pro:
- CPU má 128 PCIe 5.0 lanes
- NVMe drive potřebuje x4
- 32 nvmes × 4 = 128 lanes

Všechny disky by připojili pod `/mnt` od `0 - x`, například `/mnt/{0,1,2,3,4,...}/{eth,avax,btc,ada}/db_files`.
A napsali by indexer v Rustu se shardováním podle adres. Neadresní data
(hash bloků nebo tx atd.) jdou do `0` oddílu/adresáře a adresní data do
`1 - x` oddílů/adresářů. Tím se lineárně zvyšuje propustnost indexace i
dotazování, pokud máte mnoho uživatelů. Můžete také škálovat postupně:
začnete se shardováním přes všechny potenciální SSD sloty `0 - 16` jen se
`4` disky a nové disky později přimountujete do pozic `4 - 16`; stačí data
z původního mount pointu přesunout pomocí `rsync`, jinak by se skryla.

Výsledky mých testů ukazují, že skutečná propustnost indexování se s každým dalším shardem téměř zdvojnásobuje, 
ale pravděpodobně existuje rozumný limit 16 instancí Rocksdb. 
Pokud ovšem nemáte opravdu výkonný Threadripper a 128 GB+ nejrychlejší paměti ddr5 RAM.

Berte v potaz, že tohle nelze provést s enginy založenými na BTree jako je libmdbx nebo Redb, pouze LSM Tree enginy
jako Rocksdb umožňují sharding, protože těžkou práci (třídění, kompakce) provádějí vlákna na pozadí a nikoli hlavní vlákno.

Berte v potaz, že to lze provést paralelně pouze s EVM blockchainy, jedno vlákno na adresní shard.
V UTXO chainech není paralelizace snadná kvůli "prevouts resolution", jedno vlákno nemůže jednoduše číst, co jiné vlákno zapíše.
UTXO chainy je tedy lepší indexovat s Rocksdb, protože sharding stále pomáhá s tříděním a kompakcí s vlákny na pozadí,
přestože zápis probíha sekvenčně a ne paralelně. EVM chainy fungují skvěle jak s BTree enginy, tak s LSM Tree enginy,
tam uvidíte doslova lineární škálování se shardováním, pokud máte dost CPU jader a RAM.

A co replikace v případě, že SSD disk odejde? Stačí ručně `rsync` danou partition z funkčního serveru indexovaného na stejné výšce, 
např. volání rest-api `/maintenance/pause/at/{height}` => rsync partition => `/maintenance/resume/at/{height}`.
Takže minimálně mít 2 servery, jinak se po selhání disku nelze zotavit.

A co atomicita?
- Definitivně SIGTERM přtelská
- výpadky jsou řešeny ověřením posledních blocků při startu a validací, že zůstatky adres odpovídají historii, pokud ne, reindexací posledních N blocků

Tohle přijde v přepisu [redbit](https://github.com/pragmaxim-com/redbit), kde
jsem aktuálně na starém PCI gen 3 serveru za méně než 24 hodin zindexoval celý
Ethereum včetně všech tokenů se 4 shardy/SSD. Jinak by to trvalo 4 dny.
Dotazy na nejžhavější adresy jsou pod 1 ms, protože zůstatky jsou
předagregované a historie transakcí stránkovaná.
