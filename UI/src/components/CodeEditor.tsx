'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Play, Code2, FileCode, Loader2 } from 'lucide-react';
import { SAMPLE_VULNERABLE_CODE } from '@/lib/constants';

interface CodeEditorProps {
  onSubmit: (code: string, language: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const LANGUAGES = [
  { id: 'python', name: 'Python', icon: '🐍' },
  { id: 'javascript', name: 'JavaScript', icon: '📜' },
  { id: 'typescript', name: 'TypeScript', icon: '💙' },
  { id: 'go', name: 'Go', icon: '🐹' },
  { id: 'java', name: 'Java', icon: '☕' },
];

const SAMPLE_OPTIONS = [
  { id: 'python_sql', label: 'SQL Injection', icon: '💉' },
  { id: 'python_xss', label: 'XSS Attack', icon: '🔓' },
  { id: 'python_path', label: 'Path Traversal', icon: '📁' },
  { id: 'javascript_xss', label: 'DOM XSS', icon: '🌐' },
];

export default function CodeEditor({ onSubmit, isLoading, disabled }: CodeEditorProps) {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [lineNumbers, setLineNumbers] = useState<number[]>([1]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Update line numbers when code changes
  useEffect(() => {
    const lines = code.split('\n').length;
    setLineNumbers(Array.from({ length: Math.max(lines, 10) }, (_, i) => i + 1));
  }, [code]);

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCode(e.target.value);
  };

  const loadSample = (sampleId: string) => {
    const sampleCode = SAMPLE_VULNERABLE_CODE[sampleId as keyof typeof SAMPLE_VULNERABLE_CODE];
    if (sampleCode) {
      setCode(sampleCode);
      // Set language based on sample
      if (sampleId.startsWith('javascript')) {
        setLanguage('javascript');
      } else {
        setLanguage('python');
      }
    }
  };

  const handleSubmit = () => {
    if (code.trim() && !isLoading && !disabled) {
      onSubmit(code, language);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Handle Tab key for indentation
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = textareaRef.current?.selectionStart || 0;
      const end = textareaRef.current?.selectionEnd || 0;
      const newCode = code.substring(0, start) + '  ' + code.substring(end);
      setCode(newCode);
      // Move cursor after the tab
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 2;
        }
      }, 0);
    }
    // Submit on Ctrl/Cmd + Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="bg-bg-secondary rounded-xl border border-border-default overflow-hidden">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 border-b border-border-default bg-bg-tertiary/50">
        {/* Language Selector */}
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-text-secondary" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isLoading || disabled}
            className="bg-bg-tertiary text-text-primary text-sm rounded-lg px-3 py-1.5 border border-border-default focus:outline-none focus:border-agent-attacker disabled:opacity-50"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.id} value={lang.id}>
                {lang.icon} {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Sample Code Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-text-secondary hidden sm:inline">Load Sample:</span>
          {SAMPLE_OPTIONS.map((sample) => (
            <button
              key={sample.id}
              onClick={() => loadSample(sample.id)}
              disabled={isLoading || disabled}
              className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-lg bg-bg-tertiary border border-border-default hover:border-agent-attacker hover:text-agent-attacker transition-colors disabled:opacity-50 disabled:hover:border-border-default disabled:hover:text-text-primary"
            >
              <span>{sample.icon}</span>
              <span className="hidden sm:inline">{sample.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Code Editor Area */}
      <div className="relative flex">
        {/* Line Numbers */}
        <div className="flex-shrink-0 py-4 px-2 bg-bg-tertiary/30 border-r border-border-default select-none">
          {lineNumbers.map((num) => (
            <div
              key={num}
              className="text-right text-xs text-text-secondary font-mono leading-6 px-2"
            >
              {num}
            </div>
          ))}
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={code}
          onChange={handleCodeChange}
          onKeyDown={handleKeyDown}
          disabled={isLoading || disabled}
          placeholder="Paste your code here to analyze for security vulnerabilities..."
          className="flex-1 min-h-[300px] p-4 bg-transparent text-text-primary font-mono text-sm leading-6 resize-none focus:outline-none placeholder:text-text-secondary/50 disabled:opacity-50"
          spellCheck={false}
        />
      </div>

      {/* Submit Button */}
      <div className="flex items-center justify-between p-4 border-t border-border-default bg-bg-tertiary/30">
        <div className="text-xs text-text-secondary">
          <kbd className="px-1.5 py-0.5 rounded bg-bg-tertiary border border-border-default text-text-secondary font-mono">
            Ctrl
          </kbd>
          {' + '}
          <kbd className="px-1.5 py-0.5 rounded bg-bg-tertiary border border-border-default text-text-secondary font-mono">
            Enter
          </kbd>
          {' to submit'}
        </div>
        <button
          onClick={handleSubmit}
          disabled={!code.trim() || isLoading || disabled}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-agent-attacker text-white font-medium hover:bg-agent-attacker/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-agent-attacker"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Auditing...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Audit Code</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
