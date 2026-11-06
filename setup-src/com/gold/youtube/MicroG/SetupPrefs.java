package com.gold.youtube.MicroG;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Small preference store for the first-run setup flow.
 *
 * No account data, no package list, no signature material is stored here.
 */
final class SetupPrefs {
    private static final String FILE = "tyt_setup";

    static final String KEY_WELCOME_SEEN = "welcome_seen";
    static final String KEY_SETUP_COMPLETE = "setup_complete";
    static final String KEY_SETUP_LATER = "setup_later";
    static final String KEY_INSTALL_SESSION = "install_session";
    static final String KEY_PENDING_INSTALL = "pending_install";
    static final String KEY_LAST_STATUS = "last_status";
    static final String KEY_LAST_MESSAGE = "last_message";
    static final String KEY_NOTIF_ASKED = "notif_asked";

    private SetupPrefs() {
    }

    static SharedPreferences get(Context context) {
        return context.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }

    static boolean getBoolean(Context context, String key, boolean fallback) {
        return get(context).getBoolean(key, fallback);
    }

    static void putBoolean(Context context, String key, boolean value) {
        get(context).edit().putBoolean(key, value).apply();
    }

    static int getInt(Context context, String key, int fallback) {
        return get(context).getInt(key, fallback);
    }

    static void putInt(Context context, String key, int value) {
        get(context).edit().putInt(key, value).apply();
    }

    static String getString(Context context, String key, String fallback) {
        return get(context).getString(key, fallback);
    }

    static void putString(Context context, String key, String value) {
        get(context).edit().putString(key, value).apply();
    }
}
