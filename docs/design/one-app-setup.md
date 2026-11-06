# T YouTube v1.2.0 — One-App First-Run Setup

**Status:** design handoff. No code, no build, no APK changes in this document.
**Baseline:** v1.1.0, package `com.gold.android.youtube`, versionCode `2147483647`, AOSP `testkey`.
**Goal release:** v1.2.0 test build, installable over v1.1.0 with data intact.

---

## 1. UX goal and the one hard constraint

### Goal

A first-time user opens **T YouTube** once and never leaves it: a short, branded
setup screen explains that microG is required, installs the copy already bundled
inside the APK, asks for notifications and battery exemption, and drops the user
into YouTube. No browser, no file manager, no separate microG download, no
"install this first" README step. The flow is skippable at every point,
resumable later from Settings, and every failure has a named cause and a way out.

Target: **60–90 seconds**, one system installer confirmation, one optional
notification prompt, and at most one optional battery screen. A user who taps
**Later** is never trapped and never nagged on every launch.

### Non-negotiable constraint

> **microG stays a separate Android package. Only its launcher icon is hidden.
> A true single-package merge is not possible.**

The bundled asset is the official **MicroG-RE `-noicon`** APK. It is installed as
its own app, with its own package id, UID, signature, permissions, update path
and uninstall path. `-noicon` removes only the launcher entry; microG still
exists in **Settings → Apps** (that is required for recovery, signature spoofing
and uninstall). The T YouTube APK itself is not re-signed and its package id does
not change.

Why this is not negotiable:

- Android has no supported way to merge two signed packages into one app.
- microG must own the GMS provider identity and its signature-spoofing metadata;
  folding it into the YouTube package would break that identity.
- microG needs its own UID and permission grants (background, network, GMS
  services). A merged package cannot hold two independent permission sets.
- microG must be independently updatable and uninstallable without touching
  T YouTube data.

**UI language:** say “one icon in your app drawer”, never “one APK” or “microG is
part of T YouTube”. The welcome footnote states the truth in one friendly line.

**Do not change:** package name, versionCode, signing key, or the existing
version name. The v1.2.0 marker goes in the About string only.

---

## 2. First-launch state machine

### 2.1 States

| ID | State | Meaning |
|:--|:--|:--|
| `BOOT` | Launch gate | Cold start, before any UI. Reads persisted setup flags. |
| `WELCOME` | Welcome | First run only. Brand, one paragraph, Start / Later. |
| `CHECKING` | Checking | One fast pass over ABI, Play Services, microG package/version/signer/icon, and offline state. |
| `CHECKLIST` | Checklist hub | The 3-row screen. microG-level diagnostic results are row states, not separate screens. |
| `PLAY_SERVICES_ACTIVE` | Blocker | Real Google Play Services is installed and enabled. |
| `UNSUPPORTED_ABI` | Blocker | No bundled microG native ABI matches this device. |
| `INSTALL_PERMISSION` | Pre-install gate | `REQUEST_INSTALL_PACKAGES` app-op is off. |
| `PREPARING` | Install progress | Streams the asset into a PackageInstaller session and verifies it. |
| `SYSTEM_INSTALLER` | Android UI | The OS installer confirmation. T YouTube is behind it. |
| `ERROR_DETAIL` | Error detail | Signature mismatch, storage, corrupt asset, blocked install. |
| `SUCCESS` | Success | microG ready; optional rows answered or skipped. |
| `APP` | App running | Normal YouTube UI. |
| `APP_LATER` | App running, setup unfinished | Same UI, one non-blocking reminder, Settings entry stays amber. |

**Global modifier:** `OFFLINE`. It is a flag, not a screen. It never blocks
install, because the APK is local. It only adds a dim banner and is cleared on
reconnect.

### 2.2 microG row states (inside `CHECKLIST`)

| Row state | Detection | Row copy | Action |
|:--|:--|:--|:--|
| `MISSING` | package not installed | “Not installed. Required for sign-in and playback.” | **Install** |
| `OUTDATED` | installed versionCode < bundled | “Update available · 7.1 → 7.2.1” | **Update** |
| `CURRENT` | installed versionCode ≥ bundled | “Installed · 7.2.1” | none / check |
| `DISABLED` | `ApplicationInfo.enabled == false` | “microG is turned off.” | **Turn on** |
| `DIFFERENT_BUILD` | installed signer ≠ bundled signer | “Using a different microG build.” | **Details** (ghost, non-blocking) |
| `ICON_VISIBLE` | microG has a launcher activity | “Installed · icon visible” | **Hide icon** (non-blocking) |
| `INSTALLING` | session active | “Installing…” | none |
| `CANCELLED` | last session aborted by user | “Install cancelled.” | **Try again** |
| `FAILED` | last session failed | “Install failed.” | **Details** |

`ICON_VISIBLE` exists because a user may already have the normal microG build
from the old README. Updating it in place to the bundled `-noicon` build hides
the icon and keeps microG data.

### 2.3 State diagram (simplified)

Numbers in the transition table are the source of truth. This diagram only
shows the main path and the required branches.

```
BOOT
 |-- all required checks green ----------------------------> APP
 |-- setup needed, welcome unseen ------------------------> WELCOME --Start--> CHECKING
 |-- setup needed, welcome seen ---------------------------> APP_LATER
                                                               ^
CHECKING                                                       | Later from any screen
 |-- no matching ABI ---------------------> UNSUPPORTED_ABI    |
 |-- Play Services active ----------------> PLAY_SERVICES_ACTIVE --disabled+check--> CHECKING
 |-- microG missing/outdated/disabled ----> CHECKLIST           |
 |-- microG current ----------------------> CHECKLIST           |
                                              |                |
                              Install / Update / Try again     |
                                              v                |
                                      INSTALL_PERMISSION       |
                                        | allowed   | denied   |
                                        v           +---------> CHECKLIST
                                    PREPARING --error--> ERROR_DETAIL --retry--> INSTALL_PERMISSION
                                        | commit
                                        v
                                  SYSTEM_INSTALLER
                                     | success      | cancel / fail
                                     v              v
                                  CHECKLIST      ERROR_DETAIL / CANCELLED
                                     |
                                  Continue
                                     v
                     notifications? --> battery? --> SUCCESS --> APP
```

`OFFLINE` is a global banner on any state. It never blocks install and never
changes the transition.

### 2.4 Transition table

| # | From | Trigger / guard | To | Side effect / UI |
|:-:|:--|:--|:--|:--|
| 1 | `BOOT` | required checks green: ABI ok, Play Services not active, microG current and enabled | `APP` | Set `setup_welcome_seen = true`, `setup_complete = true`. No setup UI, even on the first launch after an upgrade. |
| 2 | `BOOT` | `setup_complete == true` but a required check now fails | blocker or `CHECKLIST` | Self-heal: clear `setup_complete`; route to the relevant blocker or checklist in manage mode. |
| 3 | `BOOT` | required checks fail and `setup_welcome_seen == false` | `WELCOME` | First run that actually needs setup. |
| 4 | `BOOT` | required checks fail and `setup_welcome_seen == true` | `APP_LATER` | One snackbar only, no full-screen nag. |
| 5 | `WELCOME` | **Start setup** | `CHECKING` | Set `setup_welcome_seen = true`; resolve statuses in parallel; show checklist with row spinners. |
| 6 | `WELCOME` | **Later** | `APP_LATER` | Set `setup_welcome_seen = true`, leave `setup_complete = false`. |
| 7 | `CHECKING` | ABI intersection empty | `UNSUPPORTED_ABI` | Blocking info screen. |
| 8 | `CHECKING` | Play Services present, enabled, signer ≠ bundled microG | `PLAY_SERVICES_ACTIVE` | Blocking warning before install. |
| 9 | `CHECKING` | microG absent | `CHECKLIST` (`MISSING`) | microG row shows **Install**; **Continue** stays disabled with **Install microG to continue.** |
| 10 | `CHECKING` | microG version < bundled | `CHECKLIST` (`OUTDATED`) | Row shows **Update**; in-place, data kept. |
| 11 | `CHECKING` | microG version ≥ bundled, probe ok | `CHECKLIST` (`CURRENT`) | microG row green; continue. |
| 12 | `CHECKING` | microG current, probe fails | `CHECKLIST` (`CURRENT` + spoofing sub-step) | Expand microG row with **Open microG settings**. |
| 13 | `CHECKLIST` | tap **Install** / **Update** / **Try again** | `INSTALL_PERMISSION` | Only if `canRequestPackageInstalls() == false`. |
| 14 | `CHECKLIST` | tap install, permission already granted | `PREPARING` | Create session, stream asset. |
| 15 | `INSTALL_PERMISSION` | user returns, permission granted | `PREPARING` | Re-check on `onResume`, do not trust the toggle. |
| 16 | `INSTALL_PERMISSION` | user returns, still denied | `CHECKLIST` (`permission off`) | Row shows **Open settings**; no loop. |
| 17 | `PREPARING` | asset streamed + hash ok + session committed | `SYSTEM_INSTALLER` | Start the pending-user-action intent. |
| 18 | `PREPARING` | no space / hash fail / copy error | `ERROR_DETAIL` | Mapped message, retry or exit. |
| 19 | `SYSTEM_INSTALLER` | `STATUS_SUCCESS` | `CHECKLIST` (`CURRENT`) | Re-query package; inline banner “microG installed”. |
| 20 | `SYSTEM_INSTALLER` | `STATUS_FAILURE_ABORTED` | `CHECKLIST` (`CANCELLED`) | “Install cancelled.” Try again. |
| 21 | `SYSTEM_INSTALLER` | `STATUS_FAILURE_*` | `ERROR_DETAIL` | Map code to plain language. |
| 22 | `ERROR_DETAIL` | `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | `ERROR_DETAIL` (signature) | Offer **Uninstall microG**, explain data loss. |
| 23 | `ERROR_DETAIL` | **Try again** | `INSTALL_PERMISSION` | Fresh session; abandon old session. |
| 24 | `PLAY_SERVICES_ACTIVE` | **Check again**, now disabled | `CHECKING` | Re-run full check. |
| 25 | `PLAY_SERVICES_ACTIVE` | **Later** | `APP_LATER` | App opens; playback will fail until fixed. |
| 26 | `UNSUPPORTED_ABI` | app updated / reinstall | `CHECKING` | Only re-check on a new build. |
| 27 | `CHECKLIST` | microG current, tap **Continue** | notification ask, then `SUCCESS` | Ask only if the notification row is unanswered and API ≥ 33. Battery is never auto-opened; it stays an optional row. |
| 28 | `CHECKLIST` | notification answered/skipped or already granted | `SUCCESS` | Set `setup_complete = true`. Battery remains optional in Settings. |
| 29 | `SUCCESS` | **Open T YouTube** / **Done** | `APP` | Finish setup activity. |
| 30 | any | **Later** / back out | `APP_LATER` | Preserve row state; Settings entry shows amber. |
| 31 | any | network lost | same state + `OFFLINE` | Dim banner; install still allowed. |

### 2.5 Priority order when several conditions are true

1. `UNSUPPORTED_ABI` — nothing can fix this at runtime.
2. `PLAY_SERVICES_ACTIVE` — installing microG first would still fail.
3. `MISSING` / `DISABLED` / `OUTDATED` — install or update.
4. `DIFFERENT_BUILD` — non-blocking info. Never uninstall a working microG just
   because its signer differs. Only a failed update becomes the signature error.
5. `ICON_VISIBLE` — non-blocking cleanup.
6. Optional permissions.

### 2.6 Persisted flags

| Key | Type | Set when | Cleared when |
|:--|:--|:--|:--|
| `setup_welcome_seen` | bool | Boot finds everything green; Start or Later on welcome | app data cleared |
| `setup_complete` | bool | Success screen reached, or boot re-check is fully green | microG re-check fails, or app data cleared |
| `setup_notif_answered` | bool | notification prompt answered/skipped | never (row can still be changed in Settings) |
| `setup_battery_answered` | bool | battery screen answered/skipped | never |
| `setup_last_check` | long | every `CHECKING` pass | never |
| `setup_later_reminder_version` | int | the Later snackbar is shown/dismissed | the app versionCode changes (then it may show once more) |
| `setup_install_session` | int | session created | success / abandon / failure |

No account data, no package list, no signature material in preferences. The
install session id is an integer owned by the system; it is safe to persist.

---

## 3. Screen-by-screen flow and exact copy

Voice: short sentences, second person, sentence case, no exclamation marks, no
jargon unless explained once. All copy below is final English for v1.2.0. Every
string goes in `res/values/strings.xml` with a `tyt_setup_` prefix so it can be
translated later.

### 3.0 Order and exits

```
Welcome ──Start──> Checklist ──Continue──> (notifications) ──> (battery) ──> Success ──> App
   │                   │                                                          
   └──Later────────────┴──Later / Back──────────────────────────────────────> App + one reminder
```

- **Every screen has an exit.** Welcome and checklist: **Later**. Permission and
  error screens: **Not now** or **Later**. Preparing: **Cancel** with a confirm.
  Success: **Open T YouTube**.
- **No loop.** A denied permission returns to the checklist with a clear row
  state; the app never re-opens the same system screen automatically.
- **No dead end.** Every error screen has at least one of **Try again**,
  **Open settings**, **Uninstall microG**, or **Get help**.

### 3.1 Welcome

| Element | Exact copy | Behaviour |
|:--|:--|:--|
| Status bar | — | Dark `#05060A`, light icons. No app bar, no back arrow. |
| App icon | — | 72 dp, existing `@mipmap/ic_launcher` / T mark. 20 dp corner radius if the launcher icon is masked. |
| Wordmark | **T YouTube** | 20 sp / 700, `#E8EBF2`, centred, 12 dp below icon. |
| Headline | **One quick setup.** | 28 sp / 700, centred, 24 dp below wordmark. |
| Body | **T YouTube runs on microG, a small service that replaces Google Play Services. It's already inside this app — we just need to install it.** | 15 sp / 400, `#98A0B3`, 16 dp side padding, left-aligned. |
| Preview | **Install microG · Notifications · Battery** | 13 sp / 600, `#6B7488`, centred, 20 dp below body. The middle dot is a separator, not a bullet list. |
| Primary | **Start setup** | Full-width minus 24 dp, 52 dp high, `#F3024E`, white 16 sp / 700, 16 dp radius. |
| Secondary | **Later** | Text button, 48 dp high, `#00FCFF`, 15 sp / 600. Below primary, 4 dp gap. |
| Footnote | **microG stays a separate app. Its icon is hidden, so you'll only see T YouTube.** | 12 sp / 400, `#6B7488`, centred, 24 dp below Later. This is the honesty line. |
| Micro-caption | **About a minute · works offline** | 12 sp / 400, `#6B7488`, centred, 12 dp above the bottom inset. |

Behaviour:

- **Start setup** → `CHECKING`; checklist appears with per-row spinners. No
  blocking full-screen spinner.
- **Later** → set `setup_welcome_seen = true`; open the app. If microG is
  missing, show the one-time bottom reminder described in 3.7.
- **Back** = **Later**. Do not trap the user on the welcome screen.
- If the user has reduced motion enabled, no entrance animation; the screen is
  static.

### 3.2 Checklist

App bar: back arrow (content description “Back”), title **Setup**, right text
button **Later**. Back and Later both mean “finish later”; no confirm.

| Element | Exact copy | Behaviour |
|:--|:--|:--|
| Headline | **3 small steps.** | 24 sp / 700, top-aligned, 20 dp side padding. |
| Subhead | **microG is required. The other two take a tap.** | 14 sp / 400, `#98A0B3`. |
| Required chip | **Required** | 11 sp / 700 uppercase, red-tinted pill on the microG row only. |
| Optional chip | **Recommended** | 11 sp / 600 uppercase, `#6B7488` outline pill on notification and battery rows. |

#### Row 1 — microG

| State | Title | Subtitle | Trailing action |
|:--|:--|:--|:--|
| `MISSING` | **microG** | **Not installed. Required for sign-in and playback.** | **Install** (red pill) |
| `OUTDATED` | **microG** | **Update available · 7.1 → 7.2.1** | **Update** (red pill) |
| `CURRENT` | **microG** | **Installed · 7.2.1** | cyan check, no button |
| `DISABLED` | **microG** | **microG is turned off.** | **Turn on** (red pill) |
| `DIFFERENT_BUILD` | **microG** | **Using a different microG build.** | **Details** (ghost pill) |
| `ICON_VISIBLE` | **microG** | **Installed · icon visible** | **Hide icon** (ghost pill) |
| `INSTALLING` | **microG** | **Installing…** | small spinner, no button |
| `CANCELLED` | **microG** | **Install cancelled.** | **Try again** (red pill) |
| `FAILED` | **microG** | **Install failed.** | **Details** (ghost pill) |

`ICON_VISIBLE` is non-blocking and appears only when a working microG with a
launcher icon is already installed. “Hide icon” updates it in place to the
bundled `-noicon` build, preserving microG data.

**Signature-spoofing sub-panel** — expands under the microG row after install
when the readiness probe is inconclusive or fails:

> **One more thing: turn on signature spoofing for T YouTube in microG.**
> [**Open microG settings**]  [**Check again**]

If the second check still fails:

> **Not ready yet. Sign-in and playback will fail without this.**
> [**Open microG settings**]  [**Get help**]

The sub-panel is not a fourth checklist item. It belongs to microG.

#### Row 2 — Notifications

| State | Title | Subtitle | Trailing action |
|:--|:--|:--|:--|
| not asked, API 33+ | **Notifications** | **Download finished and playback alerts.** | **Turn on** (ghost pill) |
| granted | **Notifications** | **On.** | cyan check |
| denied | **Notifications** | **Off. Tap to open settings.** | **Open settings** (ghost pill) |
| API < 33 | **Notifications** | **On by default on this Android version.** | cyan check |

#### Row 3 — Battery

| State | Title | Subtitle | Trailing action |
|:--|:--|:--|:--|
| not asked | **Battery** | **Keeps microG awake in the background.** | **Allow** (ghost pill) |
| granted | **Battery** | **Unrestricted.** | cyan check |
| denied | **Battery** | **Restricted. Background playback may stop.** | **Fix** (ghost pill) |
| unsupported | **Battery** | **Not needed on this phone.** | dim check |

#### Footer

| State | Primary button | Helper under button |
|:--|:--|:--|
| microG not ready | **Continue** (disabled, 40% opacity) | **Install microG to continue.** |
| installing | **Installing…** (disabled) | **This takes a few seconds.** |
| microG ready | **Continue** | **Tap any row to change it.** |
| manage mode from Settings | **Done** | **Last checked just now.** |

Below the footer, always:

> **You can change all of this later in Settings → Setup & permissions.**

12 sp / 400, `#6B7488`, 16 dp bottom inset.

Behaviour:

- The whole row is one tap target; the trailing pill is visual, not a nested
  button. This keeps TalkBack focus to one item per row.
- Tapping the notification row triggers the Android prompt (API 33+) or opens
  app notification settings if the prompt is no longer available.
- Tapping the battery row opens the system exemption dialog, with app-info
  fallback.
- **Continue** asks the notification permission once if it has not been
  answered, then goes to Success. It never auto-opens the battery screen; the
  battery row stays available and optional.
- Tapping microG when current and spoofing unknown opens the sub-panel.
- When the user returns from any system screen, re-check the relevant row on
  `onResume`; never assume the toggle changed.
- A successful microG install shows an inline banner above the rows for 4 s:
  **microG installed.** Do not jump straight to Success; the user still sees
  the optional rows.

### 3.3 Install permission

Presented as a full-width sheet over the checklist, dimming the rows but keeping
the app bar visible.

| Element | Exact copy |
|:--|:--|
| Title | **Allow installs** |
| Body | **Android needs your OK before T YouTube can install microG. You'll only do this once.** |
| Small note | **On most phones this is called “Install unknown apps”.** |
| Primary | **Open settings** |
| Secondary | **Not now** |
| Conditional note (toggle greyed out) | **If the switch is greyed out, tap ⋮ → Allow restricted settings.** |

After returning from Settings with the permission still off, replace the note
with an inline warning:

> **Still off. Turn on “Allow from this source”, then come back.**

The primary stays **Open settings**; **Not now** returns to the checklist with
the microG row showing **Install permission off.** and a trailing **Open
settings** pill.

### 3.4 Installing microG (preparing)

Full screen, app bar title **Installing microG**, back arrow opens the cancel
confirm. The screen exists so the user knows why Android is about to show a
second installer.

| Element | Exact copy |
|:--|:--|
| Headline | **Getting microG ready.** |
| Body | **This takes a few seconds. Keep the screen open.** |
| Step 1 | **Preparing the file** — spinner, then cyan check |
| Step 2 | **Checking the file** — spinner, then cyan check |
| Step 3 | **Opening Android installer** — spinner, then cyan check |
| Hint card | **Android will show one confirmation. Tap Install. microG's permissions are normal — it stands in for Google Play Services.** |
| Slow-storage note (after 8 s) | **Still working… large files take a little longer on some phones.** |
| Cancel | **Cancel** (text button, `#98A0B3`) |

No fake percentage. The progress bar is indeterminate.

Cancel confirm:

> **Stop installing microG?**
> You can finish later from Settings → Setup & permissions.
> [**Keep installing**] [**Stop**]

### 3.5 System installer

This is Android's UI, not ours. T YouTube is paused behind it.

- Before launching: the hint card in 3.4 is the only explanation.
- On return, show **Finishing up…** for up to 2 seconds while re-querying the
  package.
- If success: checklist with the banner **microG installed.**
- If the user cancelled: checklist with `CANCELLED`; no toast, no blame.
- If the system shows “App not installed”, map it in `ERROR_DETAIL` (3.8).

### 3.6 Success

| Variant | Headline | Body | Primary | Secondary |
|:--|:--|:--|:--|:--|
| all green | **You're all set.** | **microG is installed. T YouTube is ready.** | **Open T YouTube** | **Done** |
| optional rows skipped | **You're all set.** | **microG is installed. You can turn on notifications and battery later in Settings.** | **Open T YouTube** | **Review setup** |
| spoofing unverified | **Almost ready.** | **microG is installed. If sign-in fails, turn on signature spoofing in microG settings.** | **Open T YouTube** | **Review setup** |
| re-entry from Settings | **Everything is set up.** | **microG is installed and up to date.** | **Done** | — |

Visual: 64 dp cyan ring with a check, `#00FCFF`; no confetti, no sound. Headline
24 sp / 700. One-sentence body, `#98A0B3`. The success screen must not claim
“all set” if the readiness probe failed; use **Almost ready.**

### 3.7 Later path

Tapping **Later** never shows a second dialog. It sets `setup_welcome_seen` and
opens the app.

- If microG is **not ready**, show a single bottom snackbar on the first app
  screen, once per app version:
  > **Setup isn't finished.** [**Finish**] [dismiss]
  Tapping **Finish** opens the checklist. Dismissing it does not repeat it.
- If microG is **ready** but notifications or battery were skipped, show
  nothing. The Settings row is enough.
- If the user tries to play a video while microG is missing, replace the old
  dead-end dialog with:

  > **microG isn't installed.**
  > T YouTube can't sign in or play videos without it.
  > [**Set up microG**] [**Close**]

- The Settings entry in section 6 is always present and shows an amber dot when
  anything required is missing.

### 3.8 Error and blocker copy

| Case | Title | Body | Actions |
|:--|:--|:--|:--|
| Install cancelled | **Install cancelled.** | **microG isn't installed yet. You can try again now or finish later in Settings.** | **Try again** · **Later** |
| Signature mismatch | **A different microG is installed.** | **Android can't replace it because it's signed with a different key. Uninstall the old microG, then try again.** Warning line: **Uninstalling microG removes its accounts and settings. T YouTube's data stays.** | **Uninstall microG** (opens app info) · **Cancel** |
| Not enough space | **Not enough space.** | **microG needs about 250 MB free. Free up some space, then try again.** | **Try again** · **Manage storage** |
| Damaged asset | **The microG file is damaged.** | **Reinstall T YouTube to replace it. Your app data stays.** | **Get help** · **Close** |
| Android blocked install | **Android blocked the install.** | **Play Protect or your phone's security settings stopped it. Check the installer details, then try again.** | **Try again** · **Get help** |
| Generic install failure | **microG didn't install.** | **Something stopped the installer. Try again — if it keeps happening, send us the details.** | **Try again** · **Copy details** · **Get help** |
| Play Services active | **Google Play Services is on.** | **T YouTube needs microG instead. The two can't run together.** Note: **On most phones: Settings → Apps → Google Play Services → Disable. Other apps that use Google may stop working until you turn it back on.** | **Open Play Services settings** · **Check again** · **Later** |
| Play Services cannot be disabled | **Play Services can't be turned off.** | **This phone doesn't allow it. T YouTube can't run until Play Services is disabled or removed.** | **Get help** · **Later** |
| Unsupported ABI | **This phone isn't supported.** | **The microG inside this build doesn't match your phone's processor. Install the universal T YouTube build from the release page.** | **Open release page** · **Copy device info** · **Later** |
| microG disabled | **microG is turned off.** | **Turn it on to sign in and play videos.** | **Turn on** (app info) · **Later** |
| microG working, different build | **Using a different microG build.** | **This microG is newer than the bundled one. T YouTube will keep using it.** | **OK** |
| Permission still off | **Install permission off.** | **Turn on “Allow from this source” for T YouTube, then come back.** | **Open settings** · **Not now** |
| Offline banner | **You're offline.** | **Setup still works. Sign-in needs internet later.** | dismiss icon only |

“Copy details” copies a plain-text block: T YouTube version name, Android
version, ABI list, microG package/version/signature status, Play Services
enabled state, install status code, and the last 20 lines of the `TytSetup` log.
No account identifiers, no package list, no file paths.

---

## 4. Wireframes and brand

### 4.1 Welcome / setup screen

```
+--------------------------------------------------+
|  [status bar]  9:41                  [battery]   |  #05060A
|                                                  |
|                                                  |
|                    +--------+                    |
|                    |   T    |                    |  72 dp, existing icon
|                    |        |                    |
|                    +--------+                    |
|                                                  |
|                    T YouTube                     |  20 sp / 700
|                                                  |
|                One quick setup.                  |  28 sp / 700
|                                                  |
|   T YouTube runs on microG, a small service      |  15 sp / 400
|   that replaces Google Play Services. It's       |  #98A0B3
|   already inside this app - we just need to      |
|   install it.                                    |
|                                                  |
|   Install microG | Notifications | Battery       |  13 sp / 600
|                                                  |
|  +--------------------------------------------+  |
|  |               Start setup                  |  |  52 dp, #F3024E
|  +--------------------------------------------+  |
|                                                  |
|                     Later                        |  15 sp / 600 #00FCFF
|                                                  |
|   microG stays a separate app. Its icon is       |  12 sp / 400
|   hidden, so you'll only see T YouTube.          |  #6B7488
|                                                  |
|          About a minute | works offline          |
+--------------------------------------------------+
```

### 4.2 Checklist

```
+--------------------------------------------------+
|  <-   Setup                             Later    |  app bar 56 dp
|                                                  |
|  3 small steps.                                  |  24 sp / 700
|  microG is required. The other two take a tap.   |  14 sp / 400 dim
|                                                  |
|  +--------------------------------------------+  |
|  | [T]  microG                   [ Install ]  |  |  row 76 dp
|  |      Not installed. Required.              |  |  red pill
|  +--------------------------------------------+  |
|  +--------------------------------------------+  |
|  | (o)  Notifications            [ Turn on ]  |  |
|  |      Download finished and playback alerts.|  |
|  +--------------------------------------------+  |
|  +--------------------------------------------+  |
|  | (o)  Battery                    [ Allow ]  |  |
|  |      Keeps microG awake in the background. |  |
|  +--------------------------------------------+  |
|                                                  |
|  +--------------------------------------------+  |
|  |                Continue                    |  |  disabled 40%
|  +--------------------------------------------+  |
|  Install microG to continue.                     |  12 sp dim
|                                                  |
|  You can change all of this later in Settings -> |  12 sp / 400
|  Setup & permissions.                            |  #6B7488
+--------------------------------------------------+
```

Status vocabulary, used instead of colour alone:

| Mark | Meaning | Colour |
|:--|:--|:--|
| `[x]` | Ready | `#00FCFF` check |
| `[!]` | Needs attention | `#F5A524` |
| `[ ]` | Not done | `#6B7488` |
| `[-]` | Skipped / not needed | `#6B7488` |

The checklist uses the same shell as the welcome: dark background, 24 dp side
padding, 16 dp between cards, 16 dp card radius, 1 dp `#1E2330` border. The
install progress and success screens reuse the shell with a single centred
column; no separate visual language.

### 4.3 Brand tokens

Use these in-app values. They are the canonical repo brand; `docs/index.html`
uses web approximations (`#00e5ff`, `#ff2d78`) — do not copy those into the APK.

| Token | Hex | Use |
|:--|:--|:--|
| Brand red | `#F3024E` | Primary CTA fill, required chip, active progress, T mark ring. |
| Brand cyan | `#00FCFF` | Success checks, links, “ready” status, focus ring. |
| Background | `#05060A` | Full-screen background. OLED-safe, not pure black. |
| Surface | `#0B0D14` | App bar and bottom insets. |
| Card | `#11141D` | Checklist rows, hint cards. |
| Line | `#1E2330` | 1 dp borders and dividers. |
| Text | `#E8EBF2` | Titles and primary body. |
| Dim text | `#98A0B3` | Secondary body, subtitles. |
| Faint text | `#6B7488` | Footnotes, disabled labels. |
| Warning | `#F5A524` | Recoverable warning icon/dot. |
| Destructive outline | `#F3024E` at 100% stroke, transparent fill | Only **Uninstall microG**. |

Red is the action colour; cyan is the status colour. Never use red for “error”
body text — use the amber warning icon plus plain copy. The one exception is the
outlined destructive button, which is red on purpose.

### 4.4 Icon and wordmark

- **Welcome icon:** the existing launcher icon resource (`@mipmap/ic_launcher`)
  at 72 dp. Do not add a second copy of `assets/logo.png` to `res/`; that only
  grows the APK.
- **Wordmark:** a `TextView` reading **T YouTube**, bold, 20 sp, `#E8EBF2` —
  not the 1280×320 `banner.png`. The banner is a web asset; stretching it on a
  phone looks soft and adds a large bitmap to memory.
- **Optional accent:** a 2 dp horizontal line under the wordmark, gradient from
  `#F3024E` to `#00FCFF`, 48 dp wide, centred. This is the only gradient on the
  screen; keep it static (no animation).
- **Checklist microG icon:** a neutral service/shield glyph from the app's
  existing icon set. Do not use the Google “G”, the microG logo, or a
  third-party brand mark. The row label already says microG.
- **Do not** put the wordmark in a box, add a drop shadow, or use all caps.

### 4.5 Type, spacing, motion

| Item | Spec |
|:--|:--|
| Typeface | The app's existing bold/regular family (YouTube Sans or Roboto). No new font files. |
| Headline | 28 sp / 700 welcome, 24 sp / 700 checklist and success. |
| Row title | 16 sp / 600. |
| Body | 15 sp / 400, line height 1.4. |
| Caption | 12 sp / 400, `#6B7488`. |
| Touch target | 48 dp minimum; rows 76 dp. |
| Side padding | 24 dp; 16 dp on screens narrower than 360 dp. |
| Button height | 52 dp primary; 48 dp ghost. |
| Corner radius | 16 dp cards and primary button; 999 dp pills. |
| Motion | 160 ms fade/slide between checklist and detail. No loop, no bounce. Respect `Settings.Global.ANIMATOR_DURATION_SCALE` and `ValueAnimator.areAnimatorsEnabled()`. |
| Haptics | One light `CONFIRM` tick on success. No sound. |

### 4.6 Accessibility and RTL

- Status is text + icon + colour, never colour alone.
- Each checklist row is one focusable unit. Its content description includes
  title, status and action, for example: “microG, not installed, required.
  Install.”
- Announce state changes: “microG installed”, “Notifications on”, “Install
  failed”.
- 200% font scale: the screen scrolls; no fixed-height text containers; the
  footer CTA stays reachable above the navigation inset.
- Landscape: scrollable single column, max width 480 dp, centred.
- RTL: use `start`/`end`, not left/right; mirror the back arrow and chevrons.
- Focus order: headline → rows top to bottom → primary → footnote.
- Contrast: body `#98A0B3` on `#05060A` is about 7.4:1. White 16 sp / 700 on
  `#F3024E` is about 4.3:1 — acceptable for bold UI labels, but if QA requires
  strict AA for normal text, use 18 sp / 700 or darken the button fill to
  `#D40044` while keeping `#F3024E` for accents.

---

## 5. Permissions rationale

Principles:

1. **Ask at the moment of need**, never on the welcome screen or on first frame.
2. **One prompt at a time.** Resolve microG before touching notifications;
   resolve notifications before battery.
3. **Never auto-repeat a denied prompt.** After a denial, the row becomes a
   settings shortcut.
4. **Re-check on resume**, not on the result callback alone. The user may change
   the setting in a different screen.
5. **microG's own permissions are microG's business.** Do not request or grant
   location, contacts or GMS permissions on its behalf.

| Access | Why T YouTube needs it | When to ask | If denied | How to recover |
|:--|:--|:--|:--|:--|
| `REQUEST_INSTALL_PACKAGES` (special app-op, API 26+) | Install the bundled microG APK. Without it, `PackageInstaller` returns `STATUS_FAILURE_BLOCKED`. | Immediately before the first microG install/update, after the user taps **Install**. | microG cannot be installed. The app still opens; the checklist row shows **Install permission off.** | In-app **Open settings** → `ACTION_MANAGE_UNKNOWN_APP_SOURCES` with `package:com.gold.android.youtube` → **Allow from this source**. Fallback: Settings → Apps → T YouTube → Install unknown apps. Android 13+ greyed toggle: ⋮ → **Allow restricted settings**. |
| `POST_NOTIFICATIONS` (runtime, API 33+) | Download-finished alert, playback controls, and any existing app notifications. | After microG is ready, when the user taps **Turn on** on the notifications row, or **Continue** with the row still unset. | No notifications. Downloads still complete, playback is unaffected, and no feature is blocked. | In-app **Open settings** → `ACTION_APP_NOTIFICATION_SETTINGS` for T YouTube. Or Settings → Apps → T YouTube → Notifications. If Android will not show the prompt again, go straight to settings. |
| Battery optimization exemption (`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, API 23+) | Keep **microG** alive so its GMS connection survives Doze and OEM background killers. This is the exemption the README means by “microG needs background permission on some phones”. | After microG installs, when the user taps **Allow** on the battery row. Optional. | microG may be delayed or killed in the background; foreground playback still works, background playback and notifications may stop. | In-app **Fix** → `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` for the microG package. Fallback: microG app info → Battery → **Unrestricted**, or Settings → Apps → Special access → Battery optimization → microG → Don't optimize. Some ROMs have no exemption; show **Not needed on this phone.** |
| Download folder via SAF (`ACTION_OPEN_DOCUMENT_TREE`, persistable URI grant) | Let the user choose where downloads go and keep access across reboots. No broad storage permission is needed. | **Not in first-run.** First download that targets a user folder, or when the user changes **Download Settings → Download folder**. | The download uses the app's default internal folder. No crash; no loss of existing downloads. | Download Settings → Download folder → pick the folder again. If a persisted grant was revoked, the next download shows **Folder access was removed. Choose the folder again.** and opens the picker. |
| `INTERNET`, `ACCESS_NETWORK_STATE` (normal, auto-granted) | Playback, downloads, sign-in; detect offline for the setup banner. | Never prompts. | Only possible via a restricted profile, firewall or device policy. The app behaves as offline. | System-level: allow T YouTube network access in the profile/firewall. No in-app rationale needed. |
| `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_DATA_SYNC` (normal, API 34+) | Keep downloads running when the app is backgrounded, with the existing download notification. | Never prompts. | The OS may stop a background download; the user sees the existing failure UI. | No runtime recovery. The battery row and the existing download retry cover OEM killers. |
| `<queries>` for the microG package and `com.google.android.gms` (manifest, not a permission) | Android 11+ package visibility. Without it, `getPackageInfo()` throws `NameNotFoundException` even when the package is installed, and setup wrongly says “missing”. | Build time. | Setup cannot detect microG or Play Services. This is a build bug, not a user denial. | Fix the manifest declaration. Never use `QUERY_ALL_PACKAGES` as a shortcut. |
| **Not requested:** `MANAGE_EXTERNAL_STORAGE` | Broad all-files access is unnecessary and hostile. | — | — | Use SAF for the download folder. |
| **Not requested:** `READ_EXTERNAL_STORAGE` / `WRITE_EXTERNAL_STORAGE` | Scoped storage and SAF make these unnecessary on API 29+. | — | — | Use app-specific storage or the user-picked SAF tree. |
| **Not requested:** `READ_MEDIA_VIDEO` | T YouTube creates its own downloads; it does not need to read the user's gallery. | — | — | Open downloads through the app's own file/URI. |
| **Not requested:** `QUERY_ALL_PACKAGES` | Only two packages need to be visible. | — | — | Use the narrow `<queries>` entries above. |
| **Not requested:** `SYSTEM_ALERT_WINDOW` | No overlay is needed; setup is a normal Activity. | — | — | — |

### 5.1 Permission copy shown in-app

- Install permission sheet: **Allow installs** / **Android needs your OK before
  T YouTube can install microG. You'll only do this once.**
- Notification rationale (one line above the system prompt, optional): **One tap
  to hear when a download finishes.**
- Battery rationale: **Keeps microG awake so playback doesn't stop in the
  background.**
- Storage rationale (Download Settings only): **Choose where saved videos go.
  T YouTube only sees the folder you pick.**

Do not use scary words (“unknown sources”, “root”, “system app”) in the main
copy. Use the platform's own labels only when pointing at a settings screen.

---

## 6. Re-entry: “Setup & permissions”

### 6.1 Placement

Add one row to the existing Settings list, immediately above **About**:

```
  Download Settings
  Setup & permissions        [!]       <- amber when attention is needed
  About
```

- Same icon-and-label row style as the screenshot in `assets/screenshots/settings.jpg`:
  no card, no divider, 56 dp row height, existing Settings typography.
- Icon: the app's existing shield/check/settings glyph. Do not add a new bitmap.
- Label: **Setup & permissions**. This is the only label; do not call it
  “MicroG setup” or “First run”.
- Trailing status: an 8 dp dot, `#00FCFF` when everything required is ready,
  `#F5A524` when microG is missing/outdated/disabled or a required check fails.
  No dot when only optional permissions are off.
- Content description: “Setup and permissions, needs attention” / “Setup and
  permissions, ready”.

### 6.2 Behaviour

| Situation | Opens | Screen state |
|:--|:--|:--|
| First tap after a skipped setup | Checklist | Manage mode, rows reflect current state. No welcome. |
| All green | Checklist | Headline **Everything is set up.** Primary **Done**. Optional rows still tappable. |
| microG missing or outdated | Checklist | Same install/update flow as first run, including permission gate and system installer. |
| Play Services active | Checklist, then blocker | The blocker opens as its own screen; back returns to the checklist and **Later** exits. It is not a dead end. |
| Optional permissions off | Checklist | Rows show **Off** / **Restricted** with a fix action. |
| User revoked install permission | Checklist | microG row shows **Install permission off.** if an install is needed. |
| User revoked notification permission | Checklist | Row updates on `onResume` to **Off. Tap to open settings.** |
| User revoked the download folder grant | Download Settings | Existing downloader error handles it; Setup does not show a storage row. |

Manage-mode differences from first run:

- No welcome, no “Start setup”.
- No automatic success screen. The user stays on the checklist and taps
  **Done**.
- A **Check again** text button in the app bar refreshes all rows.
- The footer shows **Last checked just now.** and **Done**.
- If the user changes a setting in Android Settings and returns, every row
  re-checks on `onResume`. No pull-to-refresh gesture is needed.

### 6.3 Other entry points

- **Existing “MicroG Not Installed” dialog:** positive button becomes
  **Set up microG** and opens the checklist in manage mode. This is the safety
  net for users who tap **Later** and then try to play a video.
- **About screen:** optional one-line link **Setup & permissions** below the
  build marker, for users who look there first.
- **No launcher shortcut, no widget, no notification** for setup. The Settings
  row and the error dialog are enough.

### 6.4 What Settings must not do

- Do not show a second “MicroG” settings screen with a different design.
- Do not duplicate the install permission toggle; always deep-link to Android.
- Do not hide the row after success. It is the only discoverable recovery path
  after a future microG uninstall.
- Do not change the existing Settings order beyond inserting this one row.

---

## 7. Edge cases and acceptance criteria

### 7.1 Edge cases

| Case | Expected behaviour |
|:--|:--|
| **Offline during setup** | Install still works from the bundled asset. A dim banner says **You're offline. Setup still works. Sign-in needs internet later.** No retry loop, no blocking dialog. Success screen still appears. |
| **32-bit userspace** (`armeabi-v7a` only) | Normal flow. The bundled universal microG includes 32-bit libs; no warning, no “unsupported” screen. Verify on a real 32-bit device, not only an emulator. |
| **No matching ABI** | `UNSUPPORTED_ABI` before any install attempt. Copy device info; link to the release page. Never partially install. |
| **Play Services is a system app that cannot be disabled** | Show **Play Services can't be turned off.** Do not pretend the app will work. Offer **Get help** and **Later**. |
| **Play Services is disabled, then re-enabled later** | Next launch or Settings re-check shows the blocker again; `setup_complete` is cleared. Playback fails gracefully through the existing error path. |
| **microG installed but disabled** | Row shows **microG is turned off.** **Turn on** opens its app info. After enabling, re-check version and probe. |
| **microG newer than the bundled copy** | Keep it. Never downgrade. Show **Using a different microG build.** No update button. If its signature differs, keep it; only an update attempt can surface the signature error. |
| **microG same version, icon visible** | Offer **Hide icon**; update in place to the `-noicon` build, preserving data. If the update fails, leave the working microG alone and show an info row. |
| microG signed differently but working | Do not block. Row note **Using a different microG build.** Only an update attempt can surface the signature error; never uninstall a working microG automatically. |
| **microG uninstalled while T YouTube is open** | Next `onResume` / playback check routes to the existing “microG isn't installed” dialog with **Set up microG**. No crash. |
| **User cancels the system installer** | `CANCELLED` row, exact copy **Install cancelled.** **Try again** creates a fresh session. No orphan session, no partial package. |
| **Process death during asset copy / commit** | On next launch, query the persisted session id and the package. If installed → current; if the session is gone and the package is absent → cancelled/failed with retry. Delete any temp file. |
| **Rotation during preparing** | No duplicate session and no restart from zero. Either keep the Activity across the short copy (`configChanges`) or move the copy into a small foreground service. Progress resumes or the screen reattaches to the session. |
| **Low storage** | Pre-flight check for about 250 MB before creating the session. Show **Not enough space.** with **Manage storage**; never start a doomed install. |
| **Play Protect blocks the APK** | `STATUS_FAILURE_BLOCKED` → **Android blocked the install.** Explain that Play Protect or the phone's security settings stopped it. Do not tell users to disable Play Protect globally; point at the installer details first. |
| **Samsung Auto Blocker (One UI 6.1+)** | The system installer may refuse. The **Get help** link opens a short page that mentions Settings → Security and privacy → Auto Blocker → turn off temporarily, then retry. |
| **Android 13+ restricted setting** | If **Allow from this source** is greyed out, show the conditional note **If the switch is greyed out, tap ⋮ → Allow restricted settings.** |
| **No system package installer** (debloated ROM) | Catch `ActivityNotFoundException` when starting the pending-user-action intent. Show **Android's installer is missing on this phone.** with **Get help**; do not crash. |
| **Work profile / secondary user** | Setup is per user. microG must be installed in the same user as T YouTube. Detect the current user's package only; do not claim the main profile's microG is available. |
| **microG settings activity not launchable** | Use the component name baked from the bundled APK at build time. Fall back to microG app info → **Open**. If both fail, show a short “Open microG from Settings → Apps” instruction; never crash. |
| **Signature spoofing off or unknown** | Expand the microG sub-panel. Do not claim **You're all set.** Use **Almost ready.** and the **Open microG settings** / **Check again** actions. |
| **Notification prompt no longer available** (denied twice on Android 13+) | Do not call `requestPermissions` again. Row shows **Off. Tap to open settings.** and deep-links to app notification settings. |
| **Battery exemption unsupported** | Row shows **Not needed on this phone.** with a dim check. Do not send the user to a screen that does not exist. |
| **SAF folder revoked / SD card removed** | Download fails with the existing downloader error plus **Folder access was removed. Choose the folder again.** Opening the picker and re-granting fixes it. |
| **App updated over v1.1.0 with microG already installed** | Do not replay the welcome. If the bundled microG is newer, Settings shows **Update available** and a one-time, non-blocking checklist hint. If it is older, keep the installed one. |
| **App data cleared, microG still installed** | `setup_welcome_seen` and `setup_complete` are gone, so the welcome appears again, but the checklist immediately shows microG as current. One **Continue** and the user is done. |
| **T YouTube uninstalled, microG left behind** | A fresh install detects the existing microG, treats it as current (or updates it), and hides its icon. No duplicate package, no data loss. |
| **No browser for Get help** | Copy the URL to the clipboard and show **Link copied.** Do not crash on `ActivityNotFoundException`. |
| **RTL locale / 200% font scale** | Layout mirrors and scrolls; no clipped copy or off-screen CTA. Test Arabic or Hebrew even if v1.2.0 ships English only. |

### 7.2 Acceptance criteria — real phone

Mark every item with the device model, Android version and build. Emulator
screenshots are not enough for the install and Play Services paths.

**A. Fresh first run, no microG**

- [ ] Fresh install on a device with no microG shows the welcome once.
- [ ] **Start setup** shows the checklist with microG **Not installed**, notifications **Turn on**, battery **Allow**.
- [ ] Tapping **Install** without the install permission shows **Allow installs**, not a system crash.
- [ ] After allowing, the preparing screen streams the bundled asset, then Android's installer appears with microG.
- [ ] Tapping **Install** in the system installer returns to the checklist with **microG installed.**
- [ ] Notifications prompt appears only after microG is ready.
- [ ] Battery row opens the exemption screen and reflects the result on return.
- [ ] **Continue** reaches **You're all set.**; **Open T YouTube** opens the app.
- [ ] The launcher shows only the T YouTube icon; microG has no launcher icon.
- [ ] Relaunching T YouTube does not show the welcome again.

**B. Permissions**

- [ ] Denying **Allow installs** returns to the checklist with **Install permission off.** and a working **Open settings** action.
- [ ] Granting the permission later and tapping **Try again** succeeds without restarting the app.
- [ ] Denying notifications leaves downloads and playback working; the row shows **Off** and opens app notification settings.
- [ ] Denying the battery exemption leaves foreground playback working; the row shows **Restricted** and recovers via app info → Battery → Unrestricted.
- [ ] Changing notification/battery settings outside the app updates the row on return, without a manual refresh.
- [ ] Revoking the install permission after setup makes the next install/update attempt show the permission sheet again.
- [ ] The download folder picker is not shown during first run; it appears only from Download Settings or a folder-access failure.
- [ ] No `MANAGE_EXTERNAL_STORAGE`, `READ_MEDIA_VIDEO` or `QUERY_ALL_PACKAGES` prompt/declaration appears in the build.

**C. microG states**

- [ ] With microG current, the checklist shows **Installed · 7.2.1** and **Continue** is enabled immediately.
- [ ] With an older microG, **Update available · x → 7.2.1** appears and the in-place update keeps microG data and signature spoofing.
- [ ] With a newer microG, no downgrade is attempted; the app uses the installed copy.
- [ ] With microG disabled, **microG is turned off.** appears; enabling it and returning updates the row.
- [ ] With the normal (icon) microG build, **Hide icon** updates to `-noicon` and the icon disappears after a launcher refresh.
- [ ] With a working but differently signed microG, setup does not force an uninstall.
- [ ] With a differently signed microG that works, setup does not force an uninstall; an update attempt shows the signature error and warns about microG data loss.

**D. Failures**

- [ ] Cancelling the system installer shows **Install cancelled.** and **Try again** starts a clean session.
- [ ] Turning on airplane mode does not block install or show an error; the offline banner is informational.
- [ ] Filling storage below the threshold shows **Not enough space.** before the session starts.
- [ ] A deliberately corrupted asset shows **The microG file is damaged.** and does not install.
- [ ] A test microG signed with a different key produces `INSTALL_FAILED_UPDATE_INCOMPATIBLE` and the signature screen, not a generic crash.
- [ ] Killing the app during preparing and reopening it either resumes or offers a clean retry; no duplicate session, no partial package.
- [ ] Rotating during preparing does not duplicate the install or lose progress.
- [ ] Every error screen has a visible exit; back never traps the user.

**E. Play Services / ABI**

- [ ] On a device with Play Services enabled, the blocker appears before the install CTA.
- [ ] **Open Play Services settings** lands on the right app page; disabling it and tapping **Check again** continues setup.
- [ ] On a device where Play Services cannot be disabled, the app explains the limitation and does not loop.
- [ ] On a 32-bit `armeabi-v7a` device, setup installs and runs with no false unsupported screen.
- [ ] On an ABI with no matching microG libs, **This phone isn't supported.** appears before any install and **Copy device info** works.
- [ ] On a Huawei/AOSP device with no Play Services, the blocker is skipped entirely.

**F. Later / re-entry**

- [ ] **Later** opens the app and shows the one-time “Setup isn't finished” snackbar only when microG is missing.
- [ ] The snackbar does not reappear on the next launch after it is dismissed.
- [ ] Settings shows **Setup & permissions** above About with an amber dot when needed.
- [ ] Tapping it opens the checklist in manage mode, with no welcome.
- [ ] Completing setup from Settings sets the dot to cyan and shows **Everything is set up.**
- [ ] The existing “MicroG Not Installed” playback error has **Set up microG** and opens the checklist.
- [ ] After a successful setup, killing and relaunching the app never shows setup UI.

**G. Accessibility / layout**

- [ ] TalkBack can complete the entire flow; each row announces title, status and action once.
- [ ] 200% font scale: all copy is readable, nothing clips, the CTA is reachable by scrolling.
- [ ] 360×640 dp screen: the welcome CTA and the checklist footer are reachable.
- [ ] Landscape: single centred column, no horizontal scroll.
- [ ] RTL: layout mirrors, back arrow points the right way, no clipped text.
- [ ] Reduced motion: no entrance animation, no looping animation.
- [ ] Status is understandable without colour (text + icon).
- [ ] All touch targets are at least 48 dp.

**H. Identity and regression**

- [ ] `aapt dump badging` still reports package `com.gold.android.youtube`, versionCode `2147483647`, same version name.
- [ ] `apksigner verify --print-certs` still reports the AOSP `testkey` SHA-256 `a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc`.
- [ ] v1.2.0 installs over v1.1.0 without uninstalling; watch history, logins and downloads are intact.
- [ ] Upgrading from v1.1.0 with working microG opens the app directly, with no welcome screen.
- [ ] Playback, sign-in, downloads, SponsorBlock, Return YouTube Dislike and the Shorts brand loop still work.
- [ ] The startup promo popup is still absent.
- [ ] The About screen shows the v1.2.0 build marker.
- [ ] microG appears in Settings → Apps after setup (needed for recovery) but not in the launcher.

**I. Performance and memory**

- [ ] The 45 MB asset is never read into a single byte array; no OOM on a 2 GB RAM device.
- [ ] Setup adds less than ~10 MB to the Java heap during the copy (check `dumpsys meminfo` before/during/after).
- [ ] Cold start to welcome is under 2 s on a mid-range phone; the checklist resolves without an ANR.
- [ ] No StrictMode disk/network violation on the main thread.
- [ ] The app's normal cold start is unchanged after setup is complete.

### 7.3 Device matrix

| Device / OS | Why |
|:--|:--|
| Pixel, Android 14 or 15 | Baseline, modern notification and restricted-settings behaviour. |
| Samsung, One UI 6.1+ | Auto Blocker, battery screens, installer differences. |
| Xiaomi / HyperOS | Aggressive background killing, unknown-source screens. |
| 32-bit `armeabi-v7a` device | Confirms the universal microG path. |
| `x86_64` emulator with an arm64-only test asset | Confirms `UNSUPPORTED_ABI` without a real unsupported phone. |
| Android 10 (API 29) | Minimum supported OS; no `POST_NOTIFICATIONS` prompt. |
| 2 GB RAM / slow eMMC | Memory and copy-time behaviour. |
| Airplane mode | Offline install and sign-in-later path. |

### 7.4 Evidence to attach to the test build

- Screen recording: fresh install → welcome → permission → system installer →
  success → app.
- Screenshot: checklist in each row state (missing, current, update, cancelled,
  signature mismatch).
- Screenshot: Play Services blocker and unsupported ABI screen.
- `aapt dump badging` and `apksigner verify --print-certs` output before/after.
- `dumpsys meminfo` before and during the copy.
- `logcat -s TytSetup` for one successful and one failed install.
- Device model, Android build, and whether Play Services was present/disabled.

---

## 8. Implementation notes (smali-patched Activity/dialog)

These notes are for the implementer. They describe surfaces and contracts, not
code. Follow the existing repo ground rules: exact-once anchors, post-condition
checks, a separate test build, and real-device evidence.

### 8.1 Find the real runtime surface first

Do not assume the class or layout name. The TEST-UI-BRIEF lesson applies here:
the patched XML/layout may not be what runs.

1. On a decoded tree, run the existing read-only `ci/inspect-apk.sh` and read
   `inspect-report.txt`. It already searches for `MicroG Not Installed`,
   microG/GMS references, launcher activities, and `RouterActivity`/`Shell`/
   `MainActivity`.
2. On a real phone, reproduce the current “MicroG Not Installed” path and dump
   the screen with `uiautomator dump` or inspect it with Layout Inspector. Note
   whether it is an `AlertDialog`, a custom dialog layout, a `DialogFragment`, or
   a full Activity.
3. Resolve the actual launcher component:
   `adb shell cmd package resolve-activity --brief -c android.intent.category.LAUNCHER com.gold.android.youtube`.
   Patch the component that really receives the launcher intent, not a guessed
   `MainActivity`.
4. Trace the string resource id or the literal text in smali to the code that
   shows the dialog. Confirm the positive-button listener before replacing it.

### 8.2 Prefer the existing path; otherwise add one lightweight Activity

**Preferred:** keep the app's current “MicroG Not Installed” dialog and change
only its positive button to **Set up microG**, launching the setup Activity in
manage mode. This reuses the app's detection and keeps the patch small. If the
current dialog opens a browser or a store page, replace that action, not the
whole dialog.

**If there is no usable path:** add one small Activity, not a fragment stack:

- Suggested name/package: `com.gold.setup.SetupActivity` (or the app's existing
  extension package). Do not rename or move existing classes.
- `android:exported="false"`, `android:launchMode="singleTop"`, label **Setup**,
  dark theme with no action bar, `android:excludeFromRecents="false"` so the
  user can return during an install.
- Do not make it the launcher. Do not add a second `MAIN/LAUNCHER` alias; that
  creates a duplicate icon and breaks the “one visible app” goal.
- Theme: derive from the app's existing dark theme. Set `windowBackground`
  `#05060A`, status/navigation bar `#05060A`, and keep the light-status-bar flag
  off so the system icons stay white. Do not add AppCompat/Material dependencies.
- The app targets SDK 37, so Android 15+ enforces edge-to-edge. Apply system bar
  insets explicitly; do not rely on the old `fitsSystemWindows` behaviour.
  Keep the primary CTA above the navigation inset.
- Predictive back: register an `OnBackInvokedCallback` or explicitly opt this
  Activity out (`android:enableOnBackInvokedCallback="false"`). A plain
  `onBackPressed` override alone is not enough on Android 14+.
- Layout: one `ScrollView` + `LinearLayout`, max width 480 dp, centred, 24 dp
  padding. A `LinearLayout` is lighter than adding a ConstraintLayout dependency
  and easier to write in smali.
- Use the existing launcher icon, typeface, and icon set. Add only XML shapes
  and colours; no new bitmaps, no new font files.
- Keep the Activity free of the YouTube app graph, playback clients, or DI
  initialization. It should start in well under 100 ms.
- State: a small controller plus `onSaveInstanceState`; no AndroidX ViewModel,
  LiveData, or static Activity references.

### 8.3 Launch gate

Patch the real launcher Activity's `onCreate` **after** `super.onCreate` but
before it inflates the YouTube UI:

- Run the fast required checks. If everything is green, set
  `setup_welcome_seen = true` and `setup_complete = true`, and continue normally.
  An existing v1.1.0 user with working microG must not see the welcome.
- If setup is needed and the welcome has not been seen, start `SetupActivity`
  and finish the host.
- If setup is needed but the welcome was already seen (the Later path), do not
  auto-open the full setup. Let the app start; the one-time snackbar and the
  Settings row handle it.

Do **not** put the gate in `Application.onCreate`: it runs for services,
receivers and background processes where starting an Activity is wrong. Do not
resurrect the removed promo dialog (`DevMsg.showMessage` / `DevMsg.show`) — it
must stay stubbed.

Warm start is not a concern: first run is a cold start, and the Later path sets
`setup_welcome_seen` so the gate does not re-open.

### 8.4 Install engine

Use `PackageInstaller`, not `ACTION_VIEW` + `FileProvider`. The latter produces
an “open with” chooser, fails on some OEMs, and gives poor status reporting.
There is **no** way to skip Android's installer confirmation on a normal,
non-privileged phone; the design embraces that with the preparing screen and
the “Android will show one confirmation” hint.

Contract:

1. Check `PackageManager.canRequestPackageInstalls()`. If false, show the
   permission sheet and deep-link to `ACTION_MANAGE_UNKNOWN_APP_SOURCES` with
   `package:<T YouTube>`. Re-check on `onResume`; never trust the toggle.
2. Check free space for about 250 MB (session copy + installed copy + margin).
3. Open the asset, create a `PackageInstaller.Session` with
   `MODE_FULL_INSTALL`, set the expected size for progress, and stream with a
   small buffer (64 KB is enough). Compute SHA-256 while streaming; do not read
   the 45 MB file into memory.
4. Compare the digest to the baked-in value. On mismatch, abandon the session
   and show **The microG file is damaged.**
5. Commit with an **explicit** broadcast `PendingIntent` to a manifest-declared,
   `exported="false"` receiver. On Android 12+, the PendingIntent must be
   mutable (`FLAG_MUTABLE | FLAG_UPDATE_CURRENT`) so the system can add the
   status extras. Keep the component explicit; never use an implicit action.
6. On `STATUS_PENDING_USER_ACTION`, start the supplied `EXTRA_INTENT` and wait.
   On return, re-query `PackageManager`; do not trust the broadcast alone.
7. On success, close the session, delete any temp file, and re-check version and
   signer. On cancel/failure, abandon the session and delete temp.
8. Persist the session id. After process death or rotation, query
   `PackageInstaller.getSessionInfo(id)` and the installed package, then choose
   success, retry, or cancelled.

Status mapping:

| Installer result | Screen |
|:--|:--|
| `STATUS_SUCCESS` | checklist, microG current |
| `STATUS_PENDING_USER_ACTION` | start the system installer |
| `STATUS_FAILURE_ABORTED` | **Install cancelled.** |
| `STATUS_FAILURE_BLOCKED` | **Android blocked the install.** |
| `STATUS_FAILURE_INCOMPATIBLE` | incompatible build (ABI or signature); show details |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | signature mismatch screen |
| `STATUS_FAILURE_INSUFFICIENT_STORAGE` | **Not enough space.** |
| `STATUS_FAILURE_INVALID` | damaged asset / invalid APK |
| `STATUS_FAILURE_CONFLICT` | generic failure with **Copy details** |
| other | **microG didn't install.** |

Also catch `ActivityNotFoundException` when launching the pending-user-action
intent (debloated ROMs may have no package installer) and show a plain
**Android's installer is missing on this phone.** message.

Do not use root, `pm install`, `Runtime.exec`, or the signature-level
`INSTALL_PACKAGES` permission. Do not set a shared user id. One session at a
time; debounce repeated taps.

### 8.5 Bundled asset and build-time metadata

- Asset path: `assets/microg/microg-7.2.1-noicon.apk` (confirm the exact
  version/file name from the official MicroG-RE release at build time).
- Add `apk` to the APK's `doNotCompress` list in `apktool.yml`. The inner APK is
  already compressed; re-compressing it saves almost nothing and forces the
  AssetManager to inflate a 45 MB stream. Stored assets stream with a small
  buffer and predictable memory.
- Expect the T YouTube APK to grow by roughly the two bundled microG APKs
  (45 MB arm64-v8a + 43 MB armeabi-v7a, ~89 MB total). That is the cost of
  one-download setup that also works on 32-bit phones. Shipping separate
  per-ABI T YouTube APKs is out of scope: the app itself stays universal.
- Bake a tiny metadata block at build time, from the bundled APK itself:
  versionCode, versionName, signer SHA-256, ABI list, the microG settings
  Activity component, and whether it has a launcher Activity. Put these in
  string resources (or a small raw XML) and verify them in CI against the asset.
  Do not parse the APK at runtime with `getPackageArchiveInfo`: that requires
  copying the 45 MB asset to disk first and slows first launch.
- The microG package id must be read from the bundled APK, not hardcoded from
  memory. Package ids have changed across microG forks. Bake it with the rest of
  the metadata.
- Add narrow `<queries>` entries for the microG package and
  `com.google.android.gms`. Without them, Android 11+ hides the packages and
  setup wrongly reports “not installed”. Never use `QUERY_ALL_PACKAGES`.
- Do not re-sign or modify the microG APK. Install the official bytes exactly.
  If the asset hash changes, update the metadata and the hash together.

### 8.6 Detection rules

Run every check off the main thread and post one result per row. The whole pass
should be well under 200 ms; there is no network call.

| Check | Rule | Failure mode to avoid |
|:--|:--|:--|
| microG installed | `getPackageInfo(microgPackage, GET_SIGNING_CERTIFICATES)` with the baked package id. | Do not use `getInstalledPackages()`; it is slow and restricted. |
| Version | `longVersionCode` compared with the baked bundled versionCode. Installed ≥ bundled is current. Never downgrade. | Do not compare versionName strings. |
| Signer | SHA-256 of the first signing certificate vs the baked value. A different signer is **info**, not a block; only a failed update becomes a signature error. | Do not compare `Signature.hashCode()` or the display subject, and do not uninstall a working microG. |
| Enabled | `ApplicationInfo.enabled` and the enabled setting. Disabled means the row says **turned off**, not “missing”. | Do not treat a disabled app as absent. |
| Icon visible | `getLaunchIntentForPackage(microgPackage) != null` or a `queryIntentActivities` for `MAIN`/`LAUNCHER` scoped to that package. | Do not scan all packages. |
| Play Services active | `com.google.android.gms` is installed, enabled, and its signer differs from the bundled microG signer. If the bundled microG itself uses `com.google.android.gms`, the signer comparison is what distinguishes them. | Do not identify Play Services by package name alone. |
| ABI | Non-empty intersection of `Build.SUPPORTED_ABIS` and the baked microG ABI list. `SUPPORTED_ABIS` reflects the actual userspace, so a 32-bit userspace on a 64-bit CPU is handled correctly. | Do not use `Build.CPU_ABI` alone; it is deprecated and can lie on 32-bit userspace. |
| Install permission | `canRequestPackageInstalls()`; only relevant when an install/update is actually needed. | Do not show the permission row on a fully green setup. |
| Spoofing / readiness | Reuse the app's existing “MicroG Not Installed” probe. If it is a `GoogleApiAvailability`-style check, call it off the main thread. Unknown is a **warning**, not a hard failure. | Do not invent a second GMS probe that disagrees with the app's playback path. |
| Offline | `ConnectivityManager` active network + validated capability where available. | Do not treat “no network” as an install blocker. |

If the spoofing probe is inconclusive, the checklist shows the sub-panel and the
success screen says **Almost ready.** A false “all set” is worse than one extra
tap.

### 8.7 Lifecycle, threading, memory

- The asset copy is the only slow operation. Keep it off the main thread.
- Preferred: a tiny foreground service (`dataSync`) with a low-priority
  notification, because a 45 MB copy on slow eMMC can outlive a rotation. If
  the app already has a download service, reuse its pattern, not its instance.
  Android 14+ needs `foregroundServiceType="dataSync"` and the normal
  `FOREGROUND_SERVICE` permission; the notification channel already exists for
  downloads or can be created once.
- Smallest-patch alternative: keep the copy in the Activity, declare
  `configChanges="orientation|screenSize|keyboardHidden"`, and persist the
  session id. Do not use a bare `Thread` with no reattachment path.
- After process death, `PackageInstaller` owns the session. Query it by id, then
  re-query the installed package. Never assume the broadcast arrived.
- Release the asset stream and session in `finally` blocks. Delete temp files on
  success, cancel and failure.
- Peak Java heap during the copy should stay in the low single-digit MB. Never
  call `readAllBytes`, never hold the APK in a `byte[]`, never decode the banner
  or screenshots.
- No disk I/O, hash verification, or `PackageManager` loop on the main thread.
- Back during preparing asks **Stop installing microG?**; back on every other
  screen is **Later** or the previous screen. Once the system installer is up,
  Android owns Back.
- Re-check on `onResume` after every system screen: unknown sources,
  notifications, battery, microG app info, Play Services app info.

### 8.8 Settings integration

- Find the root Settings list that owns the rows in
  `assets/screenshots/settings.jpg` (General … About). Insert **Setup &
  permissions** immediately above **About**.
- Reuse the existing row layout and icon size. Do not build a second settings
  screen or a PreferenceFragment.
- Add an 8 dp status dot at the end of the row, with 16 dp end margin. Reserve
  its space even when hidden so the label does not shift.
- Tapping opens `SetupActivity` with an extra such as `mode=manage`. Manage mode
  skips the welcome and the automatic success screen.
- If the row list is hardcoded, add one row model; if it is XML, add one entry.
  Do not reorder the existing rows.
- The row is always visible, including after success. It is the recovery path
  for a later microG uninstall.
- Keep the row label short so it does not wrap at 200% font scale. If it wraps,
  the row height may grow; that is acceptable, clipping is not.

### 8.9 Strings, resources and identity

- Every user-visible string goes in `res/values/strings.xml` with a
  `tyt_setup_` prefix. No hardcoded English in smali. v1.2.0 ships English; the
  existing 82-locale rebrand pipeline can translate these later.
- Add `tyt_setup_*` colours and XML shapes. Do not modify shared brand resources
  that other screens use; a change there can regress the whole app.
- Use `start`/`end` in layouts, not `left`/`right`.
- Keep all new classes in one small package. Do not rename or move existing
  classes; obfuscation-aware patches should use the names from the decoded tree,
  not guessed names.
- The only manifest additions are: the setup Activity, the installer broadcast
  receiver, `<queries>` entries, `REQUEST_INSTALL_PACKAGES`,
  `POST_NOTIFICATIONS`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, and — only if the
  copy runs in a service — `FOREGROUND_SERVICE`,
  `FOREGROUND_SERVICE_DATA_SYNC` and the service declaration. Nothing else.
- Do **not** change the package name, versionCode, versionName, signing key, or
  existing launcher component.
- The v1.2.0 marker is an About-screen string only. `versionCode` stays
  `2147483647`.
- If the app uses an app bundle/split delivery, stop and re-scope: this design
  assumes the universal APK described in the README.

### 8.10 Documentation and legal follow-ups

Bundling changes claims that are currently true in the repo:

- README and `docs/index.html` say microG must be downloaded and installed
  **first**, and the legal section says microG is “not bundled or redistributed
  here”. Both become false in v1.2.0.
- Update the install tutorial to: install T YouTube → open it → tap **Start
  setup** → allow installs → tap **Install** in Android's installer → done.
- Update the FAQ: “Why does it say MicroG Not Installed?” now points at
  Settings → Setup & permissions.
- Update size/download numbers (the APK grows by roughly the microG asset).
- microG-RE is Apache-2.0; bundling is allowed with attribution. Include its
  license text in the app's open-source licenses screen and/or
  `assets/licenses/microg-RE.txt`, and keep the credit in the README.
- Release notes must state plainly: **two packages are installed; only one icon
  is visible.** Do not market it as a single-package merge.
- Do not update the stable v1.1.0 release; this is a v1.2.0 test build with
  real-device evidence before promotion.

### 8.11 Non-goals and open items

**Non-goals for v1.2.0**

- Silent install without Android's confirmation. Not possible without device
  owner/root privileges.
- Merging microG into the T YouTube package. Not possible; see section 1.
- Per-ABI T YouTube APKs. One universal APK with one universal microG asset.
- A light theme, a new font, new bitmap artwork, or an onboarding carousel.
- Analytics, remote config, or a network check during setup.
- Requesting broad storage, location, contacts or `QUERY_ALL_PACKAGES`.

**Confirm at implementation time — do not guess**

1. The exact microG package id, settings Activity component, versionCode and
   signer in the bundled `-noicon` APK.
2. Whether the app's existing “MicroG Not Installed” probe can also confirm
   signature spoofing, or whether it only checks that a GMS provider responds.
3. Which component really handles the launcher intent, and how early it can
   redirect without initializing the YouTube UI.
4. Whether the root Settings list is XML, a hardcoded array, or an adapter, and
   where the row should be inserted.
5. Whether the existing download service can host the asset copy, or whether a
   new small `dataSync` service is needed.
6. Whether the bundled `-noicon` APK fits the existing APK size/release budget;
   if not, the fallback is a per-ABI release matrix, which is a separate design.

If any of these cannot be verified, stop and report it. Do not ship a guessed
package id, a guessed Activity name, or a half-applied smali patch.
