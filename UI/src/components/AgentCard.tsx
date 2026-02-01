'use client';

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';
import { Agent, AgentStatus, AgentMessage } from '@/lib/types';

interface AgentCardProps {
  agent: Agent;
  status: AgentStatus;
  messages: AgentMessage[];
  isStreaming?: boolean;
  streamingText?: string;
}

export default function AgentCard({
  agent,
  status,
  messages,
  isStreaming = false,
  streamingText = '',
}: AgentCardProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const getStatusIcon = () => {
    switch (status) {
      case 'working':
        return <Loader2 className="w-4 h-4 animate-spin" style={{ color: agent.color }} />;
      case 'complete':
        return <CheckCircle2 className="w-4 h-4" style={{ color: agent.color }} />;
      default:
        return <Circle className="w-4 h-4 text-text-secondary" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'working':
        return 'Working...';
      case 'complete':
        return 'Complete';
      default:
        return 'Idle';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`agent-card ${agent.glowClass} ${status === 'working' ? 'active' : ''} 
        bg-bg-secondary rounded-xl border border-border-default overflow-hidden flex flex-col h-[280px]`}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-border-default"
        style={{ borderTopColor: status === 'working' ? agent.color : undefined }}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{agent.icon}</span>
          <div>
            <h3 className="font-semibold text-sm" style={{ color: agent.color }}>
              {agent.name}
            </h3>
            <p className="text-xs text-text-secondary">{agent.role}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="text-xs text-text-secondary">{getStatusText()}</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && status === 'idle' && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-text-secondary text-center">
              Waiting for audit to start...
            </p>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="message-bubble"
            >
              <MessageBubble message={message} agentColor={agent.color} />
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Streaming Text */}
        {isStreaming && streamingText && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-sm text-text-primary"
          >
            {streamingText}
            <span className="typing-cursor" style={{ backgroundColor: agent.color }}></span>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </motion.div>
  );
}

// Message bubble component
function MessageBubble({ message, agentColor }: { message: AgentMessage; agentColor: string }) {
  if (message.type === 'vulnerability') {
    return (
      <div className="bg-agent-attacker/10 border border-agent-attacker/30 rounded-lg p-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium text-agent-attacker">⚠️ VULNERABILITY</span>
        </div>
        <p className="text-sm text-text-primary whitespace-pre-wrap">{message.content}</p>
      </div>
    );
  }

  if (message.type === 'fix') {
    return (
      <div className="bg-agent-defender/10 border border-agent-defender/30 rounded-lg p-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium text-agent-defender">🔧 FIX PROPOSED</span>
        </div>
        <p className="text-sm text-text-primary whitespace-pre-wrap">{message.content}</p>
      </div>
    );
  }

  if (message.type === 'verdict') {
    const lines = message.content.split('\n');
    const verdictLines = lines.filter((line) => line.trim().startsWith('- '));
    const statuses = verdictLines
      .map((line) => {
        const match = line.match(/:\s*(FIXED|REJECTED)\b/i);
        return match ? match[1].toLowerCase() : null;
      })
      .filter(Boolean) as Array<'fixed' | 'rejected'>;

    const hasFixed = statuses.includes('fixed');
    const hasRejected = statuses.includes('rejected');

    const verdict: 'approved' | 'rejected' | 'partial' =
      hasFixed && hasRejected ? 'partial' : hasFixed ? 'approved' : 'rejected';

    const isApproved = verdict === 'approved';
    const isPartial = verdict === 'partial';
    return (
      <div
        className={`rounded-lg p-3 ${
          isApproved
            ? 'bg-agent-defender/10 border border-agent-defender/30'
            : isPartial
            ? 'bg-agent-arbiter/10 border border-agent-arbiter/30'
            : 'bg-agent-attacker/10 border border-agent-attacker/30'
        }`}
      >
        <div className="flex items-center gap-2 mb-1">
          <span
            className={`text-xs font-medium ${
              isApproved
                ? 'text-agent-defender'
                : isPartial
                ? 'text-agent-arbiter'
                : 'text-agent-attacker'
            }`}
          >
            {isApproved
              ? '✅ VERDICT: APPROVED'
              : isPartial
              ? '⚠️ VERDICT: PARTIAL'
              : '❌ VERDICT: REJECTED'}
          </span>
        </div>
        <p className="text-sm text-text-primary whitespace-pre-wrap">{message.content}</p>
      </div>
    );
  }

  // Default text message
  return (
    <div className="text-sm text-text-primary whitespace-pre-wrap">
      {message.content}
    </div>
  );
}
