"""PyInstaller 打包脚本"""

import os, sys

def build():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]

    add_data = []
    for f in json_files:
        src = os.path.join(data_dir, f)
        add_data.append(f"--add-data={src}{os.pathsep}data")

    cmd = (f"pyinstaller --onefile --windowed "
           f"--name=WorldCup2026 "
           f"{' '.join(add_data)} "
           f"main.py")
    print(f"执行: {cmd}")
    os.system(cmd)
    print(f"\n打包完成! 输出: {os.path.abspath('dist/WorldCup2026.exe')}")


if __name__ == "__main__":
    build()
