[app]
title = Humanity AI Shield V7
package.name = humanityaishield
package.domain = org.humanity
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,md,txt,sh
source.include_patterns = package/**
source.exclude_dirs = bin,.buildozer,__pycache__,tests,documentation
version = 7.0
requirements = python3,kivy,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
