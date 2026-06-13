"""PyInstaller build script for WWII Wargame - single .exe"""
import PyInstaller.__main__
import os

def build():
    root = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(root, "main.py")
    data_dir = os.path.join(root, "data")

    exe_name = "WWII_Wargame"
    dist_dir = os.path.join(os.path.dirname(root), "dist")

    # PyInstaller uses : as source:dest separator on all platforms
    args = [
        main_py,
        "--onefile",
        f"--name={exe_name}",
        f"--distpath={dist_dir}",
        "--noconsole",
        "--clean",
        f"--add-data={data_dir}:ww2/data",
    ]

    print("Building single-file exe...")
    print(f"Data: {data_dir} -> ww2/data")
    PyInstaller.__main__.run(args)
    size_mb = os.path.getsize(os.path.join(dist_dir, exe_name + ".exe")) / (1024 * 1024)
    print(f"Done: {dist_dir}\\{exe_name}.exe ({size_mb:.1f} MB)")

if __name__ == "__main__":
    build()
