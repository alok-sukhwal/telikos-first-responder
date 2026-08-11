# Telikos – Billing and Invoicing Capabilities
Source: Telikos Current Capabilities deck — Slide 2 (Billing & Invoice columns,
pre-invoice + during-invoice), Slide 5 (Live billing capabilities and
variations) and Slide 6 (additional capabilities).
Billing pre-invoice runs inside Telikos (BeP-owned), and billing during
invoice runs in SAP FACT (transitioning to S4 / NFTP in 2026).

## Billing validations performed by Telikos
Telikos performs the following billing-related validations before
triggering invoice generation:
- Billing trigger logic
- Billing frequency rules (some frequency rules will move to NFTP in future)
- Consolidated vs Non-Consolidated invoice handling
- Invoice precondition validations (contractual charges updated, VAT
  partner code captured, VAS charges added, etc.)

## Pending tasks indication for FinOps
FinOps users have a dedicated view in Telikos that surfaces pending
pre-invoice prerequisites that must be completed before invoice
generation can be triggered. Tracked prerequisites include contractual
charges, VAT partner code, and VAS charges per booking.

## Default invoice trigger
The default invoice trigger in Telikos is:
- **Imports** — On Estimated Time of Arrival (ETA) of cargo delivery
  for each booking
- **Exports** — On ETA of Gate-In at terminal for each booking

## Billing frequency configurations
Billing frequency rules are configurable. The supported configurations
include:

| Frequency | Default rule | Variation |
|-----------|--------------|-----------|
| Monthly | End of Month (30th / 31st) | Any other date of month |
| Fortnightly / Bi-Weekly | Every other Friday | Any other day-of-week / week |
| Weekly | Friday | Any other day-of-week |
| Daily | N/A | N/A |

All of the above support consolidated invoicing.

## Supplementary invoice rules
For each billing frequency Telikos supports supplementary invoices:
- Non-consolidated supplementary invoices triggered immediately
- Consolidated supplementary invoice triggered immediately
- Consolidated supplementary invoice triggered following the original
  invoice rule

## Rules applicable by
Billing frequency, consolidation and supplementary invoice rules can be
defined per:
- Country
- Customer
- City
- Terminal
- Service Mode (Import / Export)
- Shipper
- Consignee
- Ocean Carrier
- Vessel name

## Manual invoice execution
For exceptions, the invoice can be **manually triggered** before the
default trigger date. Agents can manually trigger an invoice ahead of
the configured rule.

## Send revenue line feeds for Sales Order creation
Telikos sends Revenue line feeds for downstream Sales Order creation in
SAP FACT (transitioning to S4 / Hana with Telikos integration in 2026).

## Revenue-to-Cost mapping (Rev-Cost mapping module)
FinOps agents have the ability to map revenue lines to cost lines.
Telikos runs business rules to perform Rev-to-Cost mapping and then
sends Revenue and Cost lines along with a linkage ID downstream to SAP
FACT.

## Manual billing customer-wise
Operators can manually trigger billing for a specific customer.

## Manual combined billing (2026)
Manual combined / consolidated billing across customers is on the 2026
roadmap.

## Automatic invoice split basis charge codes (2026)
Automated splitting of invoices based on charge codes (e.g. customs vs
inland vs VAS) is planned for 2026.

## Manual invoice trigger for additional invoices (2026)
Moving from automatic to manual invoice trigger for additional invoices
is planned for 2026.

## Invoice standardization basis ATA of intermodal events (2026)
Invoice standardization based on ATA of intermodal events is planned
for 2026.

## Telikos integration with S4 (2026)
End-to-end integration with SAP S4/Hana — including S4 tax validation
in Telikos for invoice orchestration in S4 — is on the 2026 roadmap.

## Container-level invoice (2026)
Container-level (per-container) invoicing is planned for 2026.

## Reprice before invoicing (2026)
The ability to reprice a booking just before invoicing is planned for
2026.

## Send billing milestones through EDI (2026)
Sending billing milestones through EDI to customers is planned for 2026.

## Invoice separator (manual split)
Agents can manually split charges into multiple invoices based on
business requirements.

## Customer-preferred charge name
Agents can define customer-personalized charge names that are printed
on the invoice.

## Passthrough indicator
Telikos can automatically update the passthrough indicator on a charge
based on business rules.

## Visibility of invoice documents
Issued invoice documents (Invoices, Credit Notes) are visible inside
Telikos along with their status (Active / Cancelled).

## Manual invoice dispatch
Agents can manually dispatch invoices from Telikos when the standard
auto-dispatch flow is not used.

## Cash customer invoice trigger
For cash customers the invoice is automatically triggered after the
order is sent to Finance.

## Invoice reference
Agents can add an invoice reference value that gets printed on the
invoice (useful for customer-specific reference numbers).

## Add manual charges and manual costs (non-TMS costs)
FinOps agents can manually add charges (revenue) and costs (non-TMS
costs) to an invoice.

## VAT partner ID code for Tax validation in SAP FACT
Telikos captures the VAT partner ID code and forwards it to SAP FACT
for tax validation. This capability is to be deprecated when the S4 /
Hana integration is live.

## During-invoice activities (SAP FACT / S4)
The following activities happen in SAP FACT (with NFTP / S4 in 2026):
- Create Sales Orders
- Update Sales Orders
- Generate Invoice
- Invoice cancellation / Credit notes issuance
- PO creation (vendor invoice)
- Revenue recognition process

## Upcoming / exploring billing capabilities
The following items appear on the deck as "Upcoming and Exploring":
- Standard billing logic change to **ETA + X days**
- **ATA + 5** based invoicing
- **Bulk invoice trigger**
- **Container-level billing**
- Billing consolidation with additional parameters — customer facility,
  carrier bill of lading number, booked-by customer
- **Manual consolidation of billing at container level**
