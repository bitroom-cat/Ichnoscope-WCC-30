import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'ichnoscope-web',
    version: '2.0.0',
    mode: 'sample-standalone-website',
    track: '01 Agentic AI (WCC Launchpad 30)',
  });
}
