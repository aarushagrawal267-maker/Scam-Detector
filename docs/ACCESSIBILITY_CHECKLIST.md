# Accessibility Checklist

**Who we design for:** older adults who may have weak eyesight, shaky hands, low confidence with technology,
limited English, an old Android phone and slow mobile internet.

**How to use this list:** go through every row before each release and before every user test. Mark ✅ / ❌ and
write down what you found. Automated tools catch only part of the problems. The final test is always real
users (`PILOT_PROTOCOL.md`).

Numbers below come from the Web Content Accessibility Guidelines (WCAG 2.2). Where we go stricter than WCAG,
because our users are older, the row says so. Verify against the current WCAG version at w3.org/WAI.

---

## 1. Reading and seeing

| ✅/❌ | Item | Target | How to test it |
|---|---|---|---|
| | Base font size | Body text **≥ 18 px** (we aim for 20 px); buttons and verdict text larger (**≥ 24 px**); verdict headline ≥ 28 px | DevTools → Inspect element → *Computed* → `font-size` |
| | Line spacing | `line-height` ≥ **1.5** for body text; short paragraphs | DevTools *Computed* panel |
| | Text contrast | **≥ 7:1** for body text (WCAG AAA; stricter than the AA minimum of 4.5:1). Large text (≥ 24 px, or ≥ 18.7 px bold) at least 4.5:1 | **WebAIM Contrast Checker** (webaim.org/resources/contrastchecker) with your exact hex colours; Lighthouse *Accessibility* audit |
| | Non-text contrast | Button borders, input box outlines and focus rings **≥ 3:1** against the background | WebAIM Contrast Checker |
| | Zoom | Page still usable at **200% browser zoom**: no text cut off, no overlapping (WCAG 1.4.4) | Ctrl/Cmd + `+` to 200% in Chrome; on a phone, Android *Settings → Display → Font size* at maximum |
| | Reflow | No sideways scrolling at **320 px** width (WCAG 1.4.10) | DevTools → *Toggle device toolbar* → set width to 320 |
| | Fonts | System fonts, or a self-hosted font with full **Devanagari** support. Check that Hindi matras (ि ी ु ू) render correctly | View the Hindi pages on a real Android phone and on a laptop |
| | No all-caps paragraphs | Capitals only for short labels (e.g., "SCAM") | Read through each page |

## 2. Colour and the verdict

| ✅/❌ | Item | Target | How to test it |
|---|---|---|---|
| | Never colour alone (WCAG 1.4.1) | On the website every verdict has **shape + WORD + colour**: octagon SCAM / triangle SUSPICIOUS / circle LIKELY SAFE (Hindi: धोखा / संदिग्ध / शायद सुरक्षित). The shapes are inline SVG and also appear in the guide legend, the stats page and the printable guide. The chat bot and the API still send the emoji 🔴 / 🟡 / 🟢 + WORD | Switch the screen to greyscale: Android *Settings → Accessibility → Colour correction / Greyscale* (names vary by phone). Can you still tell the verdicts apart? |
| | Colour-blind safe | Red and green verdicts differ by **word and shape** (octagon vs circle), not just hue | Chrome DevTools → ⋮ → *More tools → Rendering* → **Emulate vision deficiencies** (protanopia, deuteranopia, tritanopia, achromatopsia) |
| | Green is never "safe" | Green text always reads "LIKELY SAFE, not a guarantee" | Read every green-result screen and bot reply |
| | Printed guide works in black and white | Verdicts distinguishable on a black-and-white photocopy | Print one copy in greyscale and look at it |

## 3. Screen readers (blind and low-vision users)

| ✅/❌ | Item | Target | How to test it |
|---|---|---|---|
| | Page language | `<html lang="en">` or `lang="hi"`; Hindi text inside English pages wrapped in `lang="hi"` so the Hindi voice is used | View source; listen with TalkBack: does Hindi sound Hindi? |
| | Every input has a label | The message box has a visible `<label>`; the upload button says what it does | Lighthouse / **axe DevTools** (free browser extension) → "Form elements must have labels" |
| | Buttons have names | Icon-only buttons have an `aria-label` | axe DevTools; TalkBack: swipe to each button and listen |
| | Images have alt text | Meaningful images have short `alt`; decorative images `alt=""` | axe DevTools |
| | Result is announced | The result area is an `aria-live="polite"` region, **or** focus moves to the result heading, so screen-reader users hear the verdict without searching | Turn on **TalkBack** (Android *Settings → Accessibility → TalkBack*), check a message, and listen |
| | Shapes and emoji are not the only content | On the website the shape is decorative (`aria-hidden`), so screen readers read only the **word**. In bot replies screen readers say "red circle", so the **word** (SCAM) must come right after it | TalkBack |
| | Headings in order | One `<h1>`, then `<h2>`… with no skipped levels | axe DevTools; *HeadingsMap* extension |

## 4. Using it with fingers, keyboard and limited dexterity

| ✅/❌ | Item | Target | How to test it |
|---|---|---|---|
| | Touch targets | Buttons **≥ 48 × 48 px** with **≥ 8 px** space between them. (WCAG 2.2 AA minimum is 24 × 24 px and AAA is 44 × 44; we go bigger for shaky hands) | DevTools: inspect the button size; try tapping with your thumb while walking |
| | Keyboard use | Everything works with **Tab / Shift+Tab / Enter / Space**; no keyboard traps | Unplug the mouse and use only the keyboard |
| | Visible focus | A thick, high-contrast focus outline on every focused element | Tab through the page and look |
| | Logical order | Tab order follows reading order: message box → Check button → result | Tab through the page |
| | No time limits | Nothing disappears or times out while someone is reading | Leave a result on screen for 10 minutes |
| | No drag, swipe or long-press needed | Every action is a single tap | Try every feature |
| | Motion | No auto-playing animations; respect `prefers-reduced-motion` | DevTools → *Rendering* → *Emulate CSS prefers-reduced-motion* |

## 5. Language and words

| ✅/❌ | Item | Target | How to test it |
|---|---|---|---|
| | Language switch | Visible **on every screen**, each language named in its own script ("English" / "हिंदी"), choice remembered | Switch language, reload, and go to another page |
| | Plain language | Sentences ≤ **15 words**, everyday words, active voice, no jargon (no "phishing", "URL", "classifier" in user text) | English: **Hemingway Editor** (hemingwayapp.com), aiming for about grade 6; Hindi: ask **two Hindi-speaking elders** to read it aloud and explain it back |
| | Chat replies short | Each bot reply **≤ 5 lines**: verdict, top 2 reasons, 1 action, 1 short caution. More detail only behind buttons ("Why?", "What should I do?") | Count the lines in replies to the test messages |
| | One clear action | Every result ends with one thing to do next | Read each result |
| | Helpful errors | Errors say what happened **and what to do** ("No text found in the image. Please paste the message instead.") | Upload a blank image; submit an empty box |
| | Numbers people can use | 1930 and cybercrime.gov.in written in full, never as a link-only icon | Read the result and guide pages |

## 6. Old phones and slow internet

| ✅/❌ | Item | Target | How to test it |
|---|---|---|---|
| | Page weight | First load **≤ 200 KB** total (HTML + CSS + JS + images, excluding uploads) | DevTools → *Network* → reload with cache disabled → look at "transferred" at the bottom |
| | Slow network | Usable within **≈ 5 seconds** on DevTools "Slow 3G"/"3G" throttling | DevTools → *Network* → throttling dropdown |
| | Lighthouse | Accessibility score **≥ 95**, Performance **≥ 90** on mobile | DevTools → *Lighthouse* → Mobile → Analyse |
| | No heavy frameworks | Plain HTML/CSS/small JS; no big libraries or web fonts that block text from showing | Check the Network panel for large files |
| | Works on old Android | Works in Chrome on the oldest Android phone you can borrow (ideally 1–2 GB RAM) | Borrow a relative's old phone and do the full task |
| | Works with JavaScript off (static pages) | Guide, privacy and help pages readable with JS disabled | DevTools → ⌘/Ctrl+Shift+P → "Disable JavaScript" |
| | Screenshot upload size | Large photos handled (size limit explained in plain words) | Upload a 5 MB camera photo |
| | Offline / error state | If the network fails, the user sees a plain message, not a blank screen | DevTools → *Network* → "Offline", then press Check |

## 7. Trust and safety in the interface

| ✅/❌ | Item | Target | How to test it |
|---|---|---|---|
| | Links in results are not clickable | Suspicious links are shown **defanged** (`hxxp://…[.]xyz`) and never as live links | Check a message containing a link |
| | Disclaimer visible | "Automatic check, can be wrong; green ≠ safe" on every result | Read each result |
| | Official help always one tap away | 1930 / cybercrime.gov.in on every result and on the home page | Look at each page |
| | Privacy in plain words | A short "We don't save your message" line next to the message box, linking to the privacy page | Look at the home page |

---

### Free tools used above

| Tool | What it checks | Where |
|---|---|---|
| Browser zoom (Ctrl/Cmd +) | Zoom and reflow | Any browser |
| Chrome DevTools: Device toolbar | Phone widths (320–360 px) | F12 → phone icon |
| Chrome DevTools: Lighthouse | Accessibility, performance, best practices | F12 → *Lighthouse* tab |
| axe DevTools (free) | Detailed accessibility errors | Chrome Web Store extension |
| Chrome DevTools: Emulate vision deficiencies | Colour blindness | F12 → ⋮ → More tools → *Rendering* |
| Chrome DevTools: Network throttling | Slow internet | F12 → *Network* tab |
| WebAIM Contrast Checker | Exact contrast ratios | webaim.org/resources/contrastchecker |
| TalkBack | Screen reader on Android | Android *Settings → Accessibility* |
| Hemingway Editor | English reading level | hemingwayapp.com |
| Real older adults | Everything that matters | See `PILOT_PROTOCOL.md` (approval first) |
