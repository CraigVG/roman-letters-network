import type { LetterFull, CollectionInfo } from './letters';
import type { AuthorFull } from './authors';

/* ------------------------------------------------------------------ */
/*  JSON-LD Types (subset of Schema.org)                              */
/* ------------------------------------------------------------------ */

interface JsonLd {
  '@context': string;
  '@type': string | string[];
  [key: string]: unknown;
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function stripHtml(text: string | null): string {
  if (!text) return '';
  return text.replace(/<[^>]*>/g, '').slice(0, 300);
}

/* ------------------------------------------------------------------ */
/*  JSON-LD Generators                                                */
/* ------------------------------------------------------------------ */

export function letterJsonLd(letter: LetterFull): JsonLd {
  const title = letter.quick_summary
    ? `Letter ${letter.letter_number}: ${letter.quick_summary}`
    : `Letter ${letter.letter_number} from ${letter.sender_name ?? 'Unknown'}`;

  return {
    '@context': 'https://schema.org',
    '@type': ['ScholarlyArticle', 'Message'],
    headline: title,
    name: title,
    description: stripHtml(letter.english_text),
    author: letter.sender_name
      ? {
          '@type': 'Person',
          name: letter.sender_name,
        }
      : undefined,
    recipient: letter.recipient_name
      ? {
          '@type': 'Person',
          name: letter.recipient_name,
        }
      : undefined,
    dateCreated: letter.year_approx ? `${letter.year_approx}` : undefined,
    inLanguage: ['la', 'en'],
    isPartOf: {
      '@type': 'Collection',
      name: letter.collection.replace(/_/g, ' '),
    },
  };
}

export function authorJsonLd(author: AuthorFull): JsonLd {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: author.name,
    alternateName: author.name_latin ?? undefined,
    description: author.bio ? stripHtml(author.bio) : undefined,
    birthDate: author.birth_year ? `${author.birth_year}` : undefined,
    deathDate: author.death_year ? `${author.death_year}` : undefined,
    jobTitle: author.role ?? undefined,
    homeLocation: author.location
      ? {
          '@type': 'Place',
          name: author.location,
          ...(author.lat && author.lon
            ? {
                geo: {
                  '@type': 'GeoCoordinates',
                  latitude: author.lat,
                  longitude: author.lon,
                },
              }
            : {}),
        }
      : undefined,
  };
}

export function collectionJsonLd(collection: CollectionInfo): JsonLd {
  return {
    '@context': 'https://schema.org',
    '@type': 'Collection',
    name: collection.title ?? collection.slug.replace(/_/g, ' '),
    author: {
      '@type': 'Person',
      name: collection.author_name,
    },
    description: `Collection of ${collection.letter_count ?? 'unknown number of'} late antique letters by ${collection.author_name}${collection.date_range ? ` (${collection.date_range})` : ''}.`,
    numberOfItems: collection.letter_count ?? undefined,
    temporalCoverage: collection.date_range ?? undefined,
  };
}
