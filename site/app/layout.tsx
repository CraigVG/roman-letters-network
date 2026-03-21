import type { Metadata } from 'next';
import { ThemeProvider } from 'next-themes';
import { NuqsAdapter } from 'nuqs/adapters/next/app';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { SearchDialog } from '@/components/search/SearchDialog';
import Script from 'next/script';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: {
    default: 'Roman Letters',
    template: '%s | Roman Letters',
  },
  description:
    'Mapping the communication networks of the late Roman Empire through 7,049 surviving letters (100-800 AD).',
  metadataBase: new URL('https://romanletters.org'),
  alternates: {
    canonical: '/',
  },
  icons: {
    icon: '/icon.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&display=swap"
          rel="stylesheet"
        />
        <meta name="citation_title" content="Roman Letters: A Digital Corpus of Late Antique Correspondence" />
        <meta name="citation_author" content="Vander Galien, Craig" />
        <meta name="citation_publication_date" content="2026/03/20" />
        <meta name="citation_online_date" content="2026/03/20" />
        <meta name="citation_doi" content="10.5281/zenodo.19142059" />
        <meta name="DC.title" content="Roman Letters: 7,049 Letters from the Late Roman World" />
        <meta name="DC.creator" content="Craig Vander Galien" />
        <meta name="DC.date" content="2026-03-20" />
        <meta name="DC.type" content="Dataset" />
        <meta name="DC.identifier" content="doi:10.5281/zenodo.19142059" />
        <meta name="DC.rights" content="CC BY 4.0" />
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-13HJNN8SST"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-13HJNN8SST');
          `}
        </Script>
        <Script id="microsoft-clarity" strategy="afterInteractive">
          {`
            (function(c,l,a,r,i,t,y){
              c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
              t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
              y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
            })(window, document, "clarity", "script", "vyxlldih06");
          `}
        </Script>
      </head>
      <body className="min-h-screen flex flex-col">
        <NuqsAdapter>
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <Header />
            <SearchDialog />
            <main className="flex-1">{children}</main>
            <Footer />
          </ThemeProvider>
        </NuqsAdapter>
      </body>
    </html>
  );
}
