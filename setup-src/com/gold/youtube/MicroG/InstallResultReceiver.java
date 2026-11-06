package com.gold.youtube.MicroG;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.util.Log;

/**
 * Receives the PackageInstaller result for the bundled microG install.
 *
 * The PendingIntent is explicit and mutable, so this receiver is never exported.
 */
public final class InstallResultReceiver extends BroadcastReceiver {
    private static final String TAG = "TytSetup";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            return;
        }
        int status = intent.getIntExtra(
                PackageInstaller.EXTRA_STATUS, -1);
        String message = intent.getStringExtra(
                PackageInstaller.EXTRA_STATUS_MESSAGE);
        Log.i(TAG, "installer result status=" + status + " message=" + message);

        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirmation = intent.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirmation == null) {
                postResult(context, status, "Installer confirmation was missing");
                return;
            }
            confirmation.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            try {
                context.startActivity(confirmation);
            } catch (Exception e) {
                Log.e(TAG, "No system installer on this device", e);
                postResult(context, status, "Android's installer is missing on this phone.");
            }
            return;
        }

        if (status == PackageInstaller.STATUS_SUCCESS) {
            SetupPrefs.putInt(context, SetupPrefs.KEY_INSTALL_SESSION, -1);
            SetupPrefs.putBoolean(context, SetupPrefs.KEY_PENDING_INSTALL, false);
            SetupPrefs.putString(context, SetupPrefs.KEY_LAST_MESSAGE, "");
        } else {
            SetupPrefs.putInt(context, SetupPrefs.KEY_INSTALL_SESSION, -1);
            SetupPrefs.putBoolean(context, SetupPrefs.KEY_PENDING_INSTALL, false);
            SetupPrefs.putString(
                    context, SetupPrefs.KEY_LAST_MESSAGE,
                    message == null ? "" : message);
        }
        SetupPrefs.putInt(context, SetupPrefs.KEY_LAST_STATUS, status);

        postResult(context, status, message);
    }

    private static void postResult(Context context, int status, String message) {
        Intent ui = new Intent(context, MicroGActivity.class);
        ui.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        ui.putExtra(MicroGActivity.EXTRA_INSTALL_STATUS, status);
        if (message != null) {
            ui.putExtra(MicroGActivity.EXTRA_INSTALL_MESSAGE, message);
        }
        try {
            context.startActivity(ui);
        } catch (Exception e) {
            Log.e(TAG, "Could not reopen setup after install", e);
        }
    }
}
