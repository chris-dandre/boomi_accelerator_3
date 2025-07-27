import os

def print_directory_structure(startpath, exclude_dirs=['__pycache__', 'venv']):
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f'{indent}{os.path.basename(root)}/')
        for f in files:
            if not f.endswith('.pyc'):
                print(f'{indent}    {f}')
print_directory_structure('.')