'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { TimelineStep } from '@/lib/types';
import { AGENTS } from '@/lib/constants';

interface TimelineProps {
  steps: TimelineStep[];
}

export default function Timeline({ steps }: TimelineProps) {
  return (
    <div className="bg-bg-secondary rounded-xl border border-border-default p-4">
      <div className="flex items-center justify-between overflow-x-auto">
        {steps.map((step, index) => {
          const agent = AGENTS[step.agent];
          const isLast = index === steps.length - 1;

          return (
            <React.Fragment key={step.id}>
              {/* Step Node */}
              <div className="flex flex-col items-center min-w-[80px]">
                <motion.div
                  initial={false}
                  animate={{
                    scale: step.status === 'active' ? 1.2 : 1,
                    backgroundColor:
                      step.status === 'complete'
                        ? agent.color
                        : step.status === 'active'
                        ? agent.color
                        : '#21262d',
                  }}
                  className={`timeline-node w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors ${
                    step.status === 'complete' || step.status === 'active'
                      ? ''
                      : 'border-border-default'
                  }`}
                  style={{
                    borderColor:
                      step.status === 'complete' || step.status === 'active'
                        ? agent.color
                        : undefined,
                  }}
                >
                  {step.status === 'complete' ? (
                    <svg
                      className="w-4 h-4 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : step.status === 'active' ? (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                      className="w-3 h-3 rounded-full bg-white"
                    />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-text-secondary" />
                  )}
                </motion.div>

                {/* Label */}
                <div className="mt-2 text-center">
                  <p
                    className={`text-xs font-medium transition-colors ${
                      step.status === 'complete' || step.status === 'active'
                        ? 'text-text-primary'
                        : 'text-text-secondary'
                    }`}
                    style={{
                      color:
                        step.status === 'active' ? agent.color : undefined,
                    }}
                  >
                    {step.label}
                  </p>
                  <p className="text-[10px] text-text-secondary mt-0.5">
                    {agent.icon}
                  </p>
                </div>
              </div>

              {/* Connector Line */}
              {!isLast && (
                <div className="flex-1 h-0.5 mx-2 relative">
                  <div className="absolute inset-0 bg-border-default" />
                  <motion.div
                    initial={{ width: '0%' }}
                    animate={{
                      width:
                        step.status === 'complete'
                          ? '100%'
                          : step.status === 'active'
                          ? '50%'
                          : '0%',
                    }}
                    transition={{ duration: 0.5 }}
                    className="absolute inset-0"
                    style={{ backgroundColor: agent.color }}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
