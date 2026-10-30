# T YouTube — UI + link suggestion handoff brief

Work order for a separate implementation agent. This covers the **two UI
requests** and the **one optional suggestion** that were tried in test-fix-4
and withdrawn.

Read this before touching code. The test-fix-4 attempt is kept only as a
reference for what **did not** work; do not copy it blindly.

---

## Ground rules

- **Baseline:** stable **v1.0.1** (`com.gold.android.youtube`, YouTube
  `21.26.364`, versionCode `2147483647`, AOSP `testkey`). The stable release
  must not be modified.
- **Deliver a separate test build** (for example `test-fix-6`), published as a
  GitHub prerelease. Do not promote it to stable without device testing.
- **Do not touch the download dialog.** It was fixed separately in test-fix-5;
  download behaviour is out of scope for this brief.
- **Do not change** the package name, version name, version code or signing
  key. The build must install over v1.0.1 with data intact.
- Patches must be **exact-once replacements** with post-condition checks. If an
  anchor is missing, the build must fail — never ship a half-applied patch.
- Verify on a **real device**. Emulator screenshots are not enough for these
  two UI features.
- If an acceptance check fails, **drop or feature-gate the feature**. Do not
  ship a broken UI again.

---

## 1. Shorts header — “T YouTube” brand loop

### Goal

Make the Shorts back control quietly brand the app without changing how Back
works or moving the video title.

### Visual specification

- Target: the top-left back control in the **Shorts player header**.
- Tap target: one strip, **128 × 48 dp**, aligned to the start/top of the
  header.
- Inside the strip, at the start:
  - a normal **48 × 48 dp** circular translucent back button
  - the stock left-arrow glyph, tinted with the overlay primary text colour.
- The strip cycles through two visuals:
  1. the normal circular back arrow
  2. the **“T YouTube”** wordmark, vertically centred in the same strip
- Wordmark style:
  - bold YouTube Sans (or the app's bold overlay font)
  - overlay primary text colour (white on video)
  - same visual height as the arrow; do not enlarge the control
  - transparent background; no extra box, border or shadow
- The title must stay exactly where it is today. In the test-fix-4 attempt the
  title anchor was pinned at `65 dp` from the start (4 dp margin + 48 dp
  button + 13 dp title margin) so it would not shift when the strip got wider.
  Keep that behaviour or an equivalent that produces **zero title movement**.

### Animation specification

- Total loop: **8 seconds**, repeating.
- Sequence:

  | Frame | Duration |
  |:--|--:|
  | arrow | 4800 ms |
  | fade arrow → wordmark, 25% | 75 ms |
  | fade arrow → wordmark, 50% | 75 ms |
  | fade arrow → wordmark, 75% | 75 ms |
  | “T YouTube” wordmark | 2750 ms |
  | fade wordmark → arrow, 25% | 75 ms |
  | fade wordmark → arrow, 50% | 75 ms |
  | fade wordmark → arrow, 75% | 75 ms |

- Use an `AnimationDrawable` (`animation-list`, `oneshot=false`) or an
  equivalent that survives configuration changes and view re-attachment.
- Start the loop only when the real Shorts header view is attached and visible.
  Stop it when the header is detached so it does not leak or animate offscreen.

### Behaviour requirements

- The **whole 128 × 48 dp strip stays one Back target**. Tapping the arrow,
  the wordmark, or the space between must go back.
- Do not add a second clickable view on top of the back button.
- Keep the existing content description
  (`reel_accessibility_player_back_button`) and accessibility role.
- No ripple or pressed state larger than the current circular button.
- The title, channel row and other header items must not move, resize or
  re-layout during the loop.

### Acceptance checks

- [ ] Open Shorts: the arrow changes into “T YouTube” after 4.8 s, stays for
      2.75 s, then fades back. Loop repeats.
- [ ] Tap while the arrow is visible → goes back.
- [ ] Tap while the wordmark is visible → goes back.
- [ ] Tap the empty part of the strip → goes back.
- [ ] The video title stays in exactly the same position for the whole loop.
- [ ] The control is not oversized; it looks like the stock button plus a
      wordmark, not a 128 dp-wide box.
- [ ] Works on a light video, a dark video, and with the title hidden.
- [ ] Rotate / leave and re-enter Shorts; the animation still starts and stops
      cleanly, with no doubled drawable or ghost frame.
- [ ] TalkBack still announces it as the Back button.

### Why test-fix-4 failed — read before implementing

The withdrawn attempt:

- replaced `res/layout/reel_player_static_header.xml`
- added a `BrandAnimation.start(View)` hook in `smali/aqzl.smali`
- used `scripts/assets/test-fix-4/tyt_brand_*.png` (384 × 144 px, i.e.
  128 × 48 dp at xxxhdpi)

It did not render on the real device. The likely reason is that the patched
layout/resource was not the runtime surface, or the hook ran before the view
was attached.

Do this first:

1. Use Android Studio **Layout Inspector** (or `uiautomator dump`) on the real
   Shorts screen and confirm which view actually hosts `reel_back_button`.
2. Confirm the resource ID and the inflating layout at runtime — do not assume
   the XML file name.
3. Add a temporary log in the hook to prove it runs and the background is an
   `AnimationDrawable`.
4. Only then patch the confirmed surface.

Reference files (do not copy verbatim):
`scripts/apply-test-fix-4.py`,
`scripts/assets/test-fix-4/`.

---

## 2. Fullscreen — “T YouTube” watermark

### Goal

A subtle brand wordmark in fullscreen, visible only while the player controls
are visible, never over the video when controls are hidden.

### Placement and style

- Text: **“T YouTube”**
- Position: horizontally centred in the **bottom control row**, between the
  left-side controls and the “More videos” / right-side controls.
- Size: **18 sp**, bold.
- Colour: overlay primary text colour (white), **alpha 0.8**.
- Background: none.
- Not clickable, not focusable, `importantForAccessibility="no"`.
- Must not overlap, push or resize any existing control.
- Must not shift the bottom bar height when it appears or disappears.

### Visibility rules

- Show **only in fullscreen** (portrait and landscape).
- Show **only while the controls are visible**.
- Hide immediately when the controls auto-hide or the user taps to hide them.
- Never show in:
  - the inline/normal player
  - miniplayer / PiP
  - the lock-screen or audio-only player
  - the Shorts player
- If the player is in fullscreen but the bottom control row is hidden (for
  example during a gesture), the watermark must be hidden too.

### Acceptance checks

- [ ] Fullscreen portrait: controls shown → “T YouTube” centred at the bottom
      between the left controls and “More videos”.
- [ ] Wait for controls to auto-hide → watermark hides with them.
- [ ] Tap to show controls → watermark returns in the same place.
- [ ] Rotate to landscape fullscreen → same position, no clipping.
- [ ] Rotate back → still correct.
- [ ] Inline player → watermark does not appear at all.
- [ ] Miniplayer/PiP → watermark does not appear.
- [ ] Tap where the watermark sits → the tap reaches the video/controls; the
      watermark never intercepts input.
- [ ] No layout jump when it appears/disappears.
- [ ] Long titles / narrow screens → no overlap with “More videos”.

### Why test-fix-4 failed — read before implementing

The withdrawn attempt:

- added a `YouTubeTextView` tagged `tyt_watermark` as a child of
  `quick_actions_container` in
  `res/layout/youtube_controls_bottom_ui_container.xml`
- added a `WatermarkTuner.apply(View, int, int)` call at the end of
  `SizeAdjustableOverlayWrapperLayout.onMeasure`
- showed the view only when measured height was at least 75% of the display
  height (a heuristic for fullscreen)

It did not render reliably. The likely reasons are that the patched container
is not the surface used at runtime, and that measure-time visibility is the
wrong signal for “controls visible”.

Do this instead:

1. Find the **actual runtime overlay** that owns the bottom controls, using
   Layout Inspector on a fullscreen video.
2. Tie visibility to the **same controller/state that shows and hides the
   controls**, not to a height heuristic.
3. Prefer adding the wordmark programmatically to the confirmed overlay, or
   patching the confirmed controller, so it cannot be dropped by a different
   layout variant (portrait/landscape, tablet, PiP).
4. Verify on the device in both orientations and with auto-hide enabled.

Reference files (do not copy verbatim):
`scripts/apply-test-fix-4.py`,
`res/layout/youtube_controls_bottom_ui_container.xml` and
`smali_classes8/.../SizeAdjustableOverlayWrapperLayout.smali` in the decoded
tree.

---

## 3. Suggestion — open `youtube.com` links in T YouTube

### Goal

Let users choose T YouTube for `youtube.com` / `m.youtube.com` links. This is a
**documentation-only** suggestion: no app code, package name or manifest
change is required or wanted.

### Why it cannot be automatic

Android allows only **one** app per website by default. The official YouTube
app is verified for `youtube.com`, so T YouTube cannot take those links
silently. The user must release them once in Android settings.

### Guide content (already in README / site)

1. **Release the links from official YouTube**
   Android Settings → Apps → **YouTube** → **Open by default** → turn off
   **Open supported links**, or remove `youtube.com` and `m.youtube.com` from
   the supported addresses.
2. **Give them to T YouTube**
   Android Settings → Apps → **T YouTube** → **Open by default** →
   **Add link** → tick `youtube.com` and `m.youtube.com` → **Add**.
3. **Test**
   Open a `youtube.com` link from a browser or chat app; Android should open
   or offer T YouTube.

Add a note that menu names vary by manufacturer (Samsung, Xiaomi, Pixel:
“Open by default”, “Default apps”, “Supported links”) and that step 1 can be
undone the same way.

### Acceptance checks

- [ ] README section explains the limitation and the two steps.
- [ ] Site section mirrors the same steps.
- [ ] Guide states clearly that it is optional and changing nothing is fine.
- [ ] No app code, manifest, package name or default-behaviour change.
- [ ] Undo instructions are included.

### Optional follow-up (only if separately requested)

Confirm whether the app already handles `youtube.com` intents internally. If
it does not, do **not** add intent filters in this task — Android will not give
T YouTube the links while official YouTube owns them, and adding filters can
create duplicate/competing handlers. Keep this task documentation-only.

---

## Deliverables expected from the implementation agent

1. A patch script (or scripts) with exact-once anchors and post-conditions.
2. A separate test tag/build; stable v1.0.1 untouched.
3. Device evidence for each acceptance list:
   - short screen recording of the Shorts loop + Back taps
   - fullscreen portrait and landscape screenshots with controls shown/hidden
   - confirmation of inline/PiP exclusion
4. A short test checklist in `ci/TEST-BUILD-README.txt`.
5. A note of the exact device model, Android version and app build used.

## Out of scope

- Download dialog and download service.
- Playback client, seek/quality, theme or seekbar colours.
- Package name, version code, signature or stable release.
- Any other UI restyling. If it is not in this brief, do not change it.

---

*Reference: the withdrawn attempt is `scripts/apply-test-fix-4.py`. Its release
and tag were deleted after testing; use it only to understand the failure, not
as a working implementation.*
