package com.gold.youtube.MicroG;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * First-run setup for the bundled microG-RE package.
 *
 * The activity is the launcher target, so it must decide within a few
 * milliseconds whether to show setup or forward straight to YouTube.
 *
 * Framework-only: no AndroidX, no Material, no resource lookups.
 */
public final class MicroGActivity extends Activity {
    public static final String EXTRA_MODE = "mode";
    public static final String MODE_MANAGE = "manage";
    public static final String EXTRA_INSTALL_STATUS = "install_status";
    public static final String EXTRA_INSTALL_MESSAGE = "install_message";

    private static final String MAIN_ACTIVITY =
            "com.google.android.apps.youtube.app.watchwhile.MainActivity";
    private static final String RELEASE_PAGE =
            "https://github.com/engrtarun/T-YouTube/releases/latest";
    private static final int REQ_NOTIFICATIONS = 1001;

    private static final int SCREEN_WELCOME = 0;
    private static final int SCREEN_CHECKLIST = 1;
    private static final int SCREEN_PERMISSION = 2;
    private static final int SCREEN_PREPARING = 3;
    private static final int SCREEN_SUCCESS = 4;
    private static final int SCREEN_ERROR = 5;
    private static final int SCREEN_UNSUPPORTED = 6;

    private static final int BG = 0xFF05060A;
    private static final int SURFACE = 0xFF0F1219;
    private static final int TEXT = 0xFFE8EBF2;
    private static final int MUTED = 0xFF98A0B3;
    private static final int DIM = 0xFF6B7488;
    private static final int RED = 0xFFF3024E;
    private static final int CYAN = 0xFF00FCFF;
    private static final int AMBER = 0xFFF5A524;
    private static final int GREEN = 0xFF34D399;

    private FrameLayout root;
    private LinearLayout content;

    private int screen = SCREEN_WELCOME;
    private boolean manageMode;
    private boolean awaitingPermission;
    private boolean awaitingSystemInstaller;
    private boolean permissionAttempted;
    private boolean pendingContinue;
    private boolean installRunning;
    private boolean cancelled;
    private int preparingPercent;
    private String banner = "";

    private String errorTitle = "";
    private String errorBody = "";
    private String errorPrimary = "";
    private Runnable errorPrimaryAction;
    private String errorSecondary = "";
    private Runnable errorSecondaryAction;
    private boolean errorShowUninstall;

    private TextView[] stepViews;
    private ProgressBar progressBar;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        applyWindow();
        root = new FrameLayout(this);
        root.setBackgroundColor(BG);
        setContentView(root);
        applyInsets();
        manageMode = MODE_MANAGE.equals(getIntent().getStringExtra(EXTRA_MODE));
        if (handleInstallResult(getIntent())) {
            return;
        }
        route();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (MODE_MANAGE.equals(intent.getStringExtra(EXTRA_MODE))) {
            manageMode = true;
        }
        if (handleInstallResult(intent)) {
            return;
        }
        if (manageMode) {
            showChecklist();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (screen == SCREEN_PERMISSION) {
            if (MicroGInstaller.canRequestPackageInstalls(this)) {
                awaitingPermission = false;
                SetupPrefs.putBoolean(this, SetupPrefs.KEY_PENDING_INSTALL, false);
                startPreparing();
                return;
            }
            if (permissionAttempted) {
                showPermission();
                return;
            }
        }
        if (awaitingPermission && MicroGInstaller.canRequestPackageInstalls(this)) {
            awaitingPermission = false;
            SetupPrefs.putBoolean(this, SetupPrefs.KEY_PENDING_INSTALL, false);
            startPreparing();
            return;
        }
        if (screen == SCREEN_PREPARING || awaitingSystemInstaller) {
            if (MicroGInstaller.isReady(this)) {
                onInstallSuccess();
                return;
            }
        }
        if (screen == SCREEN_CHECKLIST) {
            showChecklist();
        }
    }

    @Override
    public void onBackPressed() {
        switch (screen) {
            case SCREEN_WELCOME:
                later();
                return;
            case SCREEN_CHECKLIST:
                later();
                return;
            case SCREEN_PERMISSION:
                awaitPermissionLater();
                return;
            case SCREEN_PREPARING:
                confirmCancel();
                return;
            case SCREEN_SUCCESS:
                openApp();
                return;
            case SCREEN_ERROR:
            case SCREEN_UNSUPPORTED:
                showChecklist();
                return;
            default:
                super.onBackPressed();
        }
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != REQ_NOTIFICATIONS) {
            return;
        }
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_NOTIF_ASKED, true);
        if (pendingContinue) {
            pendingContinue = false;
            showSuccess();
        } else if (screen == SCREEN_CHECKLIST) {
            showChecklist();
        }
    }

    // ---------------------------------------------------------------- routing

    private void route() {
        if (manageMode) {
            showChecklist();
            return;
        }
        if (MicroGInstaller.isReady(this)) {
            SetupPrefs.putBoolean(this, SetupPrefs.KEY_WELCOME_SEEN, true);
            SetupPrefs.putBoolean(this, SetupPrefs.KEY_SETUP_COMPLETE, true);
            openApp();
            return;
        }
        if (MicroGInstaller.pickAsset() == null) {
            showUnsupported();
            return;
        }
        if (SetupPrefs.getBoolean(this, SetupPrefs.KEY_WELCOME_SEEN, false)) {
            openApp();
            return;
        }
        showWelcome();
    }

    private void openApp() {
        Intent incoming = getIntent();
        Intent target = incoming == null
                ? new Intent(Intent.ACTION_MAIN)
                : new Intent(incoming);
        target.setClassName(this, MAIN_ACTIVITY);
        target.removeExtra(EXTRA_MODE);
        target.removeExtra(EXTRA_INSTALL_STATUS);
        target.removeExtra(EXTRA_INSTALL_MESSAGE);
        if (target.getAction() == null) {
            target.setAction(Intent.ACTION_MAIN);
            target.addCategory(Intent.CATEGORY_LAUNCHER);
        }
        target.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        try {
            startActivity(target);
        } catch (Exception ignored) {
            try {
                Intent plain = new Intent(this, Class.forName(MAIN_ACTIVITY));
                startActivity(plain);
            } catch (Exception second) {
                finish();
                return;
            }
        }
        finish();
    }

    private void later() {
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_WELCOME_SEEN, true);
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_SETUP_LATER, true);
        if (manageMode) {
            finish();
        } else {
            openApp();
        }
    }

    // ---------------------------------------------------------------- welcome

    private void showWelcome() {
        screen = SCREEN_WELCOME;
        prepareContent();

        ImageView icon = new ImageView(this);
        try {
            icon.setImageDrawable(getPackageManager().getApplicationIcon(getPackageName()));
        } catch (Exception ignored) {
            icon.setImageResource(android.R.drawable.sym_def_app_icon);
        }
        content.addView(icon, centerLp(72, 0));

        TextView wordmark = label("T YouTube", 20, TEXT, Typeface.BOLD);
        wordmark.setGravity(Gravity.CENTER);
        content.addView(wordmark, centerLp(ViewGroup.LayoutParams.WRAP_CONTENT, 12));

        TextView headline = label("One quick setup.", 28, TEXT, Typeface.BOLD);
        headline.setGravity(Gravity.CENTER);
        content.addView(headline, centerLp(ViewGroup.LayoutParams.WRAP_CONTENT, 24));

        TextView body = label(
                "T YouTube runs on microG, a small service that replaces Google Play Services. "
                        + "It's already inside this app - we just need to install it.",
                15, MUTED, Typeface.NORMAL);
        body.setLineSpacing(dp(4), 1f);
        content.addView(body, matchLp(16));

        TextView preview = label(
                "Install microG  Â·  Notifications  Â·  Battery",
                13, DIM, Typeface.BOLD);
        preview.setGravity(Gravity.CENTER);
        content.addView(preview, matchLp(20));

        TextView start = primaryButton("Start setup", true);
        start.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                SetupPrefs.putBoolean(MicroGActivity.this, SetupPrefs.KEY_WELCOME_SEEN, true);
                showChecklist();
            }
        });
        content.addView(start, matchHeightLp(52, 28));

        TextView later = textButton("Later", CYAN);
        later.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                later();
            }
        });
        content.addView(later, matchHeightLp(48, 4));

        TextView footnote = label(
                "microG stays a separate app. Its icon is hidden, so you'll only see T YouTube.",
                12, DIM, Typeface.NORMAL);
        footnote.setGravity(Gravity.CENTER);
        footnote.setLineSpacing(dp(2), 1f);
        content.addView(footnote, matchLp(24));

        TextView caption = label("About a minute Â· works offline", 12, DIM, Typeface.NORMAL);
        caption.setGravity(Gravity.CENTER);
        content.addView(caption, matchLp(12));
    }

    // -------------------------------------------------------------- checklist

    private void showChecklist() {
        screen = SCREEN_CHECKLIST;
        prepareContent();
        addTopBar(manageMode ? "Check again" : "Later", new Runnable() {
            @Override
            public void run() {
                if (manageMode) {
                    showChecklist();
                } else {
                    later();
                }
            }
        });

        boolean ready = MicroGInstaller.isReady(this);
        TextView headline = label(
                manageMode && ready ? "Everything is set up." : "3 small steps.",
                24, TEXT, Typeface.BOLD);
        content.addView(headline, matchLp(8));

        TextView subhead = label(
                manageMode && ready
                        ? "microG is installed and up to date."
                        : "microG is required. The other two take a tap.",
                14, MUTED, Typeface.NORMAL);
        content.addView(subhead, matchLp(6));

        if (!TextUtils.isEmpty(banner)) {
            TextView bannerView = label(banner, 13, GREEN, Typeface.BOLD);
            bannerView.setBackground(rounded(0x2234D399, 10, 0));
            bannerView.setPadding(dp(12), dp(10), dp(12), dp(10));
            content.addView(bannerView, matchLp(12));
            banner = "";
        }

        addMicroGRow();
        addNotificationRow();
        addBatteryRow();

        final boolean canContinue = ready;
        String primaryLabel;
        if (installRunning) {
            primaryLabel = "Installing...";
        } else if (manageMode) {
            primaryLabel = "Done";
        } else {
            primaryLabel = "Continue";
        }
        TextView primary = primaryButton(primaryLabel, canContinue || manageMode);
        primary.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (manageMode) {
                    finish();
                } else {
                    continueFromChecklist();
                }
            }
        });
        content.addView(primary, matchHeightLp(52, 20));

        String helper;
        if (installRunning) {
            helper = "This takes a few seconds.";
        } else if (!canContinue) {
            helper = "Install microG to continue.";
        } else if (manageMode) {
            helper = "Last checked just now.";
        } else {
            helper = "Tap any row to change it.";
        }
        TextView helperView = label(helper, 12, DIM, Typeface.NORMAL);
        helperView.setGravity(Gravity.CENTER);
        content.addView(helperView, matchLp(8));

        TextView note = label(
                "You can change all of this later in Settings > Setup & permissions.",
                12, DIM, Typeface.NORMAL);
        note.setGravity(Gravity.CENTER);
        note.setLineSpacing(dp(2), 1f);
        content.addView(note, matchLp(16));
    }

    private void addMicroGRow() {
        boolean installed = MicroGInstaller.isInstalled(this);
        boolean enabled = MicroGInstaller.isEnabled(this);
        long versionCode = MicroGInstaller.installedVersionCode(this);
        String versionName = MicroGInstaller.installedVersionName(this);
        boolean current = installed && enabled
                && versionCode >= MicroGInstaller.MICROG_VERSION_CODE;
        boolean outdated = installed && enabled
                && versionCode < MicroGInstaller.MICROG_VERSION_CODE;
        boolean official = installed && MicroGInstaller.isOfficialSignature(this);
        boolean permissionOff = !MicroGInstaller.canRequestPackageInstalls(this);
        int lastStatus = SetupPrefs.getInt(
                this, SetupPrefs.KEY_LAST_STATUS, Integer.MIN_VALUE);
        boolean aborted = lastStatus == PackageInstaller.STATUS_FAILURE_ABORTED;

        String subtitle;
        String action;
        Runnable actionRun;

        if (!installed) {
            subtitle = aborted
                    ? "Install cancelled. Try again."
                    : "Not installed. Required for sign-in and playback.";
            action = aborted ? "Try again" : "Install";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    beginInstallFlow();
                }
            };
        } else if (!enabled) {
            subtitle = "microG is turned off.";
            action = "Turn on";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    MicroGInstaller.openAppInfo(MicroGActivity.this, MicroGInstaller.MICROG_PACKAGE);
                }
            };
        } else if (outdated) {
            subtitle = "Update available Â· " + versionName + " > 7.3.0";
            action = "Update";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    beginInstallFlow();
                }
            };
        } else if (!official) {
            subtitle = "Installed Â· " + versionName + " (different build).";
            action = "Details";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    showDifferentBuildDialog();
                }
            };
        } else {
            subtitle = "Installed Â· " + versionName;
            action = "Settings";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    MicroGInstaller.openMicroGSettings(MicroGActivity.this);
                }
            };
        }
        if (!current && permissionOff && !"Turn on".equals(action)) {
            subtitle = subtitle + " Install permission off.";
            action = "Open settings";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    permissionAttempted = true;
                    MicroGInstaller.openInstallPermissionSettings(MicroGActivity.this);
                }
            };
        }

        addRow("microG", subtitle, current ? "READY" : "REQUIRED",
                current ? GREEN : RED, action, current ? GREEN : CYAN, actionRun);
    }

    private void addNotificationRow() {
        boolean granted = notificationsGranted();
        boolean asked = SetupPrefs.getBoolean(this, SetupPrefs.KEY_NOTIF_ASKED, false);
        String subtitle;
        String action = null;
        Runnable actionRun = null;
        if (Build.VERSION.SDK_INT < 33) {
            subtitle = "On by default on this Android version.";
        } else if (granted) {
            subtitle = "On.";
        } else if (!asked) {
            subtitle = "Download finished and playback alerts.";
            action = "Turn on";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    askNotifications();
                }
            };
        } else {
            subtitle = "Off. Tap to open settings.";
            action = "Open settings";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    openNotificationSettings();
                }
            };
        }
        addRow("Notifications", subtitle, "RECOMMENDED", DIM, action, CYAN, actionRun);
    }

    private void addBatteryRow() {
        boolean installed = MicroGInstaller.isInstalled(this);
        boolean exempt = installed
                && MicroGInstaller.isIgnoringBatteryOptimizations(this);
        String subtitle;
        String action = null;
        Runnable actionRun = null;
        if (!installed) {
            subtitle = "Available after microG is installed.";
        } else if (exempt) {
            subtitle = "Unrestricted.";
        } else {
            subtitle = "Keeps microG awake in the background.";
            action = "Allow";
            actionRun = new Runnable() {
                @Override
                public void run() {
                    MicroGInstaller.requestBatteryExemption(MicroGActivity.this);
                }
            };
        }
        addRow("Battery", subtitle, "RECOMMENDED", DIM, action, CYAN, actionRun);
    }

    private void continueFromChecklist() {
        if (!MicroGInstaller.isReady(this)) {
            return;
        }
        if (Build.VERSION.SDK_INT >= 33 && !notificationsGranted()) {
            boolean asked = SetupPrefs.getBoolean(this, SetupPrefs.KEY_NOTIF_ASKED, false);
            if (!asked) {
                pendingContinue = true;
                askNotifications();
                return;
            }
        }
        showSuccess();
    }

    private void showDifferentBuildDialog() {
        new AlertDialog.Builder(this)
                .setTitle("Using a different microG build.")
                .setMessage("This microG is newer than the bundled one. "
                        + "T YouTube will keep using it.")
                .setPositiveButton("OK", null)
                .show();
    }

    // ----------------------------------------------------------- permission

    private void beginInstallFlow() {
        cancelled = false;
        if (!MicroGInstaller.canRequestPackageInstalls(this)) {
            awaitingPermission = true;
            SetupPrefs.putBoolean(this, SetupPrefs.KEY_PENDING_INSTALL, true);
            showPermission();
            return;
        }
        startPreparing();
    }

    private void showPermission() {
        screen = SCREEN_PERMISSION;
        prepareContent();
        addTopBar("", new Runnable() {
            @Override
            public void run() {
                awaitPermissionLater();
            }
        });

        TextView title = label("Allow installs", 24, TEXT, Typeface.BOLD);
        content.addView(title, matchLp(8));

        TextView body = label(
                "Android needs your OK before T YouTube can install microG. "
                        + "You'll only do this once.",
                15, MUTED, Typeface.NORMAL);
        body.setLineSpacing(dp(4), 1f);
        content.addView(body, matchLp(16));

        TextView note = label(
                "On most phones this is called \"Install unknown apps\".",
                13, DIM, Typeface.NORMAL);
        content.addView(note, matchLp(12));

        if (permissionAttempted && !MicroGInstaller.canRequestPackageInstalls(this)) {
            TextView warning = label(
                    "Still off. Turn on \"Allow from this source\", then come back.",
                    13, AMBER, Typeface.BOLD);
            warning.setLineSpacing(dp(3), 1f);
            content.addView(warning, matchLp(16));
        }

        TextView open = primaryButton("Open settings", true);
        open.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                permissionAttempted = true;
                MicroGInstaller.openInstallPermissionSettings(MicroGActivity.this);
            }
        });
        content.addView(open, matchHeightLp(52, 24));

        TextView notNow = textButton("Not now", CYAN);
        notNow.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                awaitPermissionLater();
            }
        });
        content.addView(notNow, matchHeightLp(48, 4));
    }

    private void awaitPermissionLater() {
        awaitingPermission = false;
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_PENDING_INSTALL, false);
        showChecklist();
    }

    // ------------------------------------------------------------- preparing

    private void startPreparing() {
        if (MicroGInstaller.pickAsset() == null) {
            showUnsupported();
            return;
        }
        cancelled = false;
        installRunning = true;
        preparingPercent = 0;
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_PENDING_INSTALL, true);
        MicroGInstaller.abandonStaleSession(this);
        showPreparing();

        MicroGInstaller.startInstall(this, new MicroGInstaller.InstallCallback() {
            @Override
            public void onProgress(int percent) {
                if (isFinishing() || screen != SCREEN_PREPARING) {
                    return;
                }
                preparingPercent = percent;
                updatePreparing();
            }

            @Override
            public void onWaitingForUser() {
                if (isFinishing()) {
                    return;
                }
                preparingPercent = 100;
                updatePreparing();
                awaitingSystemInstaller = true;
            }

            @Override
            public void onFailure(String title, String message, boolean signatureMismatch) {
                if (isFinishing()) {
                    return;
                }
                installRunning = false;
                SetupPrefs.putBoolean(MicroGActivity.this, SetupPrefs.KEY_PENDING_INSTALL, false);
                showInstallError(title, message, signatureMismatch);
            }
        });
    }

    private void showPreparing() {
        screen = SCREEN_PREPARING;
        prepareContent();
        addTopBar("", new Runnable() {
            @Override
            public void run() {
                confirmCancel();
            }
        });

        TextView headline = label("Getting microG ready.", 24, TEXT, Typeface.BOLD);
        content.addView(headline, matchLp(8));

        TextView body = label(
                "This takes a few seconds. Keep the screen open.",
                14, MUTED, Typeface.NORMAL);
        content.addView(body, matchLp(6));

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setIndeterminate(true);
        progressBar.setIndeterminateTintList(
                android.content.res.ColorStateList.valueOf(CYAN));
        content.addView(progressBar, matchHeightLp(24, 24));

        stepViews = new TextView[3];
        stepViews[0] = addStep("Preparing the file");
        stepViews[1] = addStep("Checking the file");
        stepViews[2] = addStep("Opening Android installer");

        TextView hint = label(
                "Android will show one confirmation. Tap Install. "
                        + "microG's permissions are normal - it stands in for Google Play Services.",
                13, MUTED, Typeface.NORMAL);
        hint.setLineSpacing(dp(3), 1f);
        hint.setBackground(rounded(SURFACE, 12, 0));
        hint.setPadding(dp(14), dp(12), dp(14), dp(12));
        content.addView(hint, matchLp(24));

        final TextView slow = label(
                "Still working... large files take a little longer on some phones.",
                12, DIM, Typeface.NORMAL);
        slow.setVisibility(View.GONE);
        content.addView(slow, matchLp(12));
        content.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (!isFinishing()) {
                    slow.setVisibility(View.VISIBLE);
                }
            }
        }, 8000L);

        TextView cancel = textButton("Cancel", MUTED);
        cancel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                confirmCancel();
            }
        });
        content.addView(cancel, matchHeightLp(48, 20));

        updatePreparing();
    }

    private TextView addStep(String text) {
        TextView view = label("â—‹  " + text, 14, DIM, Typeface.NORMAL);
        view.setPadding(0, dp(8), 0, dp(8));
        content.addView(view, matchLp(0));
        return view;
    }

    private void updatePreparing() {
        if (stepViews == null || stepViews.length < 3) {
            return;
        }
        int done = preparingPercent >= 100 ? 3 : preparingPercent >= 60 ? 2 : 1;
        String[] labels = {
                "Preparing the file",
                "Checking the file",
                "Opening Android installer",
        };
        for (int i = 0; i < 3; i++) {
            String mark = i < done ? "âœ“" : "â—‹";
            stepViews[i].setText(mark + "  " + labels[i]);
            stepViews[i].setTextColor(i < done ? CYAN : DIM);
        }
    }

    private void confirmCancel() {
        new AlertDialog.Builder(this)
                .setTitle("Stop installing microG?")
                .setMessage("You can finish later from Settings > Setup & permissions.")
                .setPositiveButton("Keep installing", null)
                .setNegativeButton("Stop", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        MicroGInstaller.cancelInstall();
                        installRunning = false;
                        SetupPrefs.putBoolean(
                                MicroGActivity.this, SetupPrefs.KEY_PENDING_INSTALL, false);
                        SetupPrefs.putInt(
                                MicroGActivity.this, SetupPrefs.KEY_INSTALL_SESSION, -1);
                        showChecklist();
                    }
                })
                .show();
    }

    // ------------------------------------------------------- install results

    private boolean handleInstallResult(Intent intent) {
        if (intent == null || !intent.hasExtra(EXTRA_INSTALL_STATUS)) {
            return false;
        }
        int status = intent.getIntExtra(EXTRA_INSTALL_STATUS, Integer.MIN_VALUE);
        String message = intent.getStringExtra(EXTRA_INSTALL_MESSAGE);
        intent.removeExtra(EXTRA_INSTALL_STATUS);
        intent.removeExtra(EXTRA_INSTALL_MESSAGE);
        installRunning = false;
        awaitingSystemInstaller = false;
        awaitingPermission = false;
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_PENDING_INSTALL, false);

        if (status == PackageInstaller.STATUS_SUCCESS || MicroGInstaller.isReady(this)) {
            onInstallSuccess();
            return true;
        }
        if (status == PackageInstaller.STATUS_FAILURE_ABORTED) {
            SetupPrefs.putInt(this, SetupPrefs.KEY_LAST_STATUS, status);
            banner = "";
            showChecklist();
            return true;
        }
        showInstallError(mapStatusTitle(status, message), mapStatusBody(status, message),
                isSignatureError(status, message));
        return true;
    }

    private void onInstallSuccess() {
        installRunning = false;
        awaitingSystemInstaller = false;
        awaitingPermission = false;
        SetupPrefs.putInt(this, SetupPrefs.KEY_INSTALL_SESSION, -1);
        SetupPrefs.putInt(this, SetupPrefs.KEY_LAST_STATUS, PackageInstaller.STATUS_SUCCESS);
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_PENDING_INSTALL, false);
        banner = "microG installed.";
        showChecklist();
    }

    private void showInstallError(String title, String body, boolean signatureMismatch) {
        errorTitle = title;
        errorBody = body;
        errorShowUninstall = signatureMismatch;
        if (signatureMismatch) {
            errorBody = body
                    + "\n\nUninstalling microG removes its accounts and settings. "
                    + "T YouTube's data stays.";
            errorPrimary = "Uninstall microG";
            errorPrimaryAction = new Runnable() {
                @Override
                public void run() {
                    MicroGInstaller.uninstallMicroG(MicroGActivity.this);
                }
            };
            errorSecondary = "Cancel";
            errorSecondaryAction = new Runnable() {
                @Override
                public void run() {
                    showChecklist();
                }
            };
        } else {
            errorPrimary = "Try again";
            errorPrimaryAction = new Runnable() {
                @Override
                public void run() {
                    beginInstallFlow();
                }
            };
            errorSecondary = "Later";
            errorSecondaryAction = new Runnable() {
                @Override
                public void run() {
                    later();
                }
            };
        }
        showError();
    }

    private boolean isSignatureError(int status, String message) {
        if (status == PackageInstaller.STATUS_FAILURE_INCOMPATIBLE) {
            return true;
        }
        if (message == null) {
            return false;
        }
        return message.contains("UPDATE_INCOMPATIBLE")
                || message.contains("INCONSISTENT_CERTIFICATES")
                || message.contains("signatures do not match");
    }

    private String mapStatusTitle(int status, String message) {
        if (isSignatureError(status, message)) {
            return "A different microG is installed.";
        }
        switch (status) {
            case PackageInstaller.STATUS_FAILURE_ABORTED:
                return "Install cancelled.";
            case PackageInstaller.STATUS_FAILURE_BLOCKED:
                return "Android blocked the install.";
            case PackageInstaller.STATUS_FAILURE_STORAGE:
                return "Not enough space.";
            case PackageInstaller.STATUS_FAILURE_INVALID:
                return "The microG file is damaged.";
            default:
                return "microG didn't install.";
        }
    }

    private String mapStatusBody(int status, String message) {
        if (isSignatureError(status, message)) {
            return "Android can't replace it because it's signed with a different key. "
                    + "Uninstall the old microG, then try again.";
        }
        switch (status) {
            case PackageInstaller.STATUS_FAILURE_ABORTED:
                return "microG isn't installed yet. You can try again now or finish later in Settings.";
            case PackageInstaller.STATUS_FAILURE_BLOCKED:
                return "Play Protect or your phone's security settings stopped it. "
                        + "Check the installer details, then try again.";
            case PackageInstaller.STATUS_FAILURE_STORAGE:
                return "microG needs about 250 MB free. Free up some space, then try again.";
            case PackageInstaller.STATUS_FAILURE_INVALID:
                return "Reinstall T YouTube to replace it. Your app data stays.";
            default:
                String detail = message == null || message.length() == 0
                        ? ""
                        : "\n\n" + message;
                return "Something stopped the installer. Try again - if it keeps happening, "
                        + "send us the details." + detail;
        }
    }

    // ------------------------------------------------------------ error/success

    private void showError() {
        screen = SCREEN_ERROR;
        prepareContent();
        addTopBar("Later", new Runnable() {
            @Override
            public void run() {
                later();
            }
        });

        TextView title = label(errorTitle, 24, TEXT, Typeface.BOLD);
        content.addView(title, matchLp(8));

        TextView body = label(errorBody, 14, MUTED, Typeface.NORMAL);
        body.setLineSpacing(dp(4), 1f);
        content.addView(body, matchLp(16));

        if (errorShowUninstall) {
            TextView warn = label(
                    "Uninstalling microG removes its accounts and settings. "
                            + "T YouTube's data stays.",
                    12, AMBER, Typeface.NORMAL);
            warn.setLineSpacing(dp(3), 1f);
            content.addView(warn, matchLp(12));
        }

        if (errorPrimaryAction != null) {
            TextView primary = primaryButton(errorPrimary, true);
            primary.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    errorPrimaryAction.run();
                }
            });
            content.addView(primary, matchHeightLp(52, 24));
        }
        if (errorSecondaryAction != null) {
            TextView secondary = textButton(errorSecondary, CYAN);
            secondary.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    errorSecondaryAction.run();
                }
            });
            content.addView(secondary, matchHeightLp(48, 4));
        }
    }

    private void showUnsupported() {
        screen = SCREEN_UNSUPPORTED;
        prepareContent();
        addTopBar("Later", new Runnable() {
            @Override
            public void run() {
                later();
            }
        });

        TextView title = label("This phone isn't supported.", 24, TEXT, Typeface.BOLD);
        content.addView(title, matchLp(8));

        TextView body = label(
                "The microG inside this build doesn't match your phone's processor. "
                        + "Install the universal T YouTube build from the release page.",
                14, MUTED, Typeface.NORMAL);
        body.setLineSpacing(dp(4), 1f);
        content.addView(body, matchLp(16));

        TextView open = primaryButton("Open release page", true);
        open.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(RELEASE_PAGE)));
                } catch (Exception ignored) {
                }
            }
        });
        content.addView(open, matchHeightLp(52, 24));

        TextView later = textButton("Later", CYAN);
        later.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                later();
            }
        });
        content.addView(later, matchHeightLp(48, 4));
    }

    private void showSuccess() {
        screen = SCREEN_SUCCESS;
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_SETUP_COMPLETE, true);
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_WELCOME_SEEN, true);
        prepareContent();

        TextView ring = label("âœ“", 34, BG, Typeface.BOLD);
        ring.setGravity(Gravity.CENTER);
        ring.setBackground(rounded(CYAN, 32, 0));
        LinearLayout.LayoutParams ringLp = new LinearLayout.LayoutParams(dp(64), dp(64));
        ringLp.gravity = Gravity.CENTER_HORIZONTAL;
        ringLp.topMargin = dp(24);
        content.addView(ring, ringLp);

        boolean notifOff = Build.VERSION.SDK_INT >= 33 && !notificationsGranted();
        boolean batteryOff = !MicroGInstaller.isIgnoringBatteryOptimizations(this);
        String headlineText = "You're all set.";
        String bodyText;
        if (notifOff || batteryOff) {
            bodyText = "microG is installed. You can turn on notifications and battery later in Settings.";
        } else {
            bodyText = "microG is installed. T YouTube is ready.";
        }

        TextView headline = label(headlineText, 24, TEXT, Typeface.BOLD);
        headline.setGravity(Gravity.CENTER);
        content.addView(headline, matchLp(20));

        TextView body = label(bodyText, 14, MUTED, Typeface.NORMAL);
        body.setGravity(Gravity.CENTER);
        body.setLineSpacing(dp(3), 1f);
        content.addView(body, matchLp(8));

        TextView open = primaryButton("Open T YouTube", true);
        open.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openApp();
            }
        });
        content.addView(open, matchHeightLp(52, 28));

        TextView review = textButton("Review setup", CYAN);
        review.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                manageMode = true;
                showChecklist();
            }
        });
        content.addView(review, matchHeightLp(48, 4));
    }

    // --------------------------------------------------------------- helpers

    private void prepareContent() {
        root.removeAllViews();
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(24), dp(20), dp(24), dp(32));
        scroll.addView(content, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(scroll, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
    }

    private void addTopBar(String rightLabel, final Runnable rightAction) {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);

        TextView back = label("â€¹", 30, TEXT, Typeface.NORMAL);
        back.setGravity(Gravity.CENTER);
        back.setContentDescription("Back");
        back.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                onBackPressed();
            }
        });
        bar.addView(back, new LinearLayout.LayoutParams(dp(48), dp(48)));

        TextView title = label("Setup", 20, TEXT, Typeface.BOLD);
        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        bar.addView(title, titleLp);

        if (!TextUtils.isEmpty(rightLabel)) {
            TextView right = label(rightLabel, 14, CYAN, Typeface.BOLD);
            right.setGravity(Gravity.CENTER);
            right.setPadding(dp(12), 0, dp(4), 0);
            right.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    rightAction.run();
                }
            });
            bar.addView(right, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, dp(48)));
        }

        content.addView(bar, matchLp(8));
    }

    private void addRow(
            String title, String subtitle, String chip, int chipColor,
            String action, int actionColor, final Runnable actionRun) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setBackground(rounded(SURFACE, 14, 0));
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setFocusable(true);
        card.setClickable(actionRun != null);
        if (actionRun != null) {
            card.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    actionRun.run();
                }
            });
        }

        LinearLayout left = new LinearLayout(this);
        left.setOrientation(LinearLayout.VERTICAL);

        LinearLayout titleLine = new LinearLayout(this);
        titleLine.setOrientation(LinearLayout.HORIZONTAL);
        titleLine.setGravity(Gravity.CENTER_VERTICAL);

        TextView titleView = label(title, 16, TEXT, Typeface.BOLD);
        titleLine.addView(titleView);

        TextView chipView = label(chip, 10, chipColor, Typeface.BOLD);
        chipView.setPadding(dp(7), dp(2), dp(7), dp(2));
        chipView.setBackground(rounded((chipColor & 0x00FFFFFF) | 0x22000000, 8, 0));
        LinearLayout.LayoutParams chipLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        chipLp.leftMargin = dp(8);
        titleLine.addView(chipView, chipLp);

        left.addView(titleLine);

        TextView subtitleView = label(subtitle, 12, MUTED, Typeface.NORMAL);
        subtitleView.setLineSpacing(dp(2), 1f);
        LinearLayout.LayoutParams subLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        subLp.topMargin = dp(3);
        left.addView(subtitleView, subLp);

        card.addView(left, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        if (action != null) {
            TextView actionView = label(action, 12, actionColor, Typeface.BOLD);
            actionView.setGravity(Gravity.CENTER);
            actionView.setPadding(dp(12), dp(7), dp(12), dp(7));
            actionView.setBackground(rounded(0x00000000, 20, actionColor));
            LinearLayout.LayoutParams actionLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            actionLp.leftMargin = dp(10);
            card.addView(actionView, actionLp);
        } else {
            TextView check = label("âœ“", 16, CYAN, Typeface.BOLD);
            check.setGravity(Gravity.CENTER);
            LinearLayout.LayoutParams checkLp = new LinearLayout.LayoutParams(dp(32), dp(32));
            checkLp.leftMargin = dp(8);
            card.addView(check, checkLp);
        }

        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardLp.bottomMargin = dp(10);
        content.addView(card, cardLp);
    }

    private TextView label(String text, float sizeSp, int color, int style) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(sizeSp);
        view.setTextColor(color);
        view.setTypeface(Typeface.create("sans-serif", style));
        view.setIncludeFontPadding(false);
        return view;
    }

    private TextView primaryButton(String text, boolean enabled) {
        TextView view = label(text, 16, Color.WHITE, Typeface.BOLD);
        view.setGravity(Gravity.CENTER);
        view.setBackground(rounded(RED, 16, 0));
        view.setAlpha(enabled ? 1f : 0.4f);
        view.setEnabled(enabled);
        view.setClickable(enabled);
        return view;
    }

    private TextView textButton(String text, int color) {
        TextView view = label(text, 15, color, Typeface.BOLD);
        view.setGravity(Gravity.CENTER);
        return view;
    }

    private GradientDrawable rounded(int fill, float radiusDp, int strokeColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setShape(GradientDrawable.RECTANGLE);
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(radiusDp));
        if (strokeColor != 0) {
            drawable.setStroke(dp(1), strokeColor);
        }
        return drawable;
    }

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private LinearLayout.LayoutParams matchLp(int topMarginDp) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(topMarginDp);
        return params;
    }

    private LinearLayout.LayoutParams matchHeightLp(int heightDp, int topMarginDp) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(heightDp));
        params.topMargin = dp(topMarginDp);
        return params;
    }

    private LinearLayout.LayoutParams centerLp(int sizeDp, int topMarginDp) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                sizeDp == ViewGroup.LayoutParams.WRAP_CONTENT ? sizeDp : dp(sizeDp),
                sizeDp == ViewGroup.LayoutParams.WRAP_CONTENT ? sizeDp : dp(sizeDp));
        params.gravity = Gravity.CENTER_HORIZONTAL;
        params.topMargin = dp(topMarginDp);
        return params;
    }

    private void applyWindow() {
        Window window = getWindow();
        window.setStatusBarColor(BG);
        window.setNavigationBarColor(BG);
        if (Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController controller = window.getInsetsController();
            if (controller != null) {
                controller.setSystemBarsAppearance(
                        0,
                        WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                                | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS);
            }
        } else {
            window.getDecorView().setSystemUiVisibility(0);
        }
    }

    private void applyInsets() {
        root.setOnApplyWindowInsetsListener(new View.OnApplyWindowInsetsListener() {
            @Override
            public WindowInsets onApplyWindowInsets(View view, WindowInsets insets) {
                int top;
                int bottom;
                if (Build.VERSION.SDK_INT >= 30) {
                    Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                    top = bars.top;
                    bottom = bars.bottom;
                } else {
                    top = insets.getSystemWindowInsetTop();
                    bottom = insets.getSystemWindowInsetBottom();
                }
                view.setPadding(0, top, 0, bottom);
                return insets;
            }
        });
    }

    // ------------------------------------------------------- small utilities

    private boolean notificationsGranted() {
        if (Build.VERSION.SDK_INT < 33) {
            return true;
        }
        return checkSelfPermission("android.permission.POST_NOTIFICATIONS")
                == PackageManager.PERMISSION_GRANTED;
    }

    private void askNotifications() {
        if (Build.VERSION.SDK_INT < 33) {
            return;
        }
        SetupPrefs.putBoolean(this, SetupPrefs.KEY_NOTIF_ASKED, true);
        requestPermissions(
                new String[]{"android.permission.POST_NOTIFICATIONS"}, REQ_NOTIFICATIONS);
    }

    private void openNotificationSettings() {
        Intent intent = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS);
        intent.putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName());
        try {
            startActivity(intent);
        } catch (Exception ignored) {
            startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.parse("package:" + getPackageName())));
        }
    }
}
