# Synthetic Automotive CIA Dataset

This dataset is designed to test a Change Impact Analysis pipeline where changes usually originate at Stakeholder Requirements.

## Pipeline target

Change in Stakeholder Requirement -> traceability validation/recovery -> candidate generation -> impact reasoning -> downstream propagation -> impact report.

## Files

- `stakeholder_requirements.csv`
- `system_requirements.csv`
- `software_requirements.csv`
- `components.csv`
- `test_cases.csv`
- `traceability.csv`
- `requirement_versions.csv`
- `change_requests.csv`
- `expected_impacts.csv`
- `metadata.json`

## Important

The dataset intentionally contains invalid and missing traceability relationships so the system can be tested on more than a perfect graph.
