// Purpose: Protect /app dashboard routes and handle authentication flow.
import { NextResponse, type NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const authCookie = request.cookies.get('ichnoscope_admin_auth');
  const isAuthenticated = Boolean(authCookie?.value);

  // If already authenticated and visiting /login, redirect to /app
  if (pathname === '/login' && isAuthenticated) {
    return NextResponse.redirect(new URL('/app', request.url));
  }

  // Protect /app routes
  if (pathname.startsWith('/app')) {
    // If not authenticated and REQUIRE_ADMIN_AUTH is true (or demo mode with strict check)
    if (!isAuthenticated && process.env.REQUIRE_ADMIN_AUTH === 'true') {
      const loginUrl = new URL('/login', request.url);
      loginUrl.searchParams.set('next', pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api).*)'],
};
