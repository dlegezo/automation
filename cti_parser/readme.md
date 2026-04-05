# CTI Parser Notes

## Metadata

- Tags in metadata could be divided into `actor`, `victim`, etc
- Report UID if we consider cross-report analysis in the future
- Maliciousness and hashes bacame standalone properties 

## Sednit

- No public Icedrive API — reimplemented from official client
- Dual implants strategy: third-party Covenant and custom BeardShell
- Covenant algorithm rewrite for deterministic machine ID; cloud communications to Filen through C2Bridge
- Specific strings from pictures and text for YARA generation? Or try to find new ones online for the same report
- KQL generation from text and pictures? Drawback: reports contain descriptions of old artefacts for attribution purposes

## Handala

- Actors relations on pics - skipped as unreliable and not a priority
- CIDR IOCs for IP indicators. Hunting by CIDR?
- Infection chain is expressed as a plain text timeline.

## APT28

## DKnife

## Stoatwaffle




+ fourth report, pdf one
+ metadata[]
    + severity (how interesting is it)
    + confidence
    + actor in mitre classification
+ vulns
+ iocs[]
    + .regkey .email .filepath .mutex .cert .pipe .service
- queries[].iocs/ttps
+ xrefs[].type == follows for ttps, creates for files, uses for domains
- DKnife, Handala aren't indexed in Mitre groups

Process tree for detection: different type of links for mitre --follows-> mitre and file --uses/creates-> regkey
TTL for specific IOC and TTP - report date, let's keep in metadata
Xrefs Relationship type should not be creates or uses but rather parent / child - from/to are properties, and follows/uses/creates is another property. from/to is a real alternative for parents/children[] and it's broader
Sequence of TTP is important (using xrefs relationship) - connect through xref with follows type
Check how to enrich detection queries from other reports (cross references) - looks like very far shot, not the first epics
Enrich report output with MITRE name for group => Add tags to Json - metadata.actor is the place, check if all the actors have mitre names (Handala)
Show if report is relevant scope (geo, industry) - metadata.severity is the place (naming and discrete values)