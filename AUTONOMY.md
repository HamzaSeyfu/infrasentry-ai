# Autonomous development policy

This repository is designed to be developed incrementally with a high degree of autonomous engineering.

## Decisions that can be made without product-owner approval

- Code structure and refactoring
- Test strategy and test additions
- Small dependency additions with a clear technical justification
- CI, linting and developer tooling
- Documentation improvements
- Bug fixes
- Small features already implied by the roadmap
- Internal APIs that do not create user-facing lock-in

## Decisions that should be escalated

- Major scope changes
- Paid external-service dependencies
- Breaking public interfaces after a stable release
- Destructive migration or deletion of meaningful project history
- Changes that substantially alter the target user or project purpose

## Working rules

1. Prefer one coherent improvement over filler commits.
2. Keep the project usable without a paid LLM API.
3. Gather deterministic evidence before applying AI reasoning.
4. Add tests for every diagnosis rule or regression.
5. Update the roadmap when scope or status changes.
