import Link from 'next/link';
import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav>
          <Link href="/">Home</Link>
          <Link href="/experiments">Experiments</Link>
          <Link href="/experiments/new">New Experiment</Link>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
