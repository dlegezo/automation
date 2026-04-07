# CTI Parser

This README is a navigation map for project logic and entry points.
Detailed specs stay in docs and schema files to avoid duplication.

## Project Flow

1. Define parsing inputs and monitoring profile in [inbound/inbound.json](inbound/inbound.json).
2. Validate structures with schemas in [schemes](schemes).
3. Produce per-report intelligence JSON files in [outbound](outbound).
4. Build analytical outputs in [diagrams/attribution](diagrams/attribution) and [diagrams](diagrams).

## Schemas

- Pipeline schema (input + publishing + tags_of_interest): [schemes/pipeline-schema.json](schemes/pipeline-schema.json)
- IOC report schema (per-report output envelope and entities): [schemes/iocs-schema.json](schemes/iocs-schema.json)
- Schema docs:
  - [docs/pipeline-schema.md](docs/pipeline-schema.md)
  - [docs/iocs-schema.md](docs/iocs-schema.md)

## Inbound

- Main input config: [inbound/inbound.json](inbound/inbound.json)
- Contains:
  - source report list (URLs/files and metadata)
  - publishing targets
  - tags_of_interest (AXA-oriented countries, industries, malware, actors)

## Outbound

- Per-report parsed outputs live in [outbound](outbound)
- Severity recalculation script (Jaccard similarity share against inbound tags_of_interest): [utils/count_severity.py](utils/count_severity.py)

Current per-report files:
- [outbound/sednit-reloaded-back-trenches.json](outbound/sednit-reloaded-back-trenches.json)
- [outbound/handala-hack-unveiling-groups-modus-operandi.json](outbound/handala-hack-unveiling-groups-modus-operandi.json)
- [outbound/apt28-leverages-cve-2026-21509-operation-neusploit.json](outbound/apt28-leverages-cve-2026-21509-operation-neusploit.json)
- [outbound/talos-dknife.json](outbound/talos-dknife.json)
- [outbound/stoatwaffle-malware.json](outbound/stoatwaffle-malware.json)

## Attribution

- Pairwise report distance analysis (TTP, follows-chain, tags) and follows-pair popularity: [diagrams/builders/build_attribution.py](diagrams/builders/build_attribution.py)
- Shared Jaccard and normalization helpers: [utils/utils.py](utils/utils.py)
- Generated table: [diagrams/attribution/attribution.md](diagrams/attribution/attribution.md)

## Diagrams

- TTP chain builder: [diagrams/builders/build_ttps_chain_mmd.py](diagrams/builders/build_ttps_chain_mmd.py)
- IOC chain builder: [diagrams/builders/build_iocs_chain_mmd.py](diagrams/builders/build_iocs_chain_mmd.py)
- Diagram sources:
  - [diagrams/pipeline-schema.mmd](diagrams/pipeline-schema.mmd)
  - [diagrams/iocs-schema.mmd](diagrams/iocs-schema.mmd)
  - [diagrams/ttps_chain.mmd](diagrams/ttps_chain.mmd)
  - [diagrams/iocs_chain.mmd](diagrams/iocs_chain.mmd)

## Run

- Recalculate report severity: `python cti_parser/utils/count_severity.py`
- Recalculate attribution markdown: `python cti_parser/diagrams/builders/build_attribution.py`
- Rebuild IOC chain diagram: `python cti_parser/diagrams/builders/build_iocs_chain_mmd.py`
- Rebuild TTP chain diagram: `python cti_parser/diagrams/builders/build_ttps_chain_mmd.py`
- Start API server: `python cti_parser/api/server.py`

## Notes

- Previous free-form project notes were moved to [notes.md](notes.md).
