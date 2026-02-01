'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '@/components/Header';
import CodeEditor from '@/components/CodeEditor';
import AgentFeed from '@/components/AgentFeed';
import Timeline from '@/components/Timeline';
import SecurityReport from '@/components/SecurityReport';
import { useAudit } from '@/hooks/useAudit';
import { RotateCcw, Zap, Shield, Users, FileSearch } from 'lucide-react';

export default function Home() {
  const {
    status,
    agents,
    timeline,
    report,
    verdict,
    counts,
    error,
    isLoading,
    startAudit,
    resetState,
  } = useAudit();

  const handleSubmit = (code: string, language: string) => {
    startAudit(code, language);
  };

  const handleReset = () => {
    resetState();
  };

  const showAgentFeed = status !== 'idle';
  const showReport = report !== null;

  return (
    <div className="min-h-screen bg-bg-primary">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section - Only show when idle */}
        <AnimatePresence mode="wait">
          {status === 'idle' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center mb-8"
            >
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                <span className="text-agent-attacker">AI Hackers</span>{' '}
                <span className="text-text-primary">Attack Your Code</span>
              </h2>
              <p className="text-text-secondary text-lg max-w-2xl mx-auto mb-6">
                Multi-agent system where AI attackers find vulnerabilities, defenders patch them, 
                and arbiters validate the fixes through adversarial debate.
              </p>
              
              {/* Feature badges */}
              <div className="flex flex-wrap justify-center gap-4 mb-8">
                <FeatureBadge icon={<Zap className="w-4 h-4" />} text="Real-time Analysis" />
                <FeatureBadge icon={<Shield className="w-4 h-4" />} text="OWASP Patterns" />
                <FeatureBadge icon={<Users className="w-4 h-4" />} text="4 AI Agents" />
                <FeatureBadge icon={<FileSearch className="w-4 h-4" />} text="Verified Fixes" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 p-4 rounded-lg bg-agent-attacker/10 border border-agent-attacker/30 text-agent-attacker"
            >
              <p className="font-medium">⚠️ {error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Code Editor */}
        <motion.div
          layout
          className="mb-6"
        >
          <CodeEditor
            onSubmit={handleSubmit}
            isLoading={isLoading}
            disabled={isLoading}
          />
        </motion.div>

        {/* Timeline - Show when audit is running or complete */}
        <AnimatePresence>
          {showAgentFeed && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-text-primary">Audit Progress</h3>
                {status === 'complete' && (
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg bg-bg-tertiary border border-border-default hover:border-agent-reporter transition-colors"
                  >
                    <RotateCcw className="w-4 h-4" />
                    <span>New Audit</span>
                  </button>
                )}
              </div>
              <Timeline steps={timeline} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Agent Feed - Show when audit is running or complete */}
        <AnimatePresence>
          {showAgentFeed && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-6"
            >
              <h3 className="text-lg font-semibold text-text-primary mb-4">Agent Activity</h3>
              <AgentFeed agentStates={agents} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Security Report - Show when complete */}
        <AnimatePresence>
          {showReport && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-6"
            >
              <h3 className="text-lg font-semibold text-text-primary mb-4">Security Report</h3>
              <SecurityReport
                report={report}
                verdict={verdict || undefined}
                vulnerabilitiesCount={counts?.total ?? 0}
                fixedCount={counts?.fixed ?? 0}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-text-secondary">
          <p>
            Built with{' '}
            <span className="text-agent-attacker">OpenAI Agents SDK</span>
            {' '}for{' '}
            <span className="text-text-primary font-medium">OpenAI Hackathon 2026</span>
          </p>
          <p className="mt-2">
            Track 3: Multi-Agent Systems & Workflows
          </p>
        </footer>
      </main>
    </div>
  );
}

// Feature badge component
function FeatureBadge({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-bg-secondary border border-border-default">
      <span className="text-agent-reporter">{icon}</span>
      <span className="text-sm text-text-secondary">{text}</span>
    </div>
  );
}
