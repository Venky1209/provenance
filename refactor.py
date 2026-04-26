import os
import shutil
import glob
import re

# Move directories and files
if os.path.exists("scrapers"):
    os.rename("scrapers", "scraper")

if not os.path.exists("scoring"):
    os.makedirs("scoring", exist_ok=True)

if os.path.exists("scoring/trust_score.py"):
    shutil.move("scoring/trust_score.py", "scoring/trust_score.py")

if os.path.exists("utils/tagging.py"):
    shutil.move("utils/tagging.py", "utils/tagging.py")

if os.path.exists("utils/chunking.py"):
    shutil.move("utils/chunking.py", "utils/chunking.py")

# Create __init__.py in scoring
with open("scoring/__init__.py", "w") as f:
    f.write("")

# Find all python and markdown files
files = glob.glob("**/*.py", recursive=True) + glob.glob("**/*.md", recursive=True)

for file in files:
    if "venv" in file or ".git" in file: continue
    try:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        
        orig_content = content
        
        # Replace imports
        content = content.replace("from scraper.", "from scraper.")
        content = content.replace("import scraper.", "import scraper.")
        content = content.replace("from scoring.trust_score", "from scoring.trust_score")
        content = content.replace("from utils.tagging", "from utils.tagging")
        content = content.replace("from utils.chunking", "from utils.chunking")
        
        # Markdown mentions
        content = content.replace("scraper/", "scraper/")
        content = content.replace("scoring/trust_score.py", "scoring/trust_score.py")
        content = content.replace("utils/tagging.py", "utils/tagging.py")
        content = content.replace("utils/chunking.py", "utils/chunking.py")
        
        if content != orig_content:
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {file}")
            
    except Exception as e:
        print(f"Failed {file}: {e}")
