import os
from datetime import datetime

def analyze_directory(path='.'):
    print(f"\nAnalyzing directory: {os.path.abspath(path)}")
    print("\nFile Name".ljust(40), "Size (bytes)".ljust(15), "Last Modified")
    print("-" * 70)
    
    for item in os.listdir(path):
        if os.path.isfile(item):
            stats = os.stat(item)
            size = stats.st_size
            modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{item[:37] + '...' if len(item) > 37 else item.ljust(40)}"
                  f"{str(size).ljust(15)}{modified}")

if __name__ == "__main__":
    analyze_directory() 