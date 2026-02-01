'use client';

import React from 'react';
import AgentCard from './AgentCard';
import { AGENTS } from '@/lib/constants';
import { AgentId, AgentStatus, AgentMessage } from '@/lib/types';

interface AgentFeedProps {
  agentStates: Record<AgentId, {
    status: AgentStatus;
    messages: AgentMessage[];
    streamingText?: string;
  }>;
}

export default function AgentFeed({ agentStates }: AgentFeedProps) {
  const agents = Object.values(AGENTS);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {agents.map((agent) => {
        const state = agentStates[agent.id] || {
          status: 'idle' as AgentStatus,
          messages: [],
          streamingText: '',
        };
        
        return (
          <AgentCard
            key={agent.id}
            agent={agent}
            status={state.status}
            messages={state.messages}
            isStreaming={state.status === 'working' && !!state.streamingText}
            streamingText={state.streamingText}
          />
        );
      })}
    </div>
  );
}
