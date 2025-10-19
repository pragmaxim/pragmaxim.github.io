---
date: 2025-10-18T00:00:00+01:00
title: "RUST, with discipline to high performance"
description: "Complex systems with low memory footprint"
imageFront: "images/blog/rust-with-discipline-to-high-performance/rust-logo.png"
imageFrontHeight: "180"
imageHeader: "images/blog/rust-with-discipline-to-high-performance/rust-header.png"
---

I slowly shifted from using Scala to Rust because complex systems on JVM have quite high memory footprint. Experienced developer is constantly 
differentiating between hot spots and cold spots of the application as the consequences of abusing the Heap and GC are obvious. JVM languages let you 
clone an object graph in a hot spot just like that. In Rust, you have to make an effort to slow everything down, so if you are mindful, wondering and
disciplined, you can build software with throughput and memory footprint incomparable to JVM based systems. One wants the disk or network IO 
to be the bottleneck and to worry only about exhausting available RAM. JVM apps consume much more RAM and less is left for Kernel's page cache. 
This is a primary reason why Rust was adopted as a language of choice for building blockchains because decentralized systems are not forgiving when 
it comes to performance, there is no easy horizontal scaling by adding more nodes to the cluster and decentralized sharding is possible but complex.

When you come from JVM to Rust and you see that a complex system consumes 1GB of RAM in total which is almost exactly the size of your cache + data batch
that is kept in memory for sorting purposes, your mind is blown away. You would need 3GBs of RAM on JVM for the same application. Now imagine you are
parallelizing the data processing on 16 cores and the differences become much more significant, suddenly we need a cluster or start specializing the code.   

Scala/Java fight boxing & erasure by adding specialization or primitive APIs to avoid it. Rust’s generics are monomorphized by default, so primitives are 
not boxed and you get zero-cost, inlineable code. There is definitely a trade-off, you need to give up some degree of freedom at generic programming, for 
example passing a generic instance to a function without knowing its concrete type in compile time is not possible in Rust. This is quite a limitation 
after coming from wonderful world of functional type system of Scala where the design for your actual problem can be very elegant and readable. In Rust, 
it either becomes an ugly hack or you need to put in extra work to design it differently, that is simply the price for high performance with low memory footprint.

That is to say, I love both worlds and I would ideally combine them, using Scala for cold spots and Rust for hot spots of the application. 
However that is not possible, unfortunately.