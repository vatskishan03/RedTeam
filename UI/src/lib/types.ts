// Agent types
export type AgentId = 'attacker' | 'defender' | 'arbiter' | 'reporter';

export type AgentStatus = 'idle' | 'working' | 'complete';

export interface Agent {
  id: AgentId;
  name: string;
  role: string;
  icon: string;
  color: string;
  colorClass: string;
  glowClass: string;
}

export interface AgentMessage {
  id: string;
  agentId: AgentId;
  type: 'text' | 'vulnerability' | 'fix' | 'verdict' | 'report';
  content: string;
  timestamp: number;
}

// Vulnerability types
export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface Vulnerability {
  id: string;
  type: string;
  severity: Severity;
  location: string;
  description: string;
  exploit?: string;
  fix?: string;
  status: 'found' | 'fixing' | 'fixed' | 'verified';
}

// Audit status
export type AuditStatus = 
  | 'idle'
  | 'scanning'
  | 'found_vulnerabilities'
  | 'proposing_fixes'
  | 're_attacking'
  | 'validating'
  | 'generating_report'
  | 'complete';

export interface AuditState {
  status: AuditStatus;
  code: string;
  language: string;
  agents: Record<AgentId, {
    status: AgentStatus;
    messages: AgentMessage[];
  }>;
  vulnerabilities: Vulnerability[];
  verdict?: 'approved' | 'rejected' | 'partial';
  report?: string;
}

// Timeline step
export interface TimelineStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete';
  agent: AgentId;
}

// SSE Event types
export interface SSEEvent {
  type: 'agent_start' | 'agent_message' | 'agent_complete' | 'vulnerability' | 'fix' | 'verdict' | 'report' | 'done';
  agent?: AgentId;
  content?: string;
  data?: Record<string, unknown>;
}
