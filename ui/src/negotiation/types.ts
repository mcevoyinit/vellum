/**
 * Vellum Negotiation Types
 * ========================
 *
 * Domain-agnostic types for field-level bilateral negotiation.
 *
 * State Flow: DRAFT -> PROPOSED -> AGREED -> LOCKED
 *                      -> COUNTER_PROPOSED ->
 *                      -> REJECTED
 *
 * Backend mirror: vellum/negotiation/proposal_types.py
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

/** Possible states for a negotiable field */
export type FieldNegotiationStatus =
  | 'DRAFT'
  | 'PROPOSED'
  | 'COUNTER_PROPOSED'
  | 'DISCREPANCY'
  | 'AGREED'
  | 'LOCKED'
  | 'REJECTED';

/** Status of an individual proposal */
export type ProposalStatus =
  | 'PENDING'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'COUNTER_PROPOSED'
  | 'SUPERSEDED';

/**
 * Role of a party in negotiation.
 * String type allows consumer-defined roles (buyer/seller, lessor/lessee, etc.)
 */
export type NegotiationRole = string;

// ---------------------------------------------------------------------------
// API Request Types
// ---------------------------------------------------------------------------

/** Request body for submitting a new proposal */
export interface SubmitProposalRequest {
  /** Entity ID (trade, lease, agreement, etc.) */
  entityId: string;
  /** Dot-notation field path, e.g., "price" or "delivery.quantity" */
  fieldPath: string;
  /** The proposed value */
  proposedValue: string | number | boolean | Record<string, unknown>;
  /** Optional comment */
  comment?: string;
  /** Proposer's role */
  proposerRole?: string;
}

/** Request body for accepting a proposal */
export interface AcceptProposalRequest {
  comment?: string;
  acceptorRole?: string;
}

/** Request body for rejecting (optionally with counter) */
export interface RejectProposalRequest {
  comment?: string;
  /** If provided, creates a counter-proposal */
  counterValue?: string | number | boolean | Record<string, unknown>;
  rejectorRole?: string;
}

// ---------------------------------------------------------------------------
// API Response Types
// ---------------------------------------------------------------------------

/** Core proposal object */
export interface Proposal {
  id: string;
  entityId: string;
  fieldPath: string;
  proposedValue: string;
  proposerRole: NegotiationRole;
  proposerMemberId?: string;
  proposerCollaboratorId?: string;
  proposedAt: string;
  status: ProposalStatus;
  respondedAt?: string | null;
  respondedByMemberId?: string | null;
  comment?: string | null;
  responseComment?: string | null;
  counterProposalId?: string | null;
  isAmendment?: boolean;
  previousAgreedValue?: string;
  blockchainTxHash?: string;
}

/** Value held by a specific party for a field */
export interface PartyValue {
  role: NegotiationRole;
  partyId: string;
  partyName?: string;
  value: string;
  status: 'PROPOSED' | 'AGREED' | 'DRAFT';
  proposedAt?: string;
}

/** Current negotiation status for a single field */
export interface FieldStatus {
  entityId: string;
  fieldPath: string;
  currentValue: string | null;
  status: FieldNegotiationStatus;
  partyValues: PartyValue[];
  requiredApprovers: NegotiationRole[];
  approvedByRoles: NegotiationRole[];
  lastUpdated: string | null;
  pendingProposalId: string | null;
}

/** Response from submitting a proposal */
export interface SubmitProposalResponse {
  success: boolean;
  proposal: Proposal;
  fieldStatus: {
    status: FieldNegotiationStatus;
    currentValue: string | null;
  };
  error?: string;
}

/** Response from accepting a proposal */
export interface AcceptProposalResponse {
  success: boolean;
  proposal: {
    id: string;
    status: 'ACCEPTED';
    respondedAt: string;
    respondedBy: string;
  };
  fieldStatus: {
    status: 'AGREED';
    currentValue: string;
    approvedByRoles: NegotiationRole[];
  };
  consensusReached: boolean;
  error?: string;
}

/** Response from rejecting a proposal (without counter) */
export interface RejectProposalResponse {
  success: boolean;
  proposal: {
    id: string;
    status: 'REJECTED';
  };
  fieldStatus: {
    status: FieldNegotiationStatus;
  };
  error?: string;
}

/** Response from rejecting with a counter-proposal */
export interface CounterProposalResponse {
  success: boolean;
  originalProposal: {
    id: string;
    status: 'COUNTER_PROPOSED';
  };
  counterProposal: Proposal;
  fieldStatus: {
    status: 'COUNTER_PROPOSED';
    negotiationRound: number;
  };
  error?: string;
}

export type RejectOrCounterResponse = RejectProposalResponse | CounterProposalResponse;

/** All field statuses for an entity */
export interface AllFieldStatusesResponse {
  success: boolean;
  entityId: string;
  fields: Record<string, FieldStatus>;
  summary: {
    agreed: number;
    pending: number;
    draft: number;
    locked: number;
    rejected: number;
  };
  yourRole?: NegotiationRole;
}

/** A single entry in field history */
export interface FieldHistoryEntry {
  proposalId: string;
  proposedValue: string;
  proposerRole: NegotiationRole;
  proposerPartyId?: string;
  proposedAt: string;
  status: ProposalStatus;
  respondedAt: string | null;
  responseByRole?: NegotiationRole;
  isAmendment: boolean;
  previousValue: string | null;
  blockchainTxHash: string | null;
}

/** Field history response */
export interface FieldHistoryResponse {
  entityId: string;
  fieldPath: string;
  currentStatus: FieldNegotiationStatus;
  currentValue: string | null;
  entries: FieldHistoryEntry[];
}

/** A pending proposal awaiting response */
export interface PendingProposal {
  id: string;
  entityId: string;
  fieldPath: string;
  proposedValue: string;
  proposerRole: NegotiationRole;
  proposerMemberId?: string;
  proposedAt: string;
  awaitingResponseFrom: NegotiationRole[];
}

/** Pending proposals response */
export interface PendingProposalsResponse {
  proposals: PendingProposal[];
  count: number;
}

// ---------------------------------------------------------------------------
// Error Types
// ---------------------------------------------------------------------------

export interface NegotiationErrorResponse {
  success: false;
  error: string;
  code?: NegotiationErrorCode;
}

export type NegotiationErrorCode =
  | 'FIELD_LOCKED'
  | 'PROPOSAL_EXISTS'
  | 'NOT_AUTHORIZED'
  | 'PROPOSAL_NOT_FOUND'
  | 'INVALID_FIELD_PATH'
  | 'CONSENSUS_REQUIRED'
  | 'ALREADY_RESPONDED';

// ---------------------------------------------------------------------------
// UI Helper Types
// ---------------------------------------------------------------------------

/** Configuration for status indicator display */
export interface StatusIndicatorConfig {
  icon: string;
  color: string;
  label: string;
  animation?: string;
  tooltip: string;
}

/** Props for NegotiationFieldIndicator component */
export interface NegotiationFieldIndicatorProps {
  status: FieldNegotiationStatus;
  pendingProposal?: {
    id: string;
    proposerRole: NegotiationRole;
    proposedValue: string;
    proposedAt: string;
  };
  isMyProposal?: boolean;
  onClick?: () => void;
}

// ---------------------------------------------------------------------------
// Type Guards & Helpers
// ---------------------------------------------------------------------------

export function isNegotiationError(
  response: unknown,
): response is NegotiationErrorResponse {
  return (
    typeof response === 'object' &&
    response !== null &&
    'success' in response &&
    (response as { success: unknown }).success === false &&
    'error' in response
  );
}

export function isCounterProposalResponse(
  response: RejectOrCounterResponse,
): response is CounterProposalResponse {
  return 'counterProposal' in response;
}

export function parseProposalValue(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

export function formatRole(role: NegotiationRole): string {
  return role.charAt(0).toUpperCase() + role.slice(1);
}

export function formatFieldPath(fieldPath: string): string {
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
