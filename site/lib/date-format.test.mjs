import assert from 'node:assert/strict';

import {
  formatApproxYear,
  formatYear,
  formatYearRange,
} from './date-format.ts';

assert.equal(formatYear(-60), '60 BC');
assert.equal(formatYear(60), '60 AD');
assert.equal(formatYear(null), null);

assert.equal(formatApproxYear(-54), 'c. 54 BC');
assert.equal(formatApproxYear(595), 'c. 595 AD');
assert.equal(formatApproxYear(undefined), null);

assert.equal(formatYearRange(-60, -54), '60-54 BC');
assert.equal(formatYearRange(-106, -43), '106-43 BC');
assert.equal(formatYearRange(100, 800), '100-800 AD');
assert.equal(formatYearRange(-5, 5), '5 BC-5 AD');
assert.equal(formatYearRange(null, -43), '?-43 BC');
assert.equal(formatYearRange(-106, null), '106 BC-?');
