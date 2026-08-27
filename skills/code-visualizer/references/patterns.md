# Pattern catalog

For each pattern: the roles to use in `participants`, the signals that justify
naming it, and the look-alike it gets confused with. Naming a pattern is a claim
about intent, so the signal column is the bar - if you cannot point at it in the
diff, drop the claim or mark it `low`.

Contents: [Creational](#creational) · [Structural](#structural) ·
[Behavioural](#behavioural) · [Architectural](#architectural) ·
[Frontend](#frontend) · [Concurrency and resilience](#concurrency-and-resilience) ·
[Violations worth naming](#violations-worth-naming)

## Creational

**Factory Method** — roles: Creator, Product.
Signal: one function or method returns different concrete types behind a common
type, chosen from an argument. Look-alike: a constructor wrapper that always
returns the same type is not a factory, it is a helper.

**Abstract Factory** — roles: AbstractFactory, ConcreteFactory, Product.
Signal: a family of related products created together so they stay consistent
(same driver, same tenant, same environment). Look-alike: a single Factory
Method with a switch.

**Builder** — roles: Builder, Product, Director.
Signal: stepwise construction with chained calls and a terminal `build()`.
Look-alike: a fluent query interface that executes rather than builds.

**Singleton** — roles: Singleton.
Signal: one instance enforced in code - private constructor, module-level
instance, `getInstance()`. Look-alike: a DI container registering a singleton
scope; that is the container's lifecycle, not the pattern, and it is worth
saying so in `note`.

**Prototype** — roles: Prototype, Clone.
Signal: new objects made by cloning an existing one, `clone()` / `structuredClone`
/ spread of a template object.

**Dependency Injection** — roles: Injector, Client, Service.
Signal: collaborators arrive through the constructor or parameters rather than
being constructed inside. This is the most common real pattern in a diff; only
name it when the change introduces or removes the injection, not for every class
that happens to have a constructor.

## Structural

**Adapter** — roles: Target, Adaptee, Adapter.
Signal: a thin class or function whose only job is translating one interface into
another the caller already expects. Look-alike: a Facade, which simplifies rather
than translates.

**Facade** — roles: Facade, Subsystem.
Signal: one entry point hiding several collaborators, so callers stop knowing the
subsystem. Look-alike: a god object - if it also holds business rules, name that
instead.

**Decorator** — roles: Component, ConcreteComponent, Decorator.
Signal: same interface in and out, behaviour added around a delegated call -
caching, logging, retry, auth wrappers.

**Proxy** — roles: Subject, Proxy.
Signal: same interface, controls access or defers work - lazy loading, remote
call, permission gate.

**Composite** — roles: Component, Leaf, Composite.
Signal: a tree where a group is treated exactly like a single item.

**Bridge** — roles: Abstraction, Implementor.
Signal: two hierarchies varying independently, abstraction holds a reference to
an implementor.

**Repository** — roles: Repository, Entity, DataSource.
Signal: persistence sits behind a domain-shaped interface, callers never see the
query. Look-alike: a DAO that just mirrors table CRUD; that is a thinner claim,
say so.

## Behavioural

**Strategy** — roles: Strategy, ConcreteStrategy, Context.
Signal: one interface, several interchangeable implementations, context selects
at runtime and calls through the interface. The tell that it is real: the context
has no `if` on the variant. Look-alike: State, where the object swaps its own
strategy as it changes.

**Observer / Pub-Sub** — roles: Subject, Observer.
Signal: emitter and handler are wired by event name, not by direct call -
`emit`, `@OnEvent`, `subscribe`, a queue topic.

**Command** — roles: Command, Handler, Invoker.
Signal: a request captured as an object, dispatched to a handler. In CQRS
codebases this is the everyday shape: one command class, one handler, a bus.

**Chain of Responsibility** — roles: Handler, Successor.
Signal: each link either handles or passes along - middleware, interceptors,
guards, validation pipelines.

**Template Method** — roles: AbstractClass, ConcreteClass.
Signal: a base method fixes the algorithm's order and calls abstract hooks the
subclass fills in.

**State** — roles: State, ConcreteState, Context.
Signal: behaviour changes because the object's state object changed, and the
states know the legal transitions. Look-alike: a status enum with a switch; that
is a state machine, not this pattern.

**Mediator** — roles: Mediator, Colleague.
Signal: components stop talking to each other and talk to one coordinator.

**Visitor** — roles: Visitor, Element.
Signal: an operation added over a fixed type hierarchy without touching the
types - AST walkers, serializers.

**Iterator / Generator** — roles: Iterator, Collection.
Signal: traversal separated from the collection, `yield`, async iterators,
cursor pagination.

**Memento** — roles: Originator, Memento, Caretaker.
Signal: state snapshotted so it can be restored - undo, drafts, rollback.

## Architectural

**Layered / Hexagonal (ports and adapters)** — roles: Port, Adapter, Domain.
Signal: the domain declares an interface and the infrastructure implements it, so
the dependency arrow points inwards. This one is best read off the graph: if a
domain node points at an infrastructure node, the change broke the rule.

**CQRS** — roles: Command, Query, Handler, ReadModel.
Signal: separate write and read paths with their own models. Look-alike: a
service with `get` and `save` methods.

**Event Sourcing** — roles: Event, EventStore, Projection.
Signal: state derived by replaying stored events, not by mutating a row.

**Saga / Process Manager** — roles: Saga, Step, CompensatingAction.
Signal: a multi-service flow with explicit compensation on failure.

**Outbox** — roles: Outbox, Publisher, Consumer.
Signal: an event row written in the same transaction as the state change, then
published separately. Naming it matters because it is what makes the change
crash-safe.

**Strangler Fig** — roles: LegacyPath, NewPath, Router.
Signal: a toggle or router sending some traffic to a new implementation while the
old one stays. Very common shape in a migration PR.

**Anti-Corruption Layer** — roles: Translator, ExternalModel, DomainModel.
Signal: an external payload mapped into domain types at the boundary so the
vendor's shape does not leak inwards.

## Frontend

**Container / Presentational** — roles: Container, Presentational.
Signal: one component fetches and owns state, the other only renders props.

**Custom Hook (behaviour extraction)** — roles: Hook, Consumer.
Signal: stateful logic pulled out of components into a reusable `useX`.

**Provider / Context** — roles: Provider, Consumer.
Signal: shared state passed down through context rather than props.

**Compound Component** — roles: Parent, Slot.
Signal: components meant to be composed (`Menu`, `Menu.Item`) sharing implicit
state.

**Render Prop / Headless Component** — roles: Provider, Renderer.
Signal: behaviour supplied, markup left to the caller.

**Optimistic Update** — roles: Mutation, Cache, Rollback.
Signal: local cache written before the server confirms, with a rollback path.
Worth naming because the rollback is what reviewers forget.

## Concurrency and resilience

**Circuit Breaker** — roles: Breaker, ProtectedCall.
Signal: failures counted, calls short-circuited while open, a half-open probe.

**Retry with Backoff** — roles: Retrier, Operation.
Signal: bounded attempts with a growing delay, and ideally jitter. If the retry
is unbounded or has no backoff, name it and flag it in `note`.

**Bulkhead / Rate Limiter** — roles: Limiter, Resource.
Signal: concurrency or request rate capped to protect a downstream.

**Idempotency Key** — roles: Key, Store, Operation.
Signal: a request key persisted so a replay is a no-op.

**Cache-Aside** — roles: Client, Cache, Store.
Signal: read cache, miss, read store, populate cache - plus an invalidation
path. A cache with no invalidation is a finding, not a pattern.

## Violations worth naming

Name these with the pattern's own name and explain the break in `note`. They are
often the most valuable thing on the page, because a reviewer skimming a diff
will not spot them.

- **Leaky abstraction** — the interface exists but callers reach past it, or its
  types expose the implementation (an ORM entity crossing the boundary).
- **Strategy with an `if`** — the context branches on the concrete variant, so
  adding one means editing the context.
- **God object / Single Responsibility break** — the diff adds a second unrelated
  reason for one class to change.
- **Circular dependency** — visible as a right-to-left edge in the graph.
- **Anemic domain model** — entities are data bags, all rules live in services.
  Only worth naming when the diff moves logic out of an entity that had it.
- **Feature envy / shotgun surgery** — one logical change touching many files
  because the behaviour is scattered. The file view shows this well: count the
  boxes that changed for one idea.
- **Inheritance for reuse** — a subclass created only to borrow methods, with no
  is-a relationship.
