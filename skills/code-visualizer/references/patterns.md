# Pattern catalog

For each pattern: the roles to use in `participants`, the signals that justify
naming it, and the look-alike it gets confused with. Naming a pattern is a claim
about intent, so the signal column is the bar - if you cannot point at it in the
diff, drop the claim or mark it `low`.

Each entry carries a Reference line. The page shows the same link under the
pattern name, but it reads it from the `REFERENCE` map in
`scripts/render_graph.py`, not from here. Change one and change the other.

The page adds a second link on top of that one, to the pattern's own page on
patterns.dev, for the entries that have one. That mapping lives in `FAMILY` in
the same script. patterns.dev covers about a dozen of these, so most entries get
one link and that is deliberate: a link to its index page helps nobody.

Contents: [Creational](#creational) · [Structural](#structural) ·
[Behavioural](#behavioural) · [Architectural](#architectural) ·
[Frontend](#frontend) · [Concurrency and resilience](#concurrency-and-resilience) ·
[Violations worth naming](#violations-worth-naming)

## Creational

**Factory Method** — roles: Creator, Product.
Reference: <https://refactoring.guru/design-patterns/factory-method>
Signal: one function or method returns different concrete types behind a common
type, chosen from an argument. Look-alike: a constructor wrapper that always
returns the same type is not a factory, it is a helper.

**Abstract Factory** — roles: AbstractFactory, ConcreteFactory, Product.
Reference: <https://refactoring.guru/design-patterns/abstract-factory>
Signal: a family of related products created together so they stay consistent
(same driver, same tenant, same environment). Look-alike: a single Factory
Method with a switch.

**Builder** — roles: Builder, Product, Director.
Reference: <https://refactoring.guru/design-patterns/builder>
Signal: stepwise construction with chained calls and a terminal `build()`.
Look-alike: a fluent query interface that executes rather than builds.

**Singleton** — roles: Singleton.
Reference: <https://refactoring.guru/design-patterns/singleton>
Signal: one instance enforced in code - private constructor, module-level
instance, `getInstance()`. Look-alike: a DI container registering a singleton
scope; that is the container's lifecycle, not the pattern, and it is worth
saying so in `note`.

**Prototype** — roles: Prototype, Clone.
Reference: <https://refactoring.guru/design-patterns/prototype>
Signal: new objects made by cloning an existing one, `clone()` / `structuredClone`
/ spread of a template object.

**Dependency Injection** — roles: Injector, Client, Service.
Reference: <https://martinfowler.com/articles/injection.html>
Signal: collaborators arrive through the constructor or parameters rather than
being constructed inside. This is the most common real pattern in a diff; only
name it when the change introduces or removes the injection, not for every class
that happens to have a constructor.

## Structural

**Adapter** — roles: Target, Adaptee, Adapter.
Reference: <https://refactoring.guru/design-patterns/adapter>
Signal: a thin class or function whose only job is translating one interface into
another the caller already expects. Look-alike: a Facade, which simplifies rather
than translates.

**Facade** — roles: Facade, Subsystem.
Reference: <https://refactoring.guru/design-patterns/facade>
Signal: one entry point hiding several collaborators, so callers stop knowing the
subsystem. Look-alike: a god object - if it also holds business rules, name that
instead.

**Decorator** — roles: Component, ConcreteComponent, Decorator.
Reference: <https://refactoring.guru/design-patterns/decorator>
Signal: same interface in and out, behaviour added around a delegated call -
caching, logging, retry, auth wrappers.

**Proxy** — roles: Subject, Proxy.
Reference: <https://refactoring.guru/design-patterns/proxy>
Signal: same interface, controls access or defers work - lazy loading, remote
call, permission gate.

**Composite** — roles: Component, Leaf, Composite.
Reference: <https://refactoring.guru/design-patterns/composite>
Signal: a tree where a group is treated exactly like a single item.

**Bridge** — roles: Abstraction, Implementor.
Reference: <https://refactoring.guru/design-patterns/bridge>
Signal: two hierarchies varying independently, abstraction holds a reference to
an implementor.

**Repository** — roles: Repository, Entity, DataSource.
Reference: <https://martinfowler.com/eaaCatalog/repository.html>
Signal: persistence sits behind a domain-shaped interface, callers never see the
query. Look-alike: a DAO that just mirrors table CRUD; that is a thinner claim,
say so.

## Behavioural

**Strategy** — roles: Strategy, ConcreteStrategy, Context.
Reference: <https://refactoring.guru/design-patterns/strategy>
Signal: one interface, several interchangeable implementations, context selects
at runtime and calls through the interface. The tell that it is real: the context
has no `if` on the variant. Look-alike: State, where the object swaps its own
strategy as it changes.

**Observer / Pub-Sub** — roles: Subject, Observer.
Reference: <https://refactoring.guru/design-patterns/observer>
Signal: emitter and handler are wired by event name, not by direct call -
`emit`, `@OnEvent`, `subscribe`, a queue topic.

**Command** — roles: Command, Handler, Invoker.
Reference: <https://refactoring.guru/design-patterns/command>
Signal: a request captured as an object, dispatched to a handler. In CQRS
codebases this is the everyday shape: one command class, one handler, a bus.

**Chain of Responsibility** — roles: Handler, Successor.
Reference: <https://refactoring.guru/design-patterns/chain-of-responsibility>
Signal: each link either handles or passes along - middleware, interceptors,
guards, validation pipelines.

**Template Method** — roles: AbstractClass, ConcreteClass.
Reference: <https://refactoring.guru/design-patterns/template-method>
Signal: a base method fixes the algorithm's order and calls abstract hooks the
subclass fills in.

**State** — roles: State, ConcreteState, Context.
Reference: <https://refactoring.guru/design-patterns/state>
Signal: behaviour changes because the object's state object changed, and the
states know the legal transitions. Look-alike: a status enum with a switch; that
is a state machine, not this pattern.

**Mediator** — roles: Mediator, Colleague.
Reference: <https://refactoring.guru/design-patterns/mediator>
Signal: components stop talking to each other and talk to one coordinator.

**Visitor** — roles: Visitor, Element.
Reference: <https://refactoring.guru/design-patterns/visitor>
Signal: an operation added over a fixed type hierarchy without touching the
types - AST walkers, serializers.

**Iterator / Generator** — roles: Iterator, Collection.
Reference: <https://refactoring.guru/design-patterns/iterator>
Signal: traversal separated from the collection, `yield`, async iterators,
cursor pagination.

**Memento** — roles: Originator, Memento, Caretaker.
Reference: <https://refactoring.guru/design-patterns/memento>
Signal: state snapshotted so it can be restored - undo, drafts, rollback.

## Architectural

**Layered / Hexagonal (ports and adapters)** — roles: Port, Adapter, Domain.
Reference: <https://alistair.cockburn.us/hexagonal-architecture/>
Signal: the domain declares an interface and the infrastructure implements it, so
the dependency arrow points inwards. This one is best read off the graph: if a
domain node points at an infrastructure node, the change broke the rule.

**CQRS** — roles: Command, Query, Handler, ReadModel.
Reference: <https://martinfowler.com/bliki/CQRS.html>
Signal: separate write and read paths with their own models. Look-alike: a
service with `get` and `save` methods.

**Event Sourcing** — roles: Event, EventStore, Projection.
Reference: <https://martinfowler.com/eaaDev/EventSourcing.html>
Signal: state derived by replaying stored events, not by mutating a row.

**Saga / Process Manager** — roles: Saga, Step, CompensatingAction.
Reference: <https://microservices.io/patterns/data/saga.html>
Signal: a multi-service flow with explicit compensation on failure.

**Outbox** — roles: Outbox, Publisher, Consumer.
Reference: <https://microservices.io/patterns/data/transactional-outbox.html>
Signal: an event row written in the same transaction as the state change, then
published separately. Naming it matters because it is what makes the change
crash-safe.

**Strangler Fig** — roles: LegacyPath, NewPath, Router.
Reference: <https://martinfowler.com/bliki/StranglerFigApplication.html>
Signal: a toggle or router sending some traffic to a new implementation while the
old one stays. Very common shape in a migration PR.

**Anti-Corruption Layer** — roles: Translator, ExternalModel, DomainModel.
Reference: <https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>
Signal: an external payload mapped into domain types at the boundary so the
vendor's shape does not leak inwards.

## Frontend

**Container / Presentational** — roles: Container, Presentational.
Reference: <https://www.patterns.dev/react/presentational-container-pattern>
Signal: one component fetches and owns state, the other only renders props.

**Custom Hook (behaviour extraction)** — roles: Hook, Consumer.
Reference: <https://react.dev/learn/reusing-logic-with-custom-hooks>
Signal: stateful logic pulled out of components into a reusable `useX`.

**Provider / Context** — roles: Provider, Consumer.
Reference: <https://react.dev/learn/passing-data-deeply-with-context>
Signal: shared state passed down through context rather than props.

**Compound Component** — roles: Parent, Slot.
Reference: <https://www.patterns.dev/react/compound-pattern>
Signal: components meant to be composed (`Menu`, `Menu.Item`) sharing implicit
state.

**Render Prop / Headless Component** — roles: Provider, Renderer.
Reference: <https://www.patterns.dev/react/render-props-pattern>
Signal: behaviour supplied, markup left to the caller.

**Optimistic Update** — roles: Mutation, Cache, Rollback.
Reference: <https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates>
Signal: local cache written before the server confirms, with a rollback path.
Worth naming because the rollback is what reviewers forget.

## Concurrency and resilience

**Circuit Breaker** — roles: Breaker, ProtectedCall.
Reference: <https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker>
Signal: failures counted, calls short-circuited while open, a half-open probe.

**Retry with Backoff** — roles: Retrier, Operation.
Reference: <https://learn.microsoft.com/en-us/azure/architecture/patterns/retry>
Signal: bounded attempts with a growing delay, and ideally jitter. If the retry
is unbounded or has no backoff, name it and flag it in `note`.

**Bulkhead / Rate Limiter** — roles: Limiter, Resource.
Reference: <https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead>
Signal: concurrency or request rate capped to protect a downstream.

**Idempotency Key** — roles: Key, Store, Operation.
Reference: <https://docs.stripe.com/api/idempotent_requests>
Signal: a request key persisted so a replay is a no-op.

**Cache-Aside** — roles: Client, Cache, Store.
Reference: <https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside>
Signal: read cache, miss, read store, populate cache - plus an invalidation
path. A cache with no invalidation is a finding, not a pattern.

## Violations worth naming

Name these with the pattern's own name and explain the break in `note`. They are
often the most valuable thing on the page, because a reviewer skimming a diff
will not spot them.

- **Leaky abstraction** — the interface exists but callers reach past it, or its
  Reference: <https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/>
  types expose the implementation (an ORM entity crossing the boundary).
- **Strategy with an `if`** — the context branches on the concrete variant, so
  Reference: <https://refactoring.guru/replace-conditional-with-polymorphism>
  adding one means editing the context.
- **God object / Single Responsibility break** — the diff adds a second unrelated
  Reference: <https://en.wikipedia.org/wiki/Single-responsibility_principle>
  reason for one class to change.
- **Circular dependency** — visible as a right-to-left edge in the graph.
  Reference: <https://en.wikipedia.org/wiki/Circular_dependency>
- **Anemic domain model** — entities are data bags, all rules live in services.
  Reference: <https://martinfowler.com/bliki/AnemicDomainModel.html>
  Only worth naming when the diff moves logic out of an entity that had it.
- **Feature envy / shotgun surgery** — one logical change touching many files
  Reference: <https://refactoring.guru/smells/feature-envy>
  because the behaviour is scattered. The file view shows this well: count the
  boxes that changed for one idea.
- **Inheritance for reuse** — a subclass created only to borrow methods, with no
  Reference: <https://refactoring.guru/smells/refused-bequest>
  is-a relationship.
