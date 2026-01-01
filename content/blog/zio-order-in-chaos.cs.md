---
date: 2023-07-13T00:00:00+01:00
title: "ZIO, řád v chaosu"
description: "Pedantický přítel, který ti pomáhá udržet pořádek"
imageFront: "images/blog/zio-order-in-chaos/zio-logo-shadow.png"
imageFrontHeight: "180"
imageHeader: "images/blog/zio-order-in-chaos/zio-header.png"
---

Zio vnímám jako implementaci obrovského množství čistě funkcionálních
paradigmat vedoucích k udržitelnosti. Vede tě k tomu, aby sis postavil
deterministický, spolehlivý a vysoce propustný systém, který má žít a růst
po mnoho let, aniž by se dostal do bodu, odkud není návratu, jak se to
obvykle stává u nečistě funkcionálních systémů, kde je vývojářům dovoleno
podvádět, aby věci fungovaly. Pod podváděním mám na mysli zejména zbožná
přání a podcenění schopnosti lidského mozku uchopit graf kauzálních vztahů
komplexního systému, což nakonec vede k nedeterminismu. Typově bezpečná a
čistě funkcionální aplikace je v zásadě kompozitní graf kauzálních efektů,
který se materializuje, když se aplikace spustí.

Udržitelnost jde ruku v ruce s disciplínou, tvrdou prací a trochou času
navíc, což je samozřejmě trade-off. Vyžaduje určité vlastnosti systému,
zvlášť když interaguje s vnějším světem nečekanými způsoby. Deterministické
chování systému a schopnost vytvářet back-pressure vůči interakcím s
vnějším světem jsou možná nejdůležitější vlastnosti, a zároveň nejtěžší
získat a udržet v čase. Blockchainový uzel obsahuje komplexitu celého
decentralizovaného systému a použít čistě funkcionální programování k jejímu
zkrocení není špatná volba. [Haskell](https://www.haskell.org/) je velmi
příjemná zkušenost s funkcionálním programováním, přesto má velmi omezené
use case kvůli nedostatku existujících nástrojů, driverů atd.
[Scala](https://www.scala-lang.org/) se [Zio](https://zio.dev) je podle mě
podobně příjemná zkušenost jako kódování v Haskellu, přičemž získáte všechny
výhody JVM; jakýkoli database driver nebo state-of-the-art tooling, který
vznikal mnoho let díky nejchytřejším lidem, můžete použít hned.

Do čistě funkcionálního světa jsem se dlouho zdráhal skočit, protože jsem
měl pocit, že jsem tlačen do přísných hranic, ztrácím svobodu kódovat, jak
chci, a prostě to dodělat. To je pravděpodobně oprávněný postoj při psaní
menších a jednodušších aplikací jako mikroservisy bez spolupráce. Ale když
jde o multithreaded aplikaci s mnoha zodpovědnostmi běžícími paralelně,
sdílením stavu a interakcí s vnějším světem, o 10 000+ LOC, stává se to
definicí chaosu, paralelou k nepořádnému pokoji teenagera, kde se cítí dobře
jen on, protože si systém vymyslel. Svoboda dělat side-effecting akce
kdykoli a kdekoli se nám zachce nemůže být udržitelná.
