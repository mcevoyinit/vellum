/**
 * Field Type Registry
 * ===================
 *
 * Maps field paths to their UI configuration for rendering
 * appropriate input controls.
 *
 * The registry is populated by the consumer's EntityUIConfig.
 * The SDK queries it when rendering forms, tables, and negotiation modals.
 *
 * Backend mirror: the concept of EntityTypeConfig registration in
 * vellum/negotiation/entity_config.py
 */

import type { FieldUIConfig, FieldType } from './entity-config';

/**
 * Humanize a camelCase field path into a display label.
 * "billing.unitPrice" -> "Billing - Unit Price"
 */
export function humanizeFieldPath(fieldPath: string): string {
  return fieldPath
    .split('.')
    .map((part) =>
      part
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, (str) => str.toUpperCase())
        .trim(),
    )
    .join(' - ');
}

/**
 * Infer a FieldType from a GraphQL scalar type name.
 * Used by codegen tools to scaffold EntityUIConfig from schema.
 */
export function inferFieldType(graphqlType: string): FieldType {
  const normalized = graphqlType.replace(/[!\[\]]/g, '');

  switch (normalized) {
    case 'Int':
    case 'Int64':
    case 'Float':
      return 'number';
    case 'DateTime':
      return 'datetime';
    case 'Boolean':
      return 'boolean';
    case 'JSON':
      return 'json';
    default:
      return 'string';
  }
}

/**
 * FieldTypeRegistry
 *
 * In-memory registry of field configurations.
 * Built from one or more EntityUIConfig objects at app init.
 */
export class FieldTypeRegistry {
  private fields: Map<string, FieldUIConfig> = new Map();

  /**
   * Register fields from an EntityUIConfig.
   * Later registrations override earlier ones for the same path.
   */
  registerEntity(entityFields: Record<string, FieldUIConfig>): void {
    for (const [path, config] of Object.entries(entityFields)) {
      this.fields.set(path, config);
    }
  }

  /** Get config for a specific field path. Falls back to string type. */
  get(fieldPath: string): FieldUIConfig {
    return this.fields.get(fieldPath) ?? { type: 'string' };
  }

  /** Check if a field path is registered (and not a plain string). */
  isTyped(fieldPath: string): boolean {
    const info = this.fields.get(fieldPath);
    return !!info && info.type !== 'string';
  }

  /** Get all registered fields. */
  getAll(): Record<string, FieldUIConfig> {
    return Object.fromEntries(this.fields);
  }

  /** Get the display label for a field (config label or humanized path). */
  getLabel(fieldPath: string): string {
    return this.get(fieldPath).label ?? humanizeFieldPath(fieldPath);
  }
}
