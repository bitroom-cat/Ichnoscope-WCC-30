import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    message: 'Ichnoscope Dashboard API route ready. Client runs are cached and interactive in the sample UI.',
  });
}
