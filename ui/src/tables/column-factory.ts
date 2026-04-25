/**
 * Column Definition Factory
 * =========================
 *
 * Generates TanStack React Table column definitions from EntityUIConfig.
 * Consumers provide ColumnConfig[] (with optional custom renderCell),
 * and this factory produces type-safe column definitions.
 *
 * The factory is headless — it produces data/config, not UI.
 * Cell rendering is either:
 *   1. Custom: consumer provides renderCell in ColumnConfig
 *   2. Default: formatCellValue() for simple text display
 */

import { createColumnHelper, type ColumnDef } from '@tanstack/react-table';
import type { ColumnConfig, EntityUIConfig } from '../schema/entity-config';
import { getNestedValue, formatCellValue } from './utils';

/**
 * Build TanStack column definitions from an EntityUIConfig.
 *
 * Usage:
 *   const columns = buildColumnDefs(leaseAgreementConfig);
 *   // Pass to useReactTable({ columns, data })
 *
 * @param config - EntityUIConfig (or just its columns array)
 * @returns Array of TanStack ColumnDef objects
 */
export function buildColumnDefs<TEntity extends Record<string, unknown> = Record<string, unknown>>(
  config: EntityUIConfig | ColumnConfig[],
): ColumnDef<TEntity, unknown>[] {
  const columns = Array.isArray(config) ? config : config.columns;
  const columnHelper = createColumnHelper<TEntity>();

  return columns.map((col) =>
    columnHelper.accessor(
      (row) => getNestedValue(row, col.fieldPath),
      {
        id: col.fieldPath,
        header: col.header,
        size: col.width,
        enableSorting: col.sortable ?? true,
        enableColumnFilter: col.filterable ?? false,
        cell: col.renderCell
          ? (info) => col.renderCell!(info.getValue(), info.row.original)
          : (info) => formatCellValue(info.getValue()),
      },
    ),
  );
}

/**
 * Merge consumer column overrides onto a base config.
 * Useful when the SDK provides sensible defaults and the consumer
 * wants to override specific columns (e.g., custom status cell).
 *
 * Matching is by fieldPath. Overrides replace the entire ColumnConfig
 * for that field; unmatched overrides are appended.
 */
export function mergeColumnConfigs(
  base: ColumnConfig[],
  overrides: Partial<ColumnConfig>[],
): ColumnConfig[] {
  const result = [...base];
  for (const override of overrides) {
    if (!override.fieldPath) continue;
    const idx = result.findIndex((c) => c.fieldPath === override.fieldPath);
    if (idx >= 0) {
      result[idx] = { ...result[idx], ...override };
    } else {
      result.push(override as ColumnConfig);
    }
  }
  return result;
}
