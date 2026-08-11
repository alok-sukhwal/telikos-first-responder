# Telikos – Offer Search and Select Capabilities
Source: Telikos Current Capabilities deck, Slide 2 (Offer Search and Select column)
and Slide 7 (Pricing capabilities reused for offer rendering).
The Offer Search & Select domain in Telikos is powered by the MEPC platform for
routing and Athena Lite for pricing (interim Telikos pricing solution).

## Manage route via the intermodal MEPC query
Telikos uses the MEPC platform to resolve intermodal routes between origin and
destination locations for inland transportation. The route engine produces a
ranked set of intermodal options for a given origin / destination / container
configuration.

## Athena Lite pricing engine
Pricing is rendered via the **Athena Lite** interim pricing solution. The
engine retrieves rates using the following determinants:
- Origin, destination, container type and direction (Import / Export)
- Reefer flag, dangerous goods flag
- Diesel slab pricing variations
- Electric Vehicle (EV) pricing
- Empty container pickup / drop-off location and mode of transport (MOT)

These same determinants feed the priced offer that an agent sees during order
search & select.

## Address-to-address pricing (2026)
Address-to-address (door-to-door) pricing for intermodal offers is on the
2026 roadmap. Currently pricing is resolved at the city / terminal / site
level rather than full street-address granularity.

## Display of pricing and routing
Once an offer is retrieved, Telikos displays both the routing options
returned by MEPC and the pricing returned by Athena Lite alongside each
other, with the chosen offer carried forward into the order create flow.
