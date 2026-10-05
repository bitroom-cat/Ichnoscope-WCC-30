import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/ThemeProvider';
import { DemoVideoPopup } from '@/components/DemoVideoPopup';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Ichnoscope — Incident Triage Dashboard',
  description:
    'Autonomous incident triage that reads the footprints a bug leaves in version history.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <body className="min-h-screen bg-canvas text-primary font-sans antialiased selection:bg-accent/20 selection:text-accent">
        <ThemeProvider>
          {children}
          <DemoVideoPopup />
        </ThemeProvider>
      </body>
    </html>
  );
}
