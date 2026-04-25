/**
 * @vellum/ui/tables — Schema-driven table column generation
 *
 * Exports:
 *   - buildColumnDefs: Factory to generate TanStack column defs from EntityUIConfig
 *   - mergeColumnConfigs: Utility to overlay consumer overrides onto base columns
 *   - getNestedValue: Dot-notation path resolver for nested objects
 *   - timeAgo: Relative time formatter
 *   - formatCellValue: Default cell value formatter
 */

export { buildColumnDefs, mergeColumnConfigs } from './column-factory';
export { getNestedValue, timeAgo, formatCellValue } from './utils';
