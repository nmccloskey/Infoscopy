# Contributions

This document records the principal contributions to PSAIR and the research context in which it was developed. It is intended to make the project's history transparent without implying that every contributor to the surrounding research environment is responsible for the software or endorses its present form.

The role descriptions below use CRediT-aligned terminology where it is useful, but this repository record is not itself a determination of authorship for any separate manuscript or publication.

## Nicholas McCloskey

Nicholas McCloskey conceived PSAIR and led its design and development. His contributions include:

- **Conceptualization:** Identified the need for shared backend infrastructure supporting aphasiology-oriented discourse-analysis repositories and defined PSAIR's role within that software ecosystem.
- **Methodology and architecture:** Designed the package structure and the approaches used for documentation workflows, metadata handling, logging and provenance, lightweight NLP support, manual viewing, and example input/output generation.
- **Software:** Implemented the PSAIR codebase and its integrations with DIAAD. At the time of this contribution statement, the repository's public commit history attributes its code contributions to the GitHub account [`nmccloskey`](https://github.com/nmccloskey).
- **Validation and testing:** Developed and maintained automated tests and reviewed PSAIR's behavior within supported DIAAD workflows.
- **Documentation:** Wrote and organized the package documentation, manual tooling, README materials, and example usage.
- **Project administration and release:** Managed the repository, packaging, public releases, and maintenance decisions.

## Laboratory and user feedback

Certain usability aspects of PSAIR's design and integrations were indirectly refined through domain, workflow, and usability feedback regarding DIAAD from members of the conversation treatment study at Temple and Boston Universities. It did not include direct implementation of the PSAIR codebase.

Individual contributors may be named in this document when their contribution is distinctive, accurately describable, and they have agreed to be identified. Group-level acknowledgment is otherwise used to provide credit without implying individual endorsement or responsibility.

## Research environment, resources, and funding

PSAIR was developed in part while Nicholas McCloskey worked in the Speech, Language, and Brain Lab at Temple University. The laboratory provided the applied research context in which requirements for DIAAD and its supporting infrastructure were identified and tested.

Initial development occurred in part during work supported by NIH grants R21 DC015859 and R01 DC018781. Relevant principal investigators may be credited for **Funding acquisition**, **Resources**, and **Supervision** where those roles accurately describe their contribution to the supported research environment.

Funding and institutional support do not imply responsibility for the software's implementation, documentation, maintenance, or later independently developed systems.

## Relationship to DIAAD and RASCAL

PSAIR directly supports DIAAD through shared utilities for:

- metadata extraction and related-file discovery
- logging, provenance, and run records
- lightweight NLP processing and resource loading
- manual and documentation viewing
- example input/output generation

RASCAL is a lab-specific wrapper around DIAAD. RASCAL does not directly import or invoke PSAIR, but it relies on PSAIR indirectly when its DIAAD calls use these shared components.

## Earlier and discontinued scope

Earlier versions of PSAIR contemplated broader ETL, exploratory data analysis, and general pipeline-development functionality. Those areas were not completed and are not part of the repository's current planned scope. Recording that earlier intention is meant to clarify the project history and the status of any residual scaffolding; it should not be read as a claim that those capabilities were implemented.

## Future related work

Future projects may independently implement infrastructure addressing problems previously explored in PSAIR. When PSAIR materially informs later work, it should be identified as a conceptual or technical precursor. Such acknowledgment does not imply that later projects reuse PSAIR source code, depend on this repository, or were supported by the same funding.

## Corrections

Factual corrections to this contribution record may be proposed through a GitHub issue or pull request. Requests should identify the specific contribution, the person or group involved, and supporting project records where available.
