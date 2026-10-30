# T YouTube v1.0.1 — stable update

The Download crash is fixed, and everything tested in `test-fix-3` is now the
stable build.

## What changed

- **Tapping Download no longer closes the app.** The 80-character filename cap
  added in test-fix-2 had its comparison inverted: titles shorter than 80
  characters were still passed to `substring(0, 80)`, which threw
  `StringIndexOutOfBoundsException` as soon as the download dialog opened. The
  cap now applies only to titles that are actually longer than 80 characters.
- **Downloads complete.** Titles are cleaned with the app's filename charset
  before saving, and the downloader's iOS stream source is enabled, giving the
  quality picker extra unthrottled stream URLs.
- **Seeking long videos works.** The default playback client is now **visionOS**
  instead of Android Reel. Jumps to 20+ minutes resume at the selected quality
  instead of freezing and dropping to 144p/360p.
- **Shorts no longer stall.** Shorts use the same stream resolver, so they get
  the same fix.
- **Dark theme by default.** Settings → General → Appearance defaults to Dark.
- **Seekbar in the logo colours.** `#00FCFF` primary, `#F3024E` accent, enabled
  by default.
- **Picture-in-picture.** The PiP behaviour from test-fix-1 is kept: press Home
  and the video keeps playing in a floating window.

No new menus or buttons. The package name, version name (`21.26.364`), version
code and AOSP `testkey` signature are unchanged, so this installs directly over
v1.0.0 or any earlier test build with your data intact.

## Verify

- APK: `T-YouTube-v1.0.1.apk`
- Size: 222,566,961 bytes (212 MB)
- SHA-256: `71B0F782702129A0DDCC80EE0A7150F52FE0099671AB62692766B1C605EBE7FE`

This is the exact APK that passed testing as `test-fix-3`; it is promoted
without rebuilding, so the checksum matches the build testers installed.
