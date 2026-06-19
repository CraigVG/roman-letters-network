import type { Metadata } from 'next';
import { CORPUS, formatCount } from '@/lib/corpus';

export const metadata: Metadata = {
  title: 'People',
  description: `Browse all ${formatCount(CORPUS.totalAuthors)} individuals in the Roman Letters corpus - senders, recipients, and those mentioned in correspondence. Filter by role, relationship, or search by name.`,
};

export default function PeopleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
