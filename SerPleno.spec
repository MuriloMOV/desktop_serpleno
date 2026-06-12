from PyInstaller.utils.hooks import collect_data_files


datas = collect_data_files("customtkinter")
datas += [
    ("ser_pleno/assets", "assets"),
    ("ser_pleno/sql", "sql"),
    ("ser_pleno/operation_config.json", "."),
    ("ser_pleno/user_profile.json", "."),
]

a = Analysis(
    ["ser_pleno/app.py"],
    pathex=["ser_pleno"],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "mysql.connector",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SerPleno",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
