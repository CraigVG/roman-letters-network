import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'People',
  description:
    'Browse all 1,848 individuals in the Roman Letters corpus — senders, recipients, and those mentioned in correspondence. Filter by role, relationship, or search by name.',
};

export default function PeopleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
