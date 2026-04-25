/**
 * Vellum UI SDK
 * =============
 *
 * Domain-agnostic UI primitives for multi-party negotiation,
 * schema-driven forms, tables, and enterprise settlement workflows.
 *
 * The TypeScript companion to the Vellum Python protocol library.
 *
 * Packages:
 *   @vellum/ui/core         - Theme, provider, API config
 *   @vellum/ui/schema       - EntityUIConfig, FieldTypeRegistry
 *   @vellum/ui/negotiation  - Field-level bilateral negotiation
 *   @vellum/ui/forms        - Schema-driven form generation (planned)
 *   @vellum/ui/tables       - Schema-driven table generation
 *   @vellum/ui/seal         - Document signing/verification (planned)
 *   @vellum/ui/agentic      - Chat, terminal, trust layer (planned)
 *   @vellum/ui/settings     - Org/member management (planned)
 *   @vellum/ui/auth         - Auth provider, protected routes (planned)
 */

// Re-export all public APIs
export * from './core';
export * from './schema';
export * from './negotiation';
export * from './tables';
