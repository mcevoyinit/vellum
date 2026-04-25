/**
 * Entity UI Configuration
 * =======================
 *
 * The frontend equivalent of the backend's EntityTypeConfig.
 * One config object drives forms, tables, negotiation, and validation
 * for any entity type.
 *
 * This is the bridge contract: the consumer application provides
 * an EntityUIConfig per domain entity, and the SDK renders accordingly.
 *
 * Backend mirror: vellum/negotiation/entity_config.py
 */

import type { ReactNode } from 'react';

// ---------------------------------------------------------------------------
// Field Configuration
// ---------------------------------------------------------------------------

/** Supported field input types */
export type FieldType =
  | 'string'
  | 'number'
  | 'date'
  | 'datetime'
  | 'enum'
  | 'boolean'
  | 'party'
  | 'document'
  | 'json';

/** UI configuration for a single field */
export interface FieldUIConfig {
  /** Input type for rendering */
  type: FieldType;

  /** Display label (falls back to humanized field path if not provided) */
  label?: string;

  /** Placeholder text for empty inputs */
  placeholder?: string;

  /** Whether the field is required for form submission */
  required?: boolean;

  /**
   * Mandatory level from schema (@mandatory directive).
   * Higher levels = stricter lifecycle requirements.
   */
  mandatoryLevel?: number;

  /** For enum fields: list of allowed values (or async loader) */
  enumValues?: string[] | (() => Promise<string[]>);

  /** For enum fields: human-readable labels for each value */
  enumLabels?: Record<string, string>;

  /** For party-type fields (buyer, seller, etc.) */
  partyConfig?: {
    role: string;
    searchEndpoint?: string;
  };

  /** Whether this field is read-only */
  readOnly?: boolean;

  /** Custom render override for form input */
  renderField?: (props: FieldRenderProps) => ReactNode;

  /** Custom render override for table cell */
  renderCell?: (value: unknown, row: unknown) => ReactNode;
}

/** Props passed to custom field renderers */
export interface FieldRenderProps {
  fieldPath: string;
  value: unknown;
  onChange: (value: unknown) => void;
  disabled: boolean;
  error?: string;
  config: FieldUIConfig;
}

// ---------------------------------------------------------------------------
// Section Configuration (Form Layout)
// ---------------------------------------------------------------------------

/** A logical grouping of fields in a form */
export interface SectionConfig {
  /** Unique section identifier */
  id: string;

  /** Display title */
  title: string;

  /** Optional icon */
  icon?: ReactNode;

  /** Field paths included in this section (ordered) */
  fields: string[];

  /** Whether the section can be collapsed */
  collapsible?: boolean;

  /** Whether the section starts collapsed */
  defaultCollapsed?: boolean;
}

// ---------------------------------------------------------------------------
// Column Configuration (Table Layout)
// ---------------------------------------------------------------------------

/** Configuration for a table column */
export interface ColumnConfig {
  /** Dot-notation path into the entity (e.g., "buyer.companyName") */
  fieldPath: string;

  /** Column header text */
  header: string;

  /** Column width in pixels (auto if not specified) */
  width?: number;

  /** Whether the column is sortable */
  sortable?: boolean;

  /** Whether the column is filterable */
  filterable?: boolean;

  /** Custom cell renderer */
  renderCell?: (value: unknown, row: unknown) => ReactNode;
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/** A single field validation rule */
export interface FieldValidator {
  /** Validation function — returns error message or undefined */
  validate: (value: unknown, entity: Record<string, unknown>) => string | undefined;

  /** When to run: on change, on blur, or on submit */
  trigger?: 'change' | 'blur' | 'submit';
}

// ---------------------------------------------------------------------------
// Entity UI Config (the main contract)
// ---------------------------------------------------------------------------

/**
 * Complete UI configuration for a domain entity type.
 *
 * This is the single object a consumer provides to drive forms, tables,
 * negotiation, and validation for their entity type.
 *
 * Example:
 *   const leaseAgreementConfig: EntityUIConfig = {
 *     typeName: 'LeaseAgreement',
 *     sections: [...],
 *     fields: { 'rent.monthlyAmount': { type: 'number', label: 'Monthly Rent' } },
 *     columns: [...],
 *     negotiableFields: ['rent.monthlyAmount', 'term.endDate'],
 *   };
 */
export interface EntityUIConfig {
  /** GraphQL type name (must match backend schema) */
  typeName: string;

  /** Form sections (ordered) */
  sections: SectionConfig[];

  /** Field-level UI configuration, keyed by dot-notation field path */
  fields: Record<string, FieldUIConfig>;

  /** Table column configuration (ordered) */
  columns: ColumnConfig[];

  /** Field paths that participate in negotiation */
  negotiableFields?: string[];

  /** Field-level validation rules */
  validators?: Record<string, FieldValidator[]>;

  /** Display label overrides (fieldPath -> label) */
  labels?: Record<string, string>;
}
