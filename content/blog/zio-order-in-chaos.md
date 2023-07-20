---
date: 2023-07-13T00:00:00+01:00
title: "ZIO, order in chaos"
description: "Pedantic friend that helps you keep your workplace tidy"
imageFront: "images/blog/zio-order-in-chaos/zio-logo-shadow.png"
imageFrontHeight: "180"
imageHeader: "images/blog/zio-order-in-chaos/zio-header.png"
---

I perceive Zio as an implementation of vast amount of purely functional paradigms leading to sustainability. 
It guides you to build a deterministic, reliable and high-throughput system that is supposed to live and grow for many
years without getting into a point of no return as it usually happens with non-purely functional systems where developers
are allowed to cheat to get stuff done. By cheating I mean especially wishful thinking and underestimation of human brain
to grasp causal effect graph of a complex system that eventually leads to lack of determinism. Type-safe and purely
functional application is basically a composable graph of causal effects that is materialized when the app is executed.

Sustainability goes hand in hand with discipline, hard work and some extra time which is certainly a trade-off. 
It demands certain properties of a system, especially when it interacts with outside world in unexpected ways. 
Deterministic behavior of the system and the ability to back-pressure interactions with the outside world are perhaps
the most important properties, yet the hardest to acquire and maintain in time. A blockchain Node contains complexity of the
whole decentralized system and using pure functional programming to tame the complexity is not a bad choice.
[Haskell](https://www.haskell.org/) is a very pleasant experience of functional programming, yet it has very limited
use case due to lack of existing tooling, drivers, etc. [Scala](https://www.scala-lang.org/) with [Zio](https://zio.dev)
is in my eyes a similarly pleasant experience like coding in Haskell however you get all the benefits of JVM, any database
driver or state-of-the-art tooling that has been developed for many years by the smartest people can be used right away. 

I've been reluctant to jump into the purely functional world for quite a while as I felt I'm being forced into
strict boundaries, loosing freedom of coding however I like and get stuff done. That is probably valid attitude when
coding smaller and simpler applications like microservices without any collaboration. But when it comes to multi-threaded
application with many responsibilities done in parallel, sharing state and interacting with outside world, having 10 000+ LOC,
it becomes a definition of chaos, a parallel to messy room of a teenager where only the teenager feels good at as he/she engineered
the system. Freedom of making a side-effecting action anywhere and anytime we feel like it cannot be sustainable.
