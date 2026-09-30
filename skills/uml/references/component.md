# Component diagram

Shows the system's replaceable parts — services, modules, libraries — and the
interfaces they offer and need. It sits above the class diagram: a box here is
a unit you could build, ship or swap on its own.

## Notation

```plantuml
@startuml
component [Web app] as Web
component [Orders API] as Api
component [Payments] as Payments
interface "REST /orders" as OrdersRest
interface "PaymentGateway" as Gateway
Api - OrdersRest
Web ..> OrdersRest
Payments - Gateway
Api ..> Gateway
database "Orders DB" as Db
Api --> Db
@enduml
```

| Element | PlantUML | Meaning |
|---|---|---|
| Component | `component [Name]` or `[Name]` | A unit with a clear boundary. |
| Provided interface | `C - I` (lollipop) | C offers I. |
| Required interface | `C ..> I` | C needs I. |
| Dependency | `A ..> B` | A uses B. |
| Port | `port`, `portin`, `portout` inside a component | A named point of contact. |
| Grouping | `package`, `node`, `folder`, `frame` | Puts components in a layer or subsystem. |

## Anti-patterns

| Anti-pattern | Why it hurts | Instead |
|---|---|---|
| Classes drawn as components | Mixes levels | A component is a module, package, service or library, not one class. |
| Dependencies with no interface | Hides the contract | Name the interface, route or API the link goes through. |
| Every third-party package | Buries the system's own parts | Show external parts only where the system depends on them directly. |
| Cycles left unmarked | A cycle is a design fact worth seeing | Draw it, and list it in `legend bottom` ... `endlegend`, never in a note floating in the body. |
| One arrow per import | Many arrows between two components say no more than one | One arrow per pair of components. |
| Barrel or re-export modules drawn | An `index` that re-exports points at everything | Leave them out, and say so in `omitted`. |
| A label that repeats the arrow | `uses` on every dashed arrow is noise | Label an arrow with the interface, route or API, or not at all. |
| Over the budget | Past about 15 arrows or 12 components the lines tangle | Keep the components that carry the design, and say what you left out in `omitted`. |
| `skinparam linetype ortho` or `polyline` | Elbows stack on top of each other | Leave the lines as curves. |
