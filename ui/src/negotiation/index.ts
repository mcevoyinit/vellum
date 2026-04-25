// Types
export type {
  FieldNegotiationStatus,
  ProposalStatus,
  NegotiationRole,
  SubmitProposalRequest,
  AcceptProposalRequest,
  RejectProposalRequest,
  Proposal,
  PartyValue,
  FieldStatus,
  SubmitProposalResponse,
  AcceptProposalResponse,
  RejectProposalResponse,
  CounterProposalResponse,
  RejectOrCounterResponse,
  AllFieldStatusesResponse,
  FieldHistoryEntry,
  FieldHistoryResponse,
  PendingProposal,
  PendingProposalsResponse,
  NegotiationErrorResponse,
  NegotiationErrorCode,
  StatusIndicatorConfig,
  NegotiationFieldIndicatorProps,
} from './types';

// Type guards & helpers
export {
  isNegotiationError,
  isCounterProposalResponse,
  parseProposalValue,
  formatRole,
  formatFieldPath,
} from './types';

// Service
export {
  NegotiationServiceError,
  submitProposal,
  acceptProposal,
  rejectProposal,
  getEntityFieldStatuses,
  getFieldHistory,
  getPendingProposals,
} from './service';

// Hooks
export type {
  UseEntityNegotiationOptions,
  UseEntityNegotiationReturn,
} from './hooks';
export { useEntityNegotiation, usePendingProposals } from './hooks';
