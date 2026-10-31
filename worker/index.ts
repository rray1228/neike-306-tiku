import handler from "vinext/server/app-router-entry";
import { handleVisits } from './visits.js';
import { recoverVisitorSnapshot } from './visitor-recovery.js';

interface Env {
  ASSETS: Fetcher;
  DB?: { prepare(query: string): any; batch(statements: any[]): Promise<any[]> };
}

interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
  passThroughOnException(): void;
}

const worker = {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (new URL(request.url).pathname === '/api/visits') return handleVisits(request, env.DB);
    if (new URL(request.url).pathname === '/api/visitor-recovery') return recoverVisitorSnapshot(request, env.DB);
    // Keep recovery progressing as the site is used. The handler itself limits
    // external attempts to once per ten minutes and preserves the first valid
    // snapshot. This never blocks page rendering or replaces the original DB.
    if (env.DB && request.method === 'GET' && request.headers.get('Accept')?.includes('text/html')) {
      ctx.waitUntil(recoverVisitorSnapshot(new Request(new URL('/api/visitor-recovery', request.url)), env.DB).catch(() => undefined));
    }
    return handler.fetch(request, env, ctx);
  },
};

export default worker;
