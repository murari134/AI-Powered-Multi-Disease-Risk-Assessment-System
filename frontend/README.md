# MediRisk 2.0 Frontend Application

Next.js 16.3.6 App Router application with React 19.3.0, TypeScript 5.6.2, and Tailwind CSS 4.3.3.

## Features & Directory Layout
- `app/`: Next.js App Router routes and pages (`layout.tsx`, `page.tsx`).
- `components/`: Primitive & reusable UI components (shadcn/ui setup).
- `features/`: Domain-specific components (disease forms, analytics charts, hospital locator).
- `lib/`: Helper utilities and API clients.
- `hooks/`: React custom hooks.
- `stores/`: Zustand global state stores.
- `types/`: Shared TypeScript interfaces.

## Local Setup
```bash
npm install
npm run dev
```
Access application at `http://localhost:3000`.
