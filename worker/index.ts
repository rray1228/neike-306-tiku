import handler from "vinext/server/app-router-entry";
import { handleVisits } from './visits.js';

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
    // Recovery was explicitly stopped by the owner. Keep all stored records,
    // but do not send requests to the old provider on navigation or API calls.
    if (new URL(request.url).pathname === '/api/visitor-recovery') return Response.json({ stopped: true }, { status: 410, headers: { 'Cache-Control': 'no-store' } });
    return handler.fetch(request, env, ctx);
  },
};

export default worker;
