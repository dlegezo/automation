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
- 