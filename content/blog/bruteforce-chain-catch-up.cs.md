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
explorerů? Určitě úzké hrdlo diskového IO, tak jak by to Číňané řešili?

Koupili by pořádnou základní desku jako
[ASUS Pro WS WRX90E-SAGE SE](https://smicro.cz/asus-pro-ws-wrx90e-sage-se-amd-wrx90-90mb1fw0-m0eay0)
na kterou lze připojit až ~34 NVMe Gen5 disků, hlavně přes Asus Hyper M.2 x16
Gen5 a pasivní bifurkaci (ne RAID0, protože pomáhá jen se sekvenčními
zápisy).

Všechny disky by připojili pod `/mnt` od `0 - x`, například
`/mnt/{0,1,2,3,4,...}/{eth,avax,btc,ada}/db_files`.

A napsali by indexer v Rustu se shardováním podle adres. Neadresní data
(hash bloků nebo tx atd.) jdou do `0` oddílu/adresáře a adresní data do
`1 - x` oddílů/adresářů. Tím se lineárně zvyšuje propustnost indexace i
dotazování, pokud máte mnoho uživatelů. Můžete také škálovat postupně:
začnete se shardováním přes všechny potenciální SSD sloty `0 - 30` jen se
`4` disky a nové disky později přimountujete do pozic `4 - 30`; stačí data
z původního mount pointu přesunout pomocí `rsync`, jinak by se skryla.

Tohle přijde v přepisu [redbit](https://github.com/pragmaxim-com/redbit), kde
jsem aktuálně na starém PCI gen 3 serveru za méně než 24 hodin zindexoval celý
Ethereum včetně všech tokenů se 4 shardy/SSD. Jinak by to trvalo 4 dny.
Dotazy na nejžhavější adresy jsou pod 1 ms, protože zůstatky jsou
předagregované a historie transakcí stránkovaná.
