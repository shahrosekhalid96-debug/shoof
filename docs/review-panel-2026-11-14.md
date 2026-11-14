# Shoof launch review: panel decision

**Panel verdict: APPROVE WITH FIXES.** UI, UX and QA agree the core works: a phone first-timer downloads a post in 11 taps, and the visuals look professional. The blockers are first impressions. Shoofy covers the design and gives desktop tips on phones. Photos land on the headline. Size tiles open a blank page. Arabic mode mirrors English punctuation wrongly. All are small fixes; share after them.

## Must fix before sharing
1. Shoofy's bubble covers the canvas (D10, P10). Anchor it in the gutter or above the pages bar, covering at most 15% of the page.
2. Phone tips say "Ctrl+D" and "hold Shift". Use touch-only tips on phones.
3. Panel tips fire on the home screen (D14). Fire them only while that panel is open.
4. On phones Shoofy overlaps content and sheets. Dock it at 40px above the tab bar and hide it while a sheet is open.
5. After a phone upload the sheet stays open and the photo covers the headline. Close the sheet; fill an empty frame or a spot with no text.
6. A size tile gives a blank page on phones (verified). Open Templates filtered to that size, with Blank first.
7. QA: English text in the Arabic UI shows "?What will you design today" and "!Hi, I am Shoofy". Set `dir="auto"` on English fallback text.
8. Phone first-visit tips mention the "left panel" and dragging. Use phone wording and one tip.

## Nice to have
1. One scrolling row of chips.
2. Styled selects and one heading style.
3. New as the primary button.
4. Plainer AI note; shorter phone placeholders.
5. Text-edit Done button.
6. Label or drop the Style icon row.
7. Fewer home starting points.
8. Rename the "size" row.
9. Name downloads after the design.
10. A "photo covers text" check.
11. Edge fades on scroll rows.
12. Logo hints and minimum weight.
13. Elements search wording and icon size.
14. QA: focus the bubble when it opens by keyboard.

## Dropped
None. Every High and Medium row was confirmed. Reduced motion, hide persistence and Esc focus pass.
