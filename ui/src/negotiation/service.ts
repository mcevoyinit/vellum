/**
 * Vellum Negotiation Service
 * ==========================
 *
 * Domain-agnostic API client for the Vellum negotiation protocol.
 * All endpoints are parameterized via VellumApiConfig.
 *
 * Backend mirror: vellum/negotiation/orchestrator.py
 */

import type { VellumApiConfig } from '../core/api';
import { vellumFetch, DEFAULT_ENDPOINTS } from '../core/api';
import type {
  SubmitProposalRequest,
  SubmitProposalResponse,
  AcceptProposalRequest,
  AcceptProposalResponse,
  RejectProposalRequest,
  RejectOrCounterResponse,
  AllFieldStatusesResponse,
  FieldHistoryResponse,
  PendingProposalsResponse,
  NegotiationErrorResponse,
} from './types';
import { isNegotiationError } from './types';

/** Error thrown by negotiation service calls */
export class NegotiationServiceError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number,
  ) {
    super(message);
    this.name = 'NegotiationServiceError';
  }
}

function getBasePath(config: VellumApiConfig): string {
  return config.endpoints?.negotiation ?? DEFAULT_ENDPOINTS.negotiation;
}

async function handleResponse<T>(response: Response): Promise<T> {
  const data = await response.json();

  if (!response.ok || isNegotiationError(data)) {
    const err = data as NegotiationErrorResponse;
    throw new NegotiationServiceError(
      err.error ?? `HTTP ${response.status}`,
      err.code,
      response.status,
    );
  }

  return data as T;
}

// ---------------------------------------------------------------------------
// Service Functions
// ---------------------------------------------------------------------------

/** Submit a new proposal for a field */
export async function submitProposal(
  config: VellumApiConfig,
  request: SubmitProposalRequest,
): Promise<SubmitProposalResponse> {
  const res = await vellumFetch(config, `${getBasePath(config)}/proposals`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
  return handleResponse(res);
}

/** Accept a pending proposal */
export async function acceptProposal(
  config: VellumApiConfig,
  proposalId: string,
  request: AcceptProposalRequest = {},
): Promise<AcceptProposalResponse> {
  const res = await vellumFetch(
    config,
    `${getBasePath(config)}/proposals/${proposalId}/accept`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    },
  );
  return handleResponse(res);
}

/** Reject a proposal (optionally with counter-value) */
export async function rejectProposal(
  config: VellumApiConfig,
  proposalId: string,
  request: RejectProposalRequest = {},
): Promise<RejectOrCounterResponse> {
  const res = await vellumFetch(
    config,
    `${getBasePath(config)}/proposals/${proposalId}/reject`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    },
  );
  return handleResponse(res);
}

/** Get all field statuses for an entity */
export async function getEntityFieldStatuses(
  config: VellumApiConfig,
  entityId: string,
): Promise<AllFieldStatusesResponse> {
  const res = await vellumFetch(
    config,
    `${getBasePath(config)}/entity/${entityId}/status`,
  );
  return handleResponse(res);
}

/** Get negotiation history for a specific field */
export async function getFieldHistory(
  config: VellumApiConfig,
  entityId: string,
  fieldPath: string,
): Promise<FieldHistoryResponse> {
  const encodedPath = encodeURIComponent(fieldPath);
  const res = await vellumFetch(
    config,
    `${getBasePath(config)}/entity/${entityId}/field/${encodedPath}/history`,
  );
  return handleResponse(res);
}

/** Get all pending proposals for the current user */
export async function getPendingProposals(
  config: VellumApiConfig,
): Promise<PendingProposalsResponse> {
  const res = await vellumFetch(config, `${getBasePath(config)}/pending`);
  return handleResponse(res);
}
