# Class diagram

Shows the types in the system, what each one holds and does, and how they
relate. It is the diagram most readers open first, so it carries the names
the code uses.

## Notation

```plantuml
@startuml
abstract class Payment {
  #amount: Money
  +{abstract} capture(): Result
}
interface Refundable {
  +refund(amount: Money): Result
}
enum PaymentState {
  PENDING
  CAPTURED
  REFUNDED
}
class CardPayment {
  -token: String
  +capture(): Result
  +refund(amount: Money): Result
}
class Order {
  +id: OrderId
  +{static} create(cart: Cart): Order
}
Payment <|-- CardPayment
Refundable <|.. CardPayment
Order "1" *-- "1..*" LineItem : lines
Order "1" o-- "0..1" Payment
Order ..> PaymentState : reads
@enduml
```

| Element | PlantUML | Meaning |
|---|---|---|
| Visibility | `+` public, `-` private, `#` protected, `~` package | Who can reach the member. |
| Static member | `{static}` | Belongs to the type, not an instance. |
| Abstract member or type | `{abstract}`, `abstract class` | Has no body here; a subtype supplies it. |
| Interface | `interface Name` | A contract with no state. |
| Enum | `enum Name` | A closed set of values. |
| Inheritance | `Base <\|-- Sub` | Sub is a kind of Base. |
| Realization | `Contract <\|.. Impl` | Impl fulfils the interface. |
| Composition | `Whole *-- Part` | The part lives and dies with the whole. |
| Aggregation | `Whole o-- Part` | The whole holds the part, which can outlive it. |
| Association | `A -- B`, `A --> B` | A knows B; the arrow gives the direction of navigation. |
| Dependency | `A ..> B` | A uses B briefly, such as a parameter or a return type. |
| Multiplicity | `"1" -- "0..*"` | How many on each end: `1`, `0..1`, `*`, `1..*`, `n..m`. |
| Role or label | `A -- B : owner` | Names the link. |

The theme colours the letter badge by kind: interfaces, abstract classes and
enums each get their own colour, so do not add colours by hand.

## Anti-patterns

| Anti-pattern | Why it hurts | Instead |
|---|---|---|
| Every class in the repo on one canvas | Nobody can read a hundred boxes | Draw the central domain; leave out helpers, DTOs and framework glue. |
| Every getter and setter listed | Hides the members that matter | Show the fields and methods that carry the behaviour. |
| Composition used for any "has a" | Claims a lifetime rule the code does not keep | Use composition only when the part cannot exist without the whole. |
| No multiplicity on associations | The reader cannot tell one from many | Put multiplicity on both ends of every association that has one. |
| Inheritance drawn where the code composes | Misstates the design | Draw what the code does, not what it could do. |
| Names changed to sound nicer | The reader cannot find them in the code | Use the names in the code, as written. |
