# diagnostic.py
from pathlib import Path

def check_paths():
    current_dir = Path(__file__).parent
    base_path = current_dir.parent.parent / 'dataset'
    
    print("=== PATH DIAGNOSTIC ===")
    print(f"Current directory: {current_dir}")
    print(f"Base path: {base_path}")
    print(f"Base path exists: {base_path.exists()}")
    
    if base_path.exists():
        print(f"\n=== DATASET STRUCTURE ===")
        for item in base_path.iterdir():
            if item.is_dir():
                print(f"📁 {item.name}/")
                for subitem in item.iterdir():
                    if subitem.is_dir():
                        print(f"  📁 {subitem.name}/")
                        for file in subitem.iterdir():
                            print(f"    📄 {file.name}")
                    else:
                        print(f"  📄 {subitem.name}")
            else:
                print(f"📄 {item.name}")

if __name__ == "__main__":
    check_paths()