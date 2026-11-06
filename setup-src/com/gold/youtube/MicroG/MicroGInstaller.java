package com.gold.youtube.MicroG;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.content.pm.SigningInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import android.util.Log;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * Framework-only microG installer. No AndroidX, no Material, no reflection.
 *
 * The bundled APK is streamed straight from the APK asset into a
 * PackageInstaller session, so the 45 MB file is never held in memory.
 */
final class MicroGInstaller {
    private static final String TAG = "TytSetup";

    static final String MICROG_PACKAGE = "app.revanced.android.gms";
    static final long MICROG_VERSION_CODE = 255070304L;
    static final String MICROG_VERSION_NAME = "7.3.0";

    /** Official MicroG-RE signing certificate (SHA-256). */
    static final String OFFICIAL_CERT_SHA256 =
            "0b6c9515afb195fac59601696ba0a7907a0b217ccf720b43148427ccf64343e7";

    static final String ACTION_INSTALL_RESULT =
            "com.gold.youtube.MicroG.INSTALL_RESULT";

    private static final String ASSET_DIR = "microg/";
    private static final String ASSET_ARM64 =
            ASSET_DIR + "microg-7.3.0-noicon-arm64-v8a.apk";
    private static final String ASSET_V7 =
            ASSET_DIR + "microg-7.3.0-noicon-armeabi-v7a.apk";

    static final String SHA_ARM64 =
            "98e2de8c1543fb2736971b8ba307c2b58c092c96fb6dcebe3c3b8a4538151a23";
    static final String SHA_V7 =
            "af89d740a58136779f7406b6f00a546880ee7f3c7472b2a886239ee5a6e43a86";

    static final long SIZE_ARM64 = 45648640L;
    static final long SIZE_V7 = 43445006L;

    private static final String[] CONFLICTING_PACKAGES = {
            "org.microg.gms",
            "com.mgoogle.android.gms",
    };

    private static volatile boolean cancelRequested = false;

    interface InstallCallback {
        void onProgress(int percent);

        void onWaitingForUser();

        void onFailure(String title, String message, boolean signatureMismatch);
    }

    private MicroGInstaller() {
    }

    /** @return the asset path for this device, or null when no bundled ABI matches. */
    static String pickAsset() {
        String[] abis = Build.SUPPORTED_ABIS;
        if (abis == null) {
            return null;
        }
        for (String abi : abis) {
            if ("arm64-v8a".equals(abi)) {
                return ASSET_ARM64;
            }
            if ("armeabi-v7a".equals(abi)) {
                return ASSET_V7;
            }
        }
        return null;
    }

    static String shaFor(String asset) {
        return ASSET_ARM64.equals(asset) ? SHA_ARM64 : SHA_V7;
    }

    static long sizeFor(String asset) {
        return ASSET_ARM64.equals(asset) ? SIZE_ARM64 : SIZE_V7;
    }

    static boolean isInstalled(Context context) {
        try {
            context.getPackageManager().getPackageInfo(MICROG_PACKAGE, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    static boolean isEnabled(Context context) {
        try {
            ApplicationInfo info = context.getPackageManager()
                    .getApplicationInfo(MICROG_PACKAGE, 0);
            return info.enabled;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    static long installedVersionCode(Context context) {
        try {
            return context.getPackageManager()
                    .getPackageInfo(MICROG_PACKAGE, 0).versionCode;
        } catch (PackageManager.NameNotFoundException e) {
            return -1L;
        }
    }

    static String installedVersionName(Context context) {
        try {
            PackageInfo info = context.getPackageManager()
                    .getPackageInfo(MICROG_PACKAGE, 0);
            return info.versionName == null ? "" : info.versionName;
        } catch (PackageManager.NameNotFoundException e) {
            return "";
        }
    }

    static boolean isReady(Context context) {
        return isInstalled(context)
                && isEnabled(context)
                && installedVersionCode(context) >= MICROG_VERSION_CODE;
    }

    /**
     * True when the installed microG is signed by the official MicroG-RE key.
     * A different signer is not a blocker if the build already works, but it does
     * prevent an in-place update.
     */
    static boolean isOfficialSignature(Context context) {
        try {
            PackageManager pm = context.getPackageManager();
            PackageInfo info = pm.getPackageInfo(
                    MICROG_PACKAGE, PackageManager.GET_SIGNING_CERTIFICATES);
            SigningInfo signingInfo = info.signingInfo;
            Signature[] signatures = null;
            if (signingInfo != null) {
                signatures = signingInfo.hasMultipleSigners()
                        ? signingInfo.getApkContentsSigners()
                        : signingInfo.getSigningCertificateHistory();
            }
            if (signatures == null) {
                signatures = info.signatures;
            }
            if (signatures == null) {
                return false;
            }
            for (Signature signature : signatures) {
                if (OFFICIAL_CERT_SHA256.equalsIgnoreCase(sha256Hex(signature.toByteArray()))) {
                    return true;
                }
            }
            return false;
        } catch (Exception e) {
            Log.w(TAG, "Could not read microG signature", e);
            return false;
        }
    }

    static String conflictingPackage(Context context) {
        for (String packageName : CONFLICTING_PACKAGES) {
            try {
                context.getPackageManager().getPackageInfo(packageName, 0);
                return packageName;
            } catch (PackageManager.NameNotFoundException ignored) {
                // Keep looking.
            }
        }
        return null;
    }

    static boolean canRequestPackageInstalls(Context context) {
        try {
            return context.getPackageManager().canRequestPackageInstalls();
        } catch (Exception e) {
            Log.w(TAG, "Could not read install permission", e);
            return false;
        }
    }

    static boolean hasEnoughSpace(Context context, long bytes) {
        long free;
        try {
            File dir = context.getFilesDir();
            free = dir == null ? 0L : dir.getUsableSpace();
        } catch (Exception e) {
            free = 0L;
        }
        return free > bytes * 2L + 50L * 1024L * 1024L;
    }

    static void openInstallPermissionSettings(Context context) {
        Intent intent = new Intent(
                Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                Uri.parse("package:" + context.getPackageName()));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            context.startActivity(intent);
        } catch (Exception e) {
            openAppInfo(context, context.getPackageName());
        }
    }

    static void openMicroGSettings(Context context) {
        Intent intent = new Intent();
        intent.setComponent(new ComponentName(
                MICROG_PACKAGE, "org.microg.gms.ui.SettingsActivity"));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            context.startActivity(intent);
            return;
        } catch (Exception ignored) {
            // Try the next surface.
        }

        intent = new Intent(Intent.ACTION_APPLICATION_PREFERENCES)
                .setPackage(MICROG_PACKAGE)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            context.startActivity(intent);
            return;
        } catch (Exception ignored) {
            // Try the launch intent.
        }

        Intent launch = context.getPackageManager()
                .getLaunchIntentForPackage(MICROG_PACKAGE);
        if (launch != null) {
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            try {
                context.startActivity(launch);
                return;
            } catch (Exception ignored) {
                // Fall through to app info.
            }
        }
        openAppInfo(context, MICROG_PACKAGE);
    }

    static void openAppInfo(Context context, String packageName) {
        Intent intent = new Intent(
                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:" + packageName));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            context.startActivity(intent);
        } catch (Exception e) {
            Log.w(TAG, "No app info screen for " + packageName, e);
        }
    }

    static void uninstallMicroG(Context context) {
        Intent intent = new Intent(
                Intent.ACTION_UNINSTALL_PACKAGE,
                Uri.parse("package:" + MICROG_PACKAGE));
        intent.putExtra("android.intent.extra.UNINSTALL_ALL_USERS", true);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            context.startActivity(intent);
        } catch (Exception e) {
            openAppInfo(context, MICROG_PACKAGE);
        }
    }

    static boolean isIgnoringBatteryOptimizations(Context context) {
        try {
            PowerManager powerManager =
                    (PowerManager) context.getSystemService(Context.POWER_SERVICE);
            return powerManager != null
                    && powerManager.isIgnoringBatteryOptimizations(MICROG_PACKAGE);
        } catch (Exception e) {
            Log.w(TAG, "Could not read battery exemption", e);
            return false;
        }
    }

    static void requestBatteryExemption(Context context) {
        Intent intent = new Intent(
                Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                Uri.parse("package:" + MICROG_PACKAGE));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            context.startActivity(intent);
        } catch (Exception e) {
            Intent list = new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS);
            list.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            try {
                context.startActivity(list);
            } catch (Exception ignored) {
                openAppInfo(context, MICROG_PACKAGE);
            }
        }
    }

    static void cancelInstall() {
        cancelRequested = true;
    }

    static void resetCancel() {
        cancelRequested = false;
    }

    static void abandonStaleSession(Context context) {
        int sessionId = SetupPrefs.getInt(
                context, SetupPrefs.KEY_INSTALL_SESSION, -1);
        if (sessionId == -1) {
            return;
        }
        try {
            PackageInstaller installer = context.getPackageManager().getPackageInstaller();
            PackageInstaller.SessionInfo info = installer.getSessionInfo(sessionId);
            if (info != null) {
                installer.abandonSession(sessionId);
            }
        } catch (Exception e) {
            Log.w(TAG, "Could not clean stale installer session", e);
        } finally {
            SetupPrefs.putInt(context, SetupPrefs.KEY_INSTALL_SESSION, -1);
        }
    }

    static void startInstall(final Activity activity, final InstallCallback callback) {
        final String asset = pickAsset();
        final Handler main = new Handler(Looper.getMainLooper());
        cancelRequested = false;

        if (asset == null) {
            callback.onFailure(
                    "This phone isn't supported.",
                    "The microG inside this build doesn't match your phone's processor. "
                            + "Install the universal T YouTube build from the release page.",
                    false);
            return;
        }

        final long expectedSize = sizeFor(asset);
        final String expectedSha = shaFor(asset);

        if (!hasEnoughSpace(activity, expectedSize)) {
            callback.onFailure(
                    "Not enough space.",
                    "microG needs about 250 MB free. Free up some space, then try again.",
                    false);
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                PackageInstaller installer = null;
                PackageInstaller.Session session = null;
                int sessionId = -1;
                try {
                    installer = activity.getPackageManager().getPackageInstaller();
                    PackageInstaller.SessionParams params =
                            new PackageInstaller.SessionParams(
                                    PackageInstaller.SessionParams.MODE_FULL_INSTALL);
                    params.setAppPackageName(MICROG_PACKAGE);
                    params.setSize(expectedSize);

                    sessionId = installer.createSession(params);
                    SetupPrefs.putInt(
                            activity, SetupPrefs.KEY_INSTALL_SESSION, sessionId);
                    session = installer.openSession(sessionId);

                    InputStream in = activity.getAssets().open(asset);
                    OutputStream out = session.openWrite("microg.apk", 0, expectedSize);
                    MessageDigest digest = MessageDigest.getInstance("SHA-256");
                    byte[] buffer = new byte[64 * 1024];
                    long written = 0L;
                    int lastPercent = -1;
                    int read;
                    try {
                        while ((read = in.read(buffer)) > 0) {
                            if (cancelRequested) {
                                throw new IOException("Install cancelled");
                            }
                            out.write(buffer, 0, read);
                            digest.update(buffer, 0, read);
                            written += read;
                            int percent = expectedSize <= 0
                                    ? 0
                                    : (int) (written * 100L / expectedSize);
                            if (percent != lastPercent) {
                                lastPercent = percent;
                                postProgress(main, callback, percent);
                            }
                        }
                        session.fsync(out);
                    } finally {
                        try {
                            out.close();
                        } catch (Exception ignored) {
                        }
                        try {
                            in.close();
                        } catch (Exception ignored) {
                        }
                    }

                    String actualSha = toHex(digest.digest());
                    if (!expectedSha.equalsIgnoreCase(actualSha)) {
                        throw new IOException("Bundled asset hash mismatch");
                    }
                    if (written != expectedSize) {
                        throw new IOException("Bundled asset size mismatch");
                    }

                    Intent result = new Intent(activity, InstallResultReceiver.class);
                    result.setAction(ACTION_INSTALL_RESULT);
                    int flags = PendingIntent.FLAG_UPDATE_CURRENT;
                    if (Build.VERSION.SDK_INT >= 31) {
                        flags |= PendingIntent.FLAG_MUTABLE;
                    }
                    PendingIntent pendingIntent = PendingIntent.getBroadcast(
                            activity, sessionId, result, flags);
                    session.commit(pendingIntent.getIntentSender());
                    postWaiting(main, callback);
                } catch (final Exception e) {
                    Log.e(TAG, "microG install failed", e);
                    if (session != null) {
                        try {
                            session.abandon();
                        } catch (Exception ignored) {
                        }
                    }
                    if (sessionId != -1 && installer != null) {
                        try {
                            installer.abandonSession(sessionId);
                        } catch (Exception ignored) {
                        }
                    }
                    SetupPrefs.putInt(
                            activity, SetupPrefs.KEY_INSTALL_SESSION, -1);
                    final String message = e.getMessage() == null
                            ? e.getClass().getSimpleName()
                            : e.getMessage();
                    if ("Install cancelled".equals(message)) {
                        return;
                    }
                    main.post(new Runnable() {
                        @Override
                        public void run() {
                            callback.onFailure(
                                    "microG didn't install.",
                                    "Something stopped the installer. "
                                            + "Try again — if it keeps happening, send us the details.\n\n"
                                            + message,
                                    false);
                        }
                    });
                } finally {
                    if (session != null) {
                        try {
                            session.close();
                        } catch (Exception ignored) {
                        }
                    }
                }
            }
        }, "tyt-microg-install").start();
    }

    private static void postProgress(
            Handler main, final InstallCallback callback, final int percent) {
        main.post(new Runnable() {
            @Override
            public void run() {
                callback.onProgress(percent);
            }
        });
    }

    private static void postWaiting(Handler main, final InstallCallback callback) {
        main.post(new Runnable() {
            @Override
            public void run() {
                callback.onWaitingForUser();
            }
        });
    }

    static String toHex(byte[] bytes) {
        StringBuilder builder = new StringBuilder(bytes.length * 2);
        for (byte value : bytes) {
            builder.append(Character.forDigit((value >> 4) & 0xF, 16));
            builder.append(Character.forDigit(value & 0xF, 16));
        }
        return builder.toString().toLowerCase(Locale.US);
    }

    static String sha256Hex(byte[] data) {
        try {
            return toHex(MessageDigest.getInstance("SHA-256").digest(data));
        } catch (Exception e) {
            return "";
        }
    }

    static String readableSize(long bytes) {
        if (bytes >= 1024L * 1024L) {
            return String.format(Locale.US, "%.0f MB", bytes / (1024.0 * 1024.0));
        }
        return bytes + " bytes";
    }
}
