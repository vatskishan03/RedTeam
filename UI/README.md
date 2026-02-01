# 🔴 Red Team Code Auditor - UI

A real-time visualization frontend for the Adversarial Red Team Code Auditor multi-agent system.

## Features

- **Real-time Agent Activity**: Watch AI agents work in real-time as they attack, defend, and validate code
- **Live Timeline**: Visual progress indicator showing audit stages
- **Code Editor**: Monaco-style editor with syntax highlighting and sample code
- **Security Reports**: Downloadable audit reports with vulnerability details

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS with custom dark theme
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Real-time**: Server-Sent Events (SSE)

## Getting Started

### Install dependencies

```bash
cd UI
npm install
```

### Run development server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the UI.

### Build for production

```bash
npm run build
npm start
```

## Project Structure

```
UI/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Root layout with fonts/metadata
│   │   ├── page.tsx         # Main page
│   │   ├── globals.css      # Global styles + Tailwind
│   │   └── api/
│   │       └── audit/
│   │           └── route.ts # SSE endpoint
│   │
│   ├── components/
│   │   ├── Header.tsx       # Top navigation
│   │   ├── CodeEditor.tsx   # Code input with samples
│   │   ├── AgentCard.tsx    # Individual agent panel
│   │   ├── AgentFeed.tsx    # 2x2 agent grid
│   │   ├── Timeline.tsx     # Progress timeline
│   │   └── SecurityReport.tsx # Final report view
│   │
│   ├── hooks/
│   │   ├── useAudit.ts      # SSE connection + state management
│   │   └── useTypewriter.ts # Typing animation
│   │
│   └── lib/
│       ├── types.ts         # TypeScript types
│       └── constants.ts     # Agents, colors, sample code
│
├── tailwind.config.ts       # Custom theme + animations
├── next.config.js
├── tsconfig.json
└── package.json
```

## Integration with MAS Backend

The UI connects to the Multi-Agent System via the `/api/audit` SSE endpoint.

To connect to the actual MAS backend:

1. Update `src/app/api/audit/route.ts`
2. Forward requests to your Python MAS backend
3. Stream responses back as SSE events

### SSE Event Format

```typescript
// Agent starts working
{ type: 'agent_start', agent: 'attacker' }

// Agent sends a message
{ type: 'agent_message', agent: 'attacker', content: '...', messageType: 'text' | 'vulnerability' | 'fix' | 'verdict' }

// Agent completes
{ type: 'agent_complete', agent: 'attacker' }

// Timeline update
{ type: 'timeline_update', step: 'scan', status: 'active' | 'complete' }

// Final verdict
{ type: 'verdict', verdict: 'approved' | 'rejected' | 'partial' }

// Final report
{ type: 'report', content: '# Security Report...' }

// Audit complete
{ type: 'done' }
```

## License

MIT
