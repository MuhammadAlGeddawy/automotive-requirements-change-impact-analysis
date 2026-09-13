# NASAQ Design System

This is the single source of truth for NASAQ's visual design. Every frontend component should be built to match this document. If a task's requirements conflict with this doc, this doc wins.

## Brand identity

NASAQ is an engineering intelligence tool for change impact analysis. The tone is precise, technical, and confident — not playful, not consumer-y. Think "professional engineering software," similar in spirit to tools like Linear or Vercel's dashboard, but with a green/cream identity instead of dark/purple.

**Naming note:** the underlying codebase/README refers to this project as "ENGYN." "NASAQ" is treated as the product-facing display name shown in the UI (logo, page title). Use "NASAQ" in all UI copy; "ENGYN" can remain as the repo/package name internally. If this is backwards, update this note and all UI copy accordingly before proceeding with any issue below.

## Color tokens

```
--color-brand-dark:      #0B3D2E   /* sidebar, header base */
--color-brand-dark-alt:  #0F2E24   /* gradient endpoint for sidebar (top→bottom, subtle) */
--color-bg-cream:        #F4F1E8   /* page background base */
--color-accent:          #1F9D6C   /* primary CTA green — must look distinct from brand-dark */
--color-accent-hover:    #17825A
--color-accent-disabled: #A9C4BA

--color-diff-prev-bg:    #FDF2F1   /* previous requirement card */
--color-diff-prev-border:#C0392B
--color-diff-next-bg:    #F1F8F4   /* updated requirement card */
--color-diff-next-border:#1F7A5C

--color-heading:         #14261F   /* headings on cream/glass */
--color-body:            #3E4C46   /* body text on cream/glass */
--color-muted:           #6B776F   /* secondary text — verify 4.5:1 contrast on cream */
--color-sidebar-text:    #F4F1E8   /* primary text on dark sidebar */
--color-sidebar-muted:   #9FB3A8   /* secondary text on dark sidebar — verify contrast */

--color-badge-high-bg:   #FDE8E8
--color-badge-high-text: #B91C1C
--color-badge-medium-bg: #FEF3E2
--color-badge-medium-text:#B45309
--color-badge-low-bg:    #E8F5EC
--color-badge-low-text:  #15803D

--color-flag-unlinked-bg:    #FEF9E7   /* GRAPH-UNLINKED traceability flag */
--color-flag-unlinked-border:#D4A017   /* dashed border, amber */
--color-flag-unlinked-text:  #92720C
```

## Glassmorphism — used selectively, not globally

**Apply glass to:** KPI/stat cards, the Impact Chain boxes, open dropdown menus, modals/popovers.

**Never apply glass to:** the sidebar, the data table, primary buttons, comparison card bodies, or any dense body text block. These need to stay solid and fully legible.

Glass surface recipe:
```
background: rgba(255, 255, 255, 0.55);
backdrop-filter: blur(16px) saturate(160%);
-webkit-backdrop-filter: blur(16px) saturate(160%);
border: 1px solid rgba(255, 255, 255, 0.4);
box-shadow: 0 8px 32px rgba(20, 60, 45, 0.12);
border-radius: 16px;
```

The page background should be a subtle gradient mesh (cream base with 2–3 soft, low-opacity sage-green and pale-gold blurred shapes) so glass panels have visible texture to refract. This mesh sits behind all content at a low z-index and must never overlay or block interaction with content in front of it — this was the cause of a full-page render break in a previous implementation, so any implementation must verify the mesh element has `pointer-events: none` and a z-index strictly below all content.

## Typography

- Headings: bold, `color-heading`, generous size steps (page title largest, section headers smaller).
- Eyebrow labels (e.g. "CHANGED REQUIREMENT", "CHANGE REQUEST"): uppercase, small size (~11–12px), letter-spacing ~0.05em, `color-muted` or brand green.
- Body text: `color-body`, comfortable line-height (1.5+).
- Metadata/IDs (SR-001, CR-001, SYS-001): monospace font, used consistently everywhere an artifact ID appears.

## Spacing & shape

- Border radius: 12–16px standard across cards, buttons, inputs.
- Card shadow (solid cards, not glass): `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)`.
- Consistent spacing scale: 4, 8, 12, 16, 24, 32, 48px — avoid arbitrary values.

## Iconography

Use an SVG-based icon set (Lucide recommended) rendered as React components — never icon-font ligatures. This avoids the font-loading failure mode that previously caused ligature names to render as visible text.

## Key components (reference for future issues)

1. **Sidebar** — solid dark green, sections: Engineering Artifacts (upload dropzone), Change Request (dropdown), Request Details (nested card), Assessment Engine (field).
2. **Stepper** — 3 steps: Select Change → Analyze Impact → Review Results, current step highlighted in accent green.
3. **Comparison cards** — Previous (red-tinted) vs Updated (green-tinted) requirement, with the specific changed value highlighted inline (not just full-sentence diffing).
4. **Analyze Impact button** — solid accent green, distinct hover/active/disabled/loading states.
5. **KPI stat cards** — glass surface, one per impact tier (High/Medium/Low/Total).
6. **Impact Chain** — glass surface boxes connected by arrows (SR-001 → SYS-001 → SWR-001 → TC-001).
7. **Impacted Artifacts table** — solid container, monospace artifact IDs, horizontal scroll on overflow rather than column-squeezing.
   - **Impact badge is compound**, not a single value: it shows an impact tier (High/Medium/Low, from the badge color tokens above) *and* an LLM classification (DIRECT / POTENTIAL / NO_IMPACT), e.g. "HIGH · DIRECT". Style as one pill: tier drives the background/text color, the LLM label appears after a middot separator in the same pill, slightly less bold.
   - **Confidence** shown as the number plus a small horizontal bar indicator reflecting its value.
   - **Traceability column** normally reads "Linked." When an artifact was surfaced by semantic search but has no formal traceability link (a real, documented detection feature — "GRAPH-UNLINKED"), render it as a distinct flag using the `flag-unlinked` tokens above: dashed border, amber background, a small warning icon, and the text "GRAPH-UNLINKED" — this needs to visually stand out from a normal "Linked" cell since it signals a data-quality issue worth a reviewer's attention, not routine information.
