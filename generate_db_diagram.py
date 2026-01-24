#!/usr/bin/env python
"""
Generate database diagram from Django models.

Usage:
    python generate_db_diagram.py

Requirements:
    pip install django-extensions pydot

For graphviz (required for PNG output):
    Windows: choco install graphviz OR download from https://graphviz.org/download/
    macOS: brew install graphviz
    Linux: sudo apt-get install graphviz

Output:
    database_diagram.png - Visual diagram of all database models
"""

import os
import sys
import subprocess
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')

import django
django.setup()

from django.apps import apps
from django.db import models


def check_dependencies():
    """Check if required packages are installed."""
    missing = []

    try:
        import django_extensions
    except ImportError:
        missing.append('django-extensions')

    try:
        import pydot
    except ImportError:
        missing.append('pydot')

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False

    # Check graphviz
    try:
        result = subprocess.run(['dot', '-V'], capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print("Graphviz not found!")
        print("Install graphviz:")
        print("  Windows: choco install graphviz OR download from https://graphviz.org/download/")
        print("  macOS: brew install graphviz")
        print("  Linux: sudo apt-get install graphviz")
        return False

    return True


def ensure_django_extensions_installed():
    """Ensure django-extensions is in INSTALLED_APPS."""
    from django.conf import settings

    if 'django_extensions' not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['django_extensions']
        print("Note: Added django_extensions to INSTALLED_APPS temporarily")


def generate_diagram_with_management_command():
    """Generate diagram using Django management command."""
    from django.core.management import call_command
    from io import StringIO

    output_file = BASE_DIR / 'database_diagram.png'
    dot_file = BASE_DIR / 'database_diagram.dot'

    try:
        # Generate DOT file first
        with open(dot_file, 'w') as f:
            call_command(
                'graph_models',
                'tasks_api',
                '--arrow-shape', 'normal',
                '--output', str(dot_file),
                stdout=f
            )

        # Convert DOT to PNG using graphviz
        subprocess.run([
            'dot', '-Tpng', str(dot_file), '-o', str(output_file)
        ], check=True)

        print(f"Database diagram generated: {output_file}")

        # Cleanup DOT file
        if dot_file.exists():
            dot_file.unlink()

        return True

    except Exception as e:
        print(f"Error with management command: {e}")
        return False


def generate_diagram_manual():
    """Generate diagram manually using pydot if management command fails."""
    import pydot

    output_file = BASE_DIR / 'database_diagram.png'

    # Create graph
    graph = pydot.Dot(graph_type='digraph', rankdir='TB')
    graph.set_node_defaults(shape='record', fontsize='10')
    graph.set_edge_defaults(fontsize='8')

    # Color scheme
    colors = {
        'BaseModel': '#E8E8E8',
        'Account': '#FFE4B5',
        'Project': '#98FB98',
        'Section': '#87CEEB',
        'Task': '#FFB6C1',
        'TaskView': '#DDA0DD',
        'SectionView': '#F0E68C',
        'UserAchievement': '#FFA07A',
        'TaskCollaboration': '#B0C4DE',
        'TaskInvitation': '#D3D3D3',
        'ProjectCollaboration': '#90EE90',
        'ProjectInvitation': '#ADD8E6',
    }

    # Get all models from tasks_api
    app_models = apps.get_app_config('tasks_api').get_models()

    model_nodes = {}
    edges = []

    for model in app_models:
        model_name = model.__name__

        # Get fields
        fields = []
        for field in model._meta.get_fields():
            if hasattr(field, 'column'):
                field_type = type(field).__name__
                field_name = field.name

                # Mark primary keys and foreign keys
                if field.primary_key:
                    field_name = f"+ {field_name} (PK)"
                elif isinstance(field, models.ForeignKey):
                    field_name = f"* {field_name} (FK)"
                    # Track relationship
                    related_model = field.related_model.__name__
                    edges.append((model_name, related_model, field.name))
                elif isinstance(field, models.ManyToManyField):
                    field_name = f"~ {field_name} (M2M)"
                    related_model = field.related_model.__name__
                    edges.append((model_name, related_model, field.name))

                fields.append(f"{field_name}: {field_type}")

        # Create label for node
        fields_str = '\\l'.join(fields) + '\\l' if fields else ''
        label = f"{{{model_name}|{fields_str}}}"

        # Create node
        color = colors.get(model_name, '#FFFFFF')
        node = pydot.Node(
            model_name,
            label=label,
            fillcolor=color,
            style='filled'
        )
        graph.add_node(node)
        model_nodes[model_name] = node

    # Add edges (relationships)
    for from_model, to_model, field_name in edges:
        if from_model in model_nodes and to_model in model_nodes:
            edge = pydot.Edge(
                from_model,
                to_model,
                label=field_name,
                arrowhead='normal'
            )
            graph.add_edge(edge)

    # Save diagram
    graph.write_png(str(output_file))
    print(f"Database diagram generated: {output_file}")
    return True


def generate_diagram_simple():
    """Generate a simple text-based diagram if graphviz fails."""
    from django.apps import apps

    output_file = BASE_DIR / 'database_diagram.txt'

    lines = []
    lines.append("=" * 60)
    lines.append("DATABASE SCHEMA DIAGRAM")
    lines.append("=" * 60)
    lines.append("")

    app_models = apps.get_app_config('tasks_api').get_models()

    relationships = []

    for model in app_models:
        model_name = model.__name__
        lines.append(f"{'=' * 40}")
        lines.append(f"  {model_name}")
        lines.append(f"{'=' * 40}")

        for field in model._meta.get_fields():
            if hasattr(field, 'column'):
                field_type = type(field).__name__
                field_name = field.name

                prefix = "  "
                suffix = ""

                if field.primary_key:
                    prefix = "* "
                    suffix = " [PK]"
                elif isinstance(field, models.ForeignKey):
                    prefix = "-> "
                    suffix = f" [FK -> {field.related_model.__name__}]"
                    relationships.append(f"{model_name}.{field_name} -> {field.related_model.__name__}")
                elif isinstance(field, models.ManyToManyField):
                    prefix = "<> "
                    suffix = f" [M2M -> {field.related_model.__name__}]"
                    relationships.append(f"{model_name}.{field_name} <-> {field.related_model.__name__}")

                lines.append(f"  {prefix}{field_name}: {field_type}{suffix}")

        lines.append("")

    lines.append("=" * 60)
    lines.append("RELATIONSHIPS")
    lines.append("=" * 60)
    for rel in relationships:
        lines.append(f"  {rel}")

    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Text diagram generated: {output_file}")
    return True


def main():
    """Main function to generate database diagram."""
    print("Generating database diagram...")
    print("-" * 40)

    # Check dependencies
    has_deps = check_dependencies()

    if has_deps:
        # Try django-extensions management command first
        ensure_django_extensions_installed()

        try:
            if generate_diagram_with_management_command():
                return
        except Exception as e:
            print(f"Management command failed: {e}")

        # Fall back to manual pydot method
        try:
            if generate_diagram_manual():
                return
        except Exception as e:
            print(f"Manual pydot method failed: {e}")

    # Fall back to simple text diagram
    print("Falling back to text-based diagram...")
    generate_diagram_simple()


if __name__ == '__main__':
    main()
