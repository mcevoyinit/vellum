/**
 * Vellum Negotiation Hooks
 * ========================
 *
 * React hooks for negotiation state management.
 * These wrap the negotiation service with React state and provide
 * a clean interface for components.
 */

import { useState, useCallback, useEffect } from 'react';
import { useVellumApi } from '../core/provider';
import type {
  AllFieldStatusesResponse,
  FieldStatus,
  FieldNegotiationStatus,
  NegotiationRole,
  SubmitProposalRequest,
  SubmitProposalResponse,
  AcceptProposalResponse,
  RejectOrCounterResponse,
  PendingProposalsResponse,
} from './types';
import * as service from './service';

// ---------------------------------------------------------------------------
// useEntityNegotiation — main hook for entity-level negotiation state
// ---------------------------------------------------------------------------

export interface UseEntityNegotiationOptions {
  /** Entity ID to track */
  entityId: string | undefined;
  /** Auto-refresh interval in ms (0 to disable) */
  pollInterval?: number;
}

export interface UseEntityNegotiationReturn {
  /** All field statuses for this entity */
  fieldStatuses: Record<string, FieldStatus>;
  /** Summary counts */
  summary: AllFieldStatusesResponse['summary'] | null;
  /** Current user's role on this entity */
  yourRole: NegotiationRole | undefined;
  /** Loading state */
  loading: boolean;
  /** Error message */
  error: string | null;

  /** Refresh field statuses */
  refresh: () => Promise<void>;
  /** Submit a proposal */
  submitProposal: (
    fieldPath: string,
    proposedValue: SubmitProposalRequest['proposedValue'],
    comment?: string,
  ) => Promise<SubmitProposalResponse>;
  /** Accept a proposal */
  acceptProposal: (proposalId: string, comment?: string) => Promise<AcceptProposalResponse>;
  /** Reject a proposal (optionally with counter-value) */
  rejectProposal: (
    proposalId: string,
    comment?: string,
    counterValue?: SubmitProposalRequest['proposedValue'],
  ) => Promise<RejectOrCounterResponse>;

  /** Get status for a specific field */
  getFieldStatus: (fieldPath: string) => FieldStatus | undefined;
  /** Check if a field has a specific status */
  isFieldStatus: (fieldPath: string, status: FieldNegotiationStatus) => boolean;
  /** Count of pending proposals */
  pendingCount: number;
}

export function useEntityNegotiation({
  entityId,
  pollInterval = 0,
}: UseEntityNegotiationOptions): UseEntityNegotiationReturn {
  const apiConfig = useVellumApi();

  const [fieldStatuses, setFieldStatuses] = useState<Record<string, FieldStatus>>({});
  const [summary, setSummary] = useState<AllFieldStatusesResponse['summary'] | null>(null);
  const [yourRole, setYourRole] = useState<NegotiationRole | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!entityId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await service.getEntityFieldStatuses(apiConfig, entityId);
      setFieldStatuses(data.fields);
      setSummary(data.summary);
      setYourRole(data.yourRole);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch negotiation status');
    } finally {
      setLoading(false);
    }
  }, [apiConfig, entityId]);

  // Initial fetch
  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Polling
  useEffect(() => {
    if (!pollInterval || !entityId) return;
    const interval = setInterval(() => void refresh(), pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval, entityId, refresh]);

  const submitProposalFn = useCallback(
    async (
      fieldPath: string,
      proposedValue: SubmitProposalRequest['proposedValue'],
      comment?: string,
    ) => {
      if (!entityId) throw new Error('No entity ID');
      const result = await service.submitProposal(apiConfig, {
        entityId,
        fieldPath,
        proposedValue,
        comment,
        proposerRole: yourRole,
      });
      // Refresh after mutation
      void refresh();
      return result;
    },
    [apiConfig, entityId, yourRole, refresh],
  );

  const acceptProposalFn = useCallback(
    async (proposalId: string, comment?: string) => {
      const result = await service.acceptProposal(apiConfig, proposalId, {
        comment,
        acceptorRole: yourRole,
      });
      void refresh();
      return result;
    },
    [apiConfig, yourRole, refresh],
  );

  const rejectProposalFn = useCallback(
    async (
      proposalId: string,
      comment?: string,
      counterValue?: SubmitProposalRequest['proposedValue'],
    ) => {
      const result = await service.rejectProposal(apiConfig, proposalId, {
        comment,
        counterValue,
        rejectorRole: yourRole,
      });
      void refresh();
      return result;
    },
    [apiConfig, yourRole, refresh],
  );

  const getFieldStatus = useCallback(
    (fieldPath: string) => fieldStatuses[fieldPath],
    [fieldStatuses],
  );

  const isFieldStatus = useCallback(
    (fieldPath: string, status: FieldNegotiationStatus) =>
      fieldStatuses[fieldPath]?.status === status,
    [fieldStatuses],
  );

  const pendingCount = summary?.pending ?? 0;

  return {
    fieldStatuses,
    summary,
    yourRole,
    loading,
    error,
    refresh,
    submitProposal: submitProposalFn,
    acceptProposal: acceptProposalFn,
    rejectProposal: rejectProposalFn,
    getFieldStatus,
    isFieldStatus,
    pendingCount,
  };
}

// ---------------------------------------------------------------------------
// usePendingProposals — standalone hook for pending proposals badge
// ---------------------------------------------------------------------------

export function usePendingProposals(pollInterval = 30000): PendingProposalsResponse & {
  loading: boolean;
  refresh: () => Promise<void>;
} {
  const apiConfig = useVellumApi();
  const [data, setData] = useState<PendingProposalsResponse>({ proposals: [], count: 0 });
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await service.getPendingProposals(apiConfig);
      setData(result);
    } catch {
      // Silently fail for badge — not critical
    } finally {
      setLoading(false);
    }
  }, [apiConfig]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!pollInterval) return;
    const interval = setInterval(() => void refresh(), pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval, refresh]);

  return { ...data, loading, refresh };
}
