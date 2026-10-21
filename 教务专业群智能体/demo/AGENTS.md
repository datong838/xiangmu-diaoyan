# Prototype Instructions

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.

The overview must foreground how one real school task is handled from start to finish. Use the confirmed working chain from the 4178 school-facing presentation as the business source: building basis, assigning work, receiving teachers' records, checking evidence, judging progress, creating follow-up work, and forming reports. For every step, show the work object, responsible person, assistant action, school confirmation point, and resulting output. Do not turn the overview into a status-only dashboard and do not invent school capabilities beyond the source documents.

Treat the prototype as a product design, not a visual copy of the school-facing business presentation. The product must visibly support multi-role action: teachers and administrators submit, edit, relate, review, return, confirm, and version materials around goals. Present the professional-group assistant as a working digital employee that accepts tasks and operates on permitted context. Apply Semantica-inspired principles at the product-model level: goals, tasks, people, events, files, evidence, conclusions, and outputs are typed facts connected by explicit relationships; every submission, correction, invalidation, and confirmation remains in a chronological ledger instead of being silently overwritten or deleted. Use school-friendly wording and do not imply that Semantica itself is embedded.

Keep the navigation visually integrated with the workspace. Avoid a high-contrast black sidebar beside a light content surface; use a light, calm education-workspace palette with clear active states.

The selected full-site visual reference is `/Users/ddt/work/projects/ai_agent/docs/palantier/foundry/html/workshop-content-campaign.html` (`http://127.0.0.1:18465/workshop-content-campaign.html`). Match its compact Foundry-style frame: a narrow dark global tool rail, white business navigation, 48px header, blue-gray work surface, 1px borders, small radii, dense typography, three-column work area, blue primary actions, and green/amber/red states. Preserve all professional-group content and interactions. On narrow screens keep the professional-group prototype usable instead of reproducing the reference page's horizontal clipping.

Write all non-assistant interface copy as product UI language: name the function, managed object, user action, or current state directly. Do not reuse school-facing presentation phrases such as “先……”“把……”“都在这里……”“只需……”. The professional-group assistant may remain conversational, but page titles, module titles, form labels, buttons, and system notices must be concise and operational.
