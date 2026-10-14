# ISO Quality Models for NFRs

Every NFR names one ISO characteristic and one subcharacteristic. Pick
them from the lists below. Do not invent names.

## ISO/IEC 25002:2024 — how to use the models

ISO/IEC 25002 explains how to pick and tailor the models below for a
product. Apply it as:

- Select only the characteristics that matter for the feature. A feature
  does not need an NFR for all of them.
- Tailor each selected subcharacteristic into a measure with a target.
- Rank the selected NFRs. The rank drives the order of work and the
  trade-offs (see Priority in `./nfr-template.md`).

## ISO/IEC 25010:2023 — product quality

| Characteristic | Subcharacteristics |
|---|---|
| Functional suitability | Functional completeness, Functional correctness, Functional appropriateness |
| Performance efficiency | Time behaviour, Resource utilization, Capacity |
| Compatibility | Co-existence, Interoperability |
| Interaction capability | Appropriateness recognizability, Learnability, Operability, User error protection, User engagement, Inclusivity, User assistance, Self-descriptiveness |
| Reliability | Faultlessness, Availability, Fault tolerance, Recoverability |
| Security | Confidentiality, Integrity, Non-repudiation, Accountability, Authenticity, Resistance |
| Maintainability | Modularity, Reusability, Analysability, Modifiability, Testability |
| Flexibility | Adaptability, Scalability, Installability, Replaceability |
| Safety | Operational constraint, Risk identification, Fail safe, Hazard warning, Safe integration |

## ISO/IEC 25019:2023 — quality in use

| Characteristic | Subcharacteristics |
|---|---|
| Beneficialness | Usability, Accessibility, Suitability |
| Freedom from risk | Freedom from economic risk, Freedom from environmental and societal risk, Freedom from health risk, Freedom from human life risk |
| Acceptability | Experience, Trustworthiness, Compliance |

## Mapping the 8 NFR types to ISO

| NFR type | ISO characteristic › subcharacteristic |
|---|---|
| Performance | 25010 Performance efficiency › Time behaviour, Resource utilization, Capacity |
| Reliability | 25010 Reliability › Faultlessness, Fault tolerance, Recoverability |
| Availability | 25010 Reliability › Availability |
| Security | 25010 Security › any subcharacteristic |
| Usability | 25010 Interaction capability › any subcharacteristic; 25019 Beneficialness › Usability, Accessibility |
| Portability | 25010 Flexibility › Adaptability, Installability, Replaceability; Compatibility › Interoperability |
| Scalability | 25010 Flexibility › Scalability; Performance efficiency › Capacity |
| Regulations/laws | 25019 Acceptability › Compliance; Freedom from risk › Freedom from economic risk; 25010 Security › Accountability, Non-repudiation |

When a requirement fits none of these rows, name the closest ISO
characteristic and flag the mismatch to the engineer.
