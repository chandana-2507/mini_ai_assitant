# AI-Assisted Development Notes

## AI tools used
ChatGPT was used as an AI coding assistant for planning the application structure, drafting starter code, proposing tests, and improving documentation. The final implementation should be run and reviewed by the candidate before submission.

## How AI was used
The challenge was split into data loading, question interpretation, database analytics, UI presentation, automated tests, and setup documentation. The implementation uses deterministic intent matching and predefined SQL rather than unrestricted generated SQL.

## Problems encountered and debugging decisions
- A row in the supplied CSV has a missing unit price. The importer rejects that row rather than guessing a price.
- Returned transactions are excluded from revenue to avoid counting returned goods as sales.
- Unsupported questions are rejected with an actionable message.
- Automated tests check data loading, all five supported analytics, and invalid input handling.

## Improvements with another day
Use an LLM with constrained intent JSON (not raw SQL), add charts and exports, improve date-range parsing, add authentication, and run the app in Docker/CI.
