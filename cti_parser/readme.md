# CTI Parser

This README is a navigation map for project logic and entry points.
Detailed specs stay in docs and schema files to avoid duplication.

## Project Flow

1. Define parsing inputs and monitoring profile in [inbound/inbound.json](inbound/inbound.json).
2. Validate structures with schemas in [schemes](schemes).
3. Produce per-report intelligence JSON files in [outbound](outbound).
4. Build analytical outputs in [attribution](attribution) and [diagrams](diagrams).

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
- Severity recalculation script (Jaccard distance against inbound tags_of_interest): [utils/count_severity.py](utils/count_severity.py)

Current per-report files:
- [outbound/sednit-reloaded-back-trenches.json](outbound/sednit-reloaded-back-trenches.json)
- [outbound/handala-hack-unveiling-groups-modus-operandi.json](outbound/handala-hack-unveiling-groups-modus-operandi.json)
- [outbound/apt28-leverages-cve-2026-21509-operation-neusploit.json](outbound/apt28-leverages-cve-2026-21509-operation-neusploit.json)
- [outbound/talos-dknife.json](outbound/talos-dknife.json)
- [outbound/stoatwaffle-malware.json](outbound/stoatwaffle-malware.json)

## Attribution

- Pairwise report distance analysis (TTP, follows-chain, tags): [utils/count_attribution.py](utils/count_attribution.py)
- Shared Jaccard and normalization helpers: [utils/utils.py](utils/utils.py)
- Generated table: [attribution/attribution.md](attribution/attribution.md)

## Diagrams

- TTP chain builder: [diagrams/build_ttps_chain_mmd.py](diagrams/build_ttps_chain_mmd.py)
- IOC chain builder: [diagrams/build_iocs_chain_mmd.py](diagrams/build_iocs_chain_mmd.py)
- Diagram sources:
  - [diagrams/pipeline-schema.mmd](diagrams/pipeline-schema.mmd)
  - [diagrams/iocs-schema.mmd](diagrams/iocs-schema.mmd)
  - [diagrams/ttps_chain.mmd](diagrams/ttps_chain.mmd)
  - [diagrams/iocs_chain.mmd](diagrams/iocs_chain.mmd)

## Notes

- Previous free-form project notes were moved to [notes.md](notes.md).
