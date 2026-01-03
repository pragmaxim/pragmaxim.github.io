---
date: 2025-10-18T00:00:00+01:00
title: "RUST, s disciplínou k vysokému výkonu"
description: "Komplexní systémy s nízkou paměťovou stopou"
imageFront: "images/blog/rust-with-discipline-to-high-performance/rust-logo.png"
imageFrontHeight: "180"
imageHeader: "images/blog/rust-with-discipline-to-high-performance/rust-header.png"
---

Postupně jsem přešel ze Scaly na Rust, protože komplexní systémy na JVM mají
poměrně vysokou paměťovou stopu. Zkušený vývojář neustále rozlišuje mezi hot
spoty a cold spoty aplikace, protože následky zneužívání heapu a GC jsou
zřejmé. JVM jazyky vám dovolí klonovat objektový graf v hot spotu jen tak.
V Rustu musíte vynaložit úsilí, abyste všechno zpomalili, takže když jste
všímaví, zvídaví a disciplinovaní, můžete stavět software s propustností a
paměťovou stopou nesrovnatelnou se systémy na JVM. Člověk chce, aby úzkým
hrdlem bylo diskové nebo síťové IO a aby ho trápilo jen vyčerpání dostupné
RAM. JVM aplikace spotřebují mnohem více RAM a pro page cache jádra zůstane
méně. To je hlavní důvod, proč byl Rust přijat jako jazyk volby pro tvorbu
blockchainů, protože decentralizované systémy neodpouštějí, pokud jde o
výkon, neexistuje snadné horizontální škálování přidáním dalších uzlů do
clusteru a decentralizované shardování je možné, ale složité.

Když přijdete z JVM do Rustu a zjistíte, že komplexní systém spotřebuje
celkem 1 GB RAM, což je téměř přesně velikost vaší cache + datové dávky
udržované v paměti pro účely třídění, vyrazí vám to dech. Na JVM byste pro
stejnou aplikaci potřebovali 3 GB RAM. A teď si představte, že paralelizujete
zpracování dat na 16 jádrech a rozdíly jsou mnohem výraznější; najednou
potřebujeme cluster nebo začít se specializací kódu.

Scala/Java bojují s boxingem a erasure přidáváním specializace nebo
primitivních API, aby se tomu vyhnuly. Generika v Rustu jsou ve výchozím
stavu monomorfizovaná, takže primitiva nejsou boxovaná a dostanete
zero-cost, inlinovatelný kód. Je v tom samozřejmě trade-off, musíte se
vzdát určité míry svobody v generickém programování, například předat
generickou instanci do funkce bez znalosti jejího konkrétního typu v čase
překladu v Rustu nejde. To je docela omezení po příchodu z nádherného světa
funkcionálního typového systému ve Scale, kde může být návrh vašeho reálného
problému velmi elegantní a čitelný. V Rustu se to buď stane ošklivým hackem,
nebo musíte vynaložit extra práci a navrhnout to jinak, což je prostě cena
za vysoký výkon s nízkou paměťovou stopou.

Pěkným příkladem tragédie v Rustu je už jen fakt, že i přítomnost
asociovaného typu (ne generického typu) jako Settings :
```rust
pub trait Store {
    type Settings; // associated type
    type WriteTxn<'a>: WriteTransaction + 'a // generic associated type (GAT)
    where
        Self: 'a;
}
```

vám zabrání udělat `Box<dyn UStore>` a už nemůžete postavit Service s
libovolným Store. Musí to být známo v době překladu. Pravidlo palce v Rustu
je používat asociované typy nebo GATy jen tehdy, když je opravdu potřebujete.

Na druhou stranu je komunita stojící za Rustem neuvěřitelně silná. Obzvláště ve vývoji blockchainu, kde například
tento ekosystém nástrojů pro EVM řetězce [alloy-rs](https://github.com/alloy-rs) vám dává neuvěřitelné schopnosti, rozhodně ne
srovnatelné s jinými jazyky.

Tím chci říct, že miluju oba světy a ideálně bych je kombinoval: Scalu pro
cold spoty a Rust pro hot spoty aplikace. I když to v blockchain vývoji
nejde, v mikroservisní architektuře to možné je.
