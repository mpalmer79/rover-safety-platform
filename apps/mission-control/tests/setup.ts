import "@testing-library/jest-dom/vitest";
import { expect } from "vitest";
import { toHaveNoViolations } from "jest-axe";

// Extend vitest's expect with jest-axe's toHaveNoViolations matcher
// so accessibility tests can assert axe runs cleanly against
// rendered DOM.
expect.extend(toHaveNoViolations);
