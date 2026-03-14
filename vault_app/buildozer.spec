[app]

# (str) Title of your application
title = Black Box Vault

# (str) Package name
package.name = blackboxvault

# (str) Package domain (needed for android/ios packaging)
package.domain = org.blackboxvault

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (leave empty to include all the files)
source.include_exts = py,png,jpg,kv

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# FIX 1: Removed 'pillow' and 'qrcode[pil]'. Pure python qrcode only.
requirements = python3,kivy,qrcode,openssl

# (str) Icon of the application
#icon.filename = %(source.dir)s/icon.png

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = android.permission.CAMERA

# (int) Target Android API, should be as high as possible (Android 13)
android.api = 33

# (int) Minimum API your APK will support (Android 5.0).
# FIX 2: Lowered from 24 to 21 to match the NDK API level below.
android.minapi = 21

# (int) Android NDK version to use.
# FIX 3: Explicitly set to 25b to prevent auto-detection errors.
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support.
# FIX 4: Matches minapi above. 21 is the standard "safe" baseline.
android.ndk_api = 21

# (list) The Android archs to build for.
android.archs = arm64-v8a, armeabi-v7a

# (bool) Copy library instead of making a libpymodules.so
# This can sometimes help with finding libraries on certain phones.
# android.copy_libs = 1

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (str) Android app theme, default is ok for Kivy-based app
# android.apptheme = "@android:style/Theme.NoTitleBar"

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
