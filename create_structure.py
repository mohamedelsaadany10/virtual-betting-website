import os

def create_directory_structure():
    """
    Creates the complete folder structure for the virtual betting Django project
    """
    
    # Base project directory
    base_dir = "virtual-betting"
    
    # Define the complete structure
    structure = {
        base_dir: {
            "config": [
                "__init__.py",
                "settings.py",
                "urls.py",
                "asgi.py",
                "wsgi.py"
            ],
            "apps": {
                "accounts": {
                    "migrations": ["__init__.py"],
                    "__init__.py": None,
                    "admin.py": None,
                    "apps.py": None,
                    "forms.py": None,
                    "models.py": None,
                    "urls.py": None,
                    "views.py": None
                },
                "wallet": {
                    "migrations": ["__init__.py"],
                    "__init__.py": None,
                    "admin.py": None,
                    "models.py": None,
                    "urls.py": None,
                    "views.py": None
                },
                "events": {
                    "migrations": ["__init__.py"],
                    "__init__.py": None,
                    "admin.py": None,
                    "models.py": None,
                    "urls.py": None,
                    "views.py": None
                },
                "bets": {
                    "migrations": ["__init__.py"],
                    "__init__.py": None,
                    "admin.py": None,
                    "forms.py": None,
                    "models.py": None,
                    "urls.py": None,
                    "views.py": None
                },
                "results": {
                    "migrations": ["__init__.py"],
                    "__init__.py": None,
                    "admin.py": None,
                    "models.py": None,
                    "views.py": None
                }
            },
            "templates": {
                "base.html": None,
                "accounts": {},
                "wallet": {},
                "events": {},
                "bets": {},
                "results": {}
            },
            "static": {
                "css": ["style.css"],
                "js": {},
                "images": {}
            },
            "docs": [
                "api.md",
                "database.md",
                "betting_rules.md"
            ],
            "manage.py": None,
            "README.md": None,
            "requirements.txt": None,
            ".gitignore": None
        }
    }
    
    def create_structure(base_path, structure):
        """Recursively creates directories and files"""
        for name, content in structure.items():
            path = os.path.join(base_path, name)
            
            if isinstance(content, dict):
                # It's a directory with subdirectories/files
                os.makedirs(path, exist_ok=True)
                print(f"Created directory: {path}")
                create_structure(path, content)
            elif isinstance(content, list):
                # It's a directory with files
                os.makedirs(path, exist_ok=True)
                print(f"Created directory: {path}")
                for file in content:
                    file_path = os.path.join(path, file)
                    open(file_path, 'a').close()
                    print(f"Created file: {file_path}")
            elif content is None:
                # It's a file
                open(path, 'a').close()
                print(f"Created file: {path}")
    
    # Create the structure
    print("Creating Django project structure...")
    print("=" * 50)
    create_structure(".", structure)
    print("=" * 50)
    print(f"\n✓ Project structure created successfully!")
    print(f"\nTo start working:")
    print(f"1. cd {base_dir}")
    print(f"2. python -m venv venv")
    print(f"3. source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print(f"4. pip install django")
    print(f"5. Open the folder in VS Code")

if __name__ == "__main__":
    create_directory_structure()
