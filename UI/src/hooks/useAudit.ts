'use client';

import { useState, useCallback, useRef } from 'react';
import { AgentId, AgentStatus, AgentMessage, TimelineStep, AuditStatus } from '@/lib/types';
import { TIMELINE_STEPS } from '@/lib/constants';

interface AgentState {
  status: AgentStatus;
  messages: AgentMessage[];
  streamingText: string;
}

interface AuditHookState {
  status: AuditStatus;
  agents: Record<AgentId, AgentState>;
  timeline: TimelineStep[];
  report: string | null;
  verdict: 'approved' | 'rejected' | 'partial' | null;
  counts: { total: number; fixed: number; rejected: number } | null;
  error: string | null;
}

const initialAgentState: AgentState = {
  status: 'idle',
  messages: [],
  streamingText: '',
};

const initialState: AuditHookState = {
  status: 'idle',
  agents: {
    attacker: { ...initialAgentState },
    defender: { ...initialAgentState },
    arbiter: { ...initialAgentState },
    reporter: { ...initialAgentState },
  },
  timeline: TIMELINE_STEPS.map(step => ({ ...step })),
  report: null,
  verdict: null,
  counts: null,
  error: null,
};

export function useAudit() {
  const [state, setState] = useState<AuditHookState>(initialState);
  const eventSourceRef = useRef<EventSource | null>(null);
  const runIdRef = useRef<string | null>(null);

  const resetState = useCallback(() => {
    setState(initialState);
  }, []);

  const updateAgentStatus = useCallback((agentId: AgentId, status: AgentStatus) => {
    setState(prev => ({
      ...prev,
      agents: {
        ...prev.agents,
        [agentId]: {
          ...prev.agents[agentId],
          status,
        },
      },
    }));
  }, []);

  const addAgentMessage = useCallback((agentId: AgentId, message: Omit<AgentMessage, 'id' | 'timestamp' | 'agentId'>) => {
    const newMessage: AgentMessage = {
      ...message,
      id: `${agentId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      agentId,
      timestamp: Date.now(),
    };
    
    setState(prev => ({
      ...prev,
      agents: {
        ...prev.agents,
        [agentId]: {
          ...prev.agents[agentId],
          messages: [...prev.agents[agentId].messages, newMessage],
          streamingText: '',
        },
      },
    }));
  }, []);

  const updateStreamingText = useCallback((agentId: AgentId, text: string) => {
    setState(prev => ({
      ...prev,
      agents: {
        ...prev.agents,
        [agentId]: {
          ...prev.agents[agentId],
          streamingText: text,
        },
      },
    }));
  }, []);

  const updateTimelineStep = useCallback((stepId: string, status: 'pending' | 'active' | 'complete') => {
    setState(prev => ({
      ...prev,
      timeline: prev.timeline.map(step => 
        step.id === stepId ? { ...step, status } : step
      ),
    }));
  }, []);

  const startAudit = useCallback(async (code: string, language: string) => {
    // Reset state
    resetState();
    setState(prev => ({ ...prev, status: 'scanning' }));
    runIdRef.current = null;

    try {
      // Close any existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Start SSE connection
      const params = new URLSearchParams({ code, language });
      const eventSource = new EventSource(`/api/audit?${params.toString()}`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleSSEEvent(data);
        } catch (e) {
          console.error('Failed to parse SSE event:', e);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        eventSource.close();
        setState(prev => ({
          ...prev,
          status: 'complete',
          error: 'Connection lost. Please try again.',
        }));
      };

    } catch (error) {
      console.error('Failed to start audit:', error);
      setState(prev => ({
        ...prev,
        status: 'idle',
        error: 'Failed to start audit. Please try again.',
      }));
    }
  }, [resetState]);

  const handleSSEEvent = useCallback((event: any) => {
    // Guard against stale events (e.g., if a previous SSE stream lingers).
    if (event?.run_id) {
      if (!runIdRef.current) {
        runIdRef.current = String(event.run_id);
      } else if (String(event.run_id) !== runIdRef.current) {
        return;
      }
    }

    switch (event.type) {
      case 'agent_start':
        updateAgentStatus(event.agent as AgentId, 'working');
        break;

      case 'agent_chunk':
        updateStreamingText(event.agent as AgentId, event.content);
        break;

      case 'agent_message':
        updateAgentStatus(event.agent as AgentId, 'working');
        addAgentMessage(event.agent as AgentId, {
          type: event.messageType || 'text',
          content: event.content,
        });
        break;

      case 'agent_complete':
        updateAgentStatus(event.agent as AgentId, 'complete');
        break;

      case 'timeline_update':
        updateTimelineStep(event.step, event.status);
        break;

      case 'status_update':
        setState(prev => ({ ...prev, status: event.status }));
        break;

      case 'verdict':
        setState(prev => ({ 
          ...prev, 
          verdict: event.verdict,
          counts: event.counts ? {
            total: Number(event.counts.total) || 0,
            fixed: Number(event.counts.fixed) || 0,
            rejected: Number(event.counts.rejected) || 0,
          } : prev.counts,
        }));
        break;

      case 'report':
        setState(prev => ({ ...prev, report: event.content }));
        break;

      case 'done':
        setState(prev => ({ ...prev, status: 'complete' }));
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }
        break;

      case 'error':
        setState(prev => ({
          ...prev,
          status: 'complete',
          error: event.message,
        }));
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }
        break;
    }
  }, [updateAgentStatus, updateStreamingText, addAgentMessage, updateTimelineStep]);

  const stopAudit = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setState(prev => ({ ...prev, status: 'complete' }));
  }, []);

  return {
    ...state,
    isLoading: state.status !== 'idle' && state.status !== 'complete',
    startAudit,
    stopAudit,
    resetState,
  };
}
