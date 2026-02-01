'use client';

import React from 'react';
import { Shield, Github, ExternalLink } from 'lucide-react';

export default function Header() {
  return (
    <header className="border-b border-border-default bg-bg-secondary/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-agent-attacker/20 border border-agent-attacker/30">
              <Shield className="w-5 h-5 text-agent-attacker" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-text-primary flex items-center gap-2">
                <span className="text-agent-attacker">Red Team</span>
                <span>Code Auditor</span>
              </h1>
              <p className="text-xs text-text-secondary hidden sm:block">
                AI hackers attack your code before real ones do
              </p>
            </div>
          </div>

          {/* Links */}
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/vatskishan03/RedTeam"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              <Github className="w-4 h-4" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-bg-tertiary border border-border-default">
              <span className="w-2 h-2 rounded-full bg-agent-defender animate-pulse"></span>
              <span className="text-xs text-text-secondary">Multi-Agent System</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
