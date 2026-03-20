'use client';

/**
 * LetterText - formats raw letter text into styled HTML.
 *
 * Handles:
 *  - Structured headers (From: / To: / Date: / Context:) at the top
 *  - Double-newline paragraph splitting into <p> tags
 *  - Single-newline line breaks into <br> tags
 *  - Inline [Context: ...] and [Note: ...] annotations
 */

interface LetterTextProps {
  text: string;
}

/* Lines that look like metadata headers at the very top of a letter */
const HEADER_KEYS = /^(From|To|Date|Context|Subject|Place|Written at|Addressed to|Sender|Recipient|Written from):\s/i;

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Style inline bracket annotations like [Context: ...] or [Note: ...]
 */
function styleInlineAnnotations(html: string): string {
  return html.replace(
    /\[([^\]]{3,})\]/g,
    '<span class="letter-annotation">[$1]</span>',
  );
}

/**
 * Parse the text into a header block (if present) and body paragraphs.
 */
function parseLetterText(raw: string): { headerLines: string[]; body: string } {
  const lines = raw.split('\n');
  const headerLines: string[] = [];
  let bodyStartIndex = 0;

  // Walk through the initial lines to find contiguous header block
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Empty line after headers ends the header block
    if (line === '' && headerLines.length > 0) {
      bodyStartIndex = i + 1;
      break;
    }

    // Check if this line looks like a header field
    if (HEADER_KEYS.test(line)) {
      headerLines.push(line);
    } else {
      // Not a header line - everything is body
      bodyStartIndex = i;
      break;
    }
  }

  // If we collected headers but never hit a blank line, the rest is body
  const body = lines.slice(bodyStartIndex).join('\n').trim();
  return { headerLines, body };
}

/**
 * Convert body text into HTML paragraphs.
 * Double newlines become paragraph breaks; single newlines become <br>.
 */
function bodyToHtml(body: string): string {
  // Split on double newlines (with optional whitespace between)
  const paragraphs = body.split(/\n\s*\n/).filter((p) => p.trim());

  return paragraphs
    .map((para) => {
      const escaped = escapeHtml(para.trim());
      // Convert remaining single newlines to <br>
      const withBreaks = escaped.replace(/\n/g, '<br>');
      // Style inline annotations
      const styled = styleInlineAnnotations(withBreaks);
      return `<p>${styled}</p>`;
    })
    .join('\n');
}

/**
 * Build HTML for the header metadata block.
 */
function headerToHtml(headerLines: string[]): string {
  if (headerLines.length === 0) return '';

  const rows = headerLines.map((line) => {
    const colonIdx = line.indexOf(':');
    const key = escapeHtml(line.slice(0, colonIdx).trim());
    const value = escapeHtml(line.slice(colonIdx + 1).trim());
    return `<div class="letter-header-row"><span class="letter-header-key">${key}:</span> <span class="letter-header-value">${value}</span></div>`;
  });

  return `<div class="letter-header-block">${rows.join('\n')}</div>`;
}

export function LetterText({ text }: LetterTextProps) {
  const { headerLines, body } = parseLetterText(text);
  const html = headerToHtml(headerLines) + bodyToHtml(body);

  return (
    <div
      className="prose-letter"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
