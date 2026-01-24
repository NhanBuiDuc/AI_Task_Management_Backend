#!/usr/bin/env python
"""
Generate API Blueprint documentation from Django REST Framework.

Usage:
    python generate_api_blueprint.py

Output:
    api_blueprint.md  - Markdown documentation of all API endpoints
    api_quick_reference.md - Quick reference table
"""

import os
import sys
import json
import inspect
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')

import django
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.views import APIView
from rest_framework.serializers import Serializer


def get_serializer_fields(serializer_class):
    """Extract fields from a serializer class."""
    if not serializer_class:
        return {}

    try:
        # Try to instantiate the serializer to get field info
        serializer = serializer_class()
        fields = {}

        for name, field in serializer.fields.items():
            field_info = {
                'type': type(field).__name__,
                'required': field.required,
                'read_only': field.read_only,
                'write_only': getattr(field, 'write_only', False),
                'help_text': str(field.help_text) if field.help_text else '',
                'default': str(field.default) if field.default is not None and field.default != '' else None
            }

            # Get choices if available
            if hasattr(field, 'choices') and field.choices:
                field_info['choices'] = list(dict(field.choices).keys())

            fields[name] = field_info

        return fields
    except Exception as e:
        return {'_error': str(e)}


def get_view_info(view_class, method=None):
    """Extract information from a view class."""
    info = {
        'class_name': view_class.__name__,
        'module': view_class.__module__,
        'docstring': inspect.getdoc(view_class) or '',
        'methods': [],
        'serializer_class': None,
        'serializer_fields': {},
        'actions': {}
    }

    # Get allowed methods
    if hasattr(view_class, 'http_method_names'):
        info['methods'] = [m.upper() for m in view_class.http_method_names if m != 'options']

    # Get serializer info
    if hasattr(view_class, 'serializer_class') and view_class.serializer_class:
        info['serializer_class'] = view_class.serializer_class.__name__
        info['serializer_fields'] = get_serializer_fields(view_class.serializer_class)

    # For ViewSets, get actions
    if issubclass(view_class, ViewSet):
        for attr_name in dir(view_class):
            attr = getattr(view_class, attr_name, None)
            if callable(attr) and hasattr(attr, 'kwargs'):
                # This is likely a @action decorated method
                action_kwargs = getattr(attr, 'kwargs', {})
                if action_kwargs:
                    info['actions'][attr_name] = {
                        'methods': action_kwargs.get('methods', ['get']),
                        'detail': action_kwargs.get('detail', False),
                        'url_path': action_kwargs.get('url_path', attr_name),
                        'docstring': inspect.getdoc(attr) or ''
                    }

    return info


def extract_urls(urlpatterns, prefix='', namespace=''):
    """Recursively extract all URL patterns."""
    endpoints = []

    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            # Nested URL configuration
            nested_prefix = prefix + str(pattern.pattern)
            nested_namespace = pattern.namespace or namespace

            if hasattr(pattern, 'url_patterns'):
                endpoints.extend(extract_urls(pattern.url_patterns, nested_prefix, nested_namespace))

        elif isinstance(pattern, URLPattern):
            # Single URL pattern
            path = prefix + str(pattern.pattern)
            path = '/' + path.lstrip('/').rstrip('$')

            callback = pattern.callback

            # Extract view class
            view_class = None
            methods = ['GET']
            actions = {}

            if hasattr(callback, 'cls'):
                view_class = callback.cls
            elif hasattr(callback, 'view_class'):
                view_class = callback.view_class

            if hasattr(callback, 'actions'):
                actions = callback.actions or {}
                methods = [m.upper() for m in actions.keys()]
            elif hasattr(callback, 'initkwargs'):
                # APIView-based
                methods = []
                for method in ['get', 'post', 'put', 'patch', 'delete']:
                    if hasattr(view_class, method):
                        methods.append(method.upper())

            endpoint = {
                'path': path,
                'name': pattern.name or '',
                'namespace': namespace,
                'view_class': view_class,
                'methods': methods,
                'actions': actions,
                'callback': callback
            }

            endpoints.append(endpoint)

    return endpoints


def categorize_endpoint(path, name):
    """Categorize endpoint based on path and name."""
    path_lower = path.lower()
    name_lower = (name or '').lower()

    categories = {
        'Account': ['account', 'login', 'register', 'profile', 'password'],
        'Tasks': ['task', 'task-'],
        'Projects': ['project'],
        'Sections': ['section'],
        'AI & Chat': ['ai/', 'intent', 'chat', 'extract', 'quick-task'],
        'Analytics': ['analytics', 'productivity', 'patterns', 'dashboard'],
        'Collaboration': ['collaboration', 'collab', 'invite', 'shared'],
        'Notifications': ['notification', 'notif'],
        'Scheduler': ['scheduler', 'schedule', 'workload'],
        'Import/Export': ['import', 'export', 'csv', 'json', 'pdf'],
        'Bulk Operations': ['bulk'],
        'Search': ['search'],
        'Templates': ['template'],
        'Time Tracking': ['time/', 'timer'],
        'Webhooks': ['webhook'],
        'Recurring': ['recurring'],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in path_lower or keyword in name_lower:
                return category

    return 'General'


def get_request_body_info(view_class, method, action_name=None):
    """Get request body information for an endpoint."""
    if method not in ['POST', 'PUT', 'PATCH']:
        return None

    # Check for action-specific serializer
    if action_name and hasattr(view_class, f'get_{action_name}_serializer_class'):
        try:
            serializer_class = getattr(view_class, f'get_{action_name}_serializer_class')()
            return {
                'serializer': serializer_class.__name__,
                'fields': get_serializer_fields(serializer_class)
            }
        except:
            pass

    # Check for general serializer
    serializer_class = getattr(view_class, 'serializer_class', None)
    if serializer_class:
        return {
            'serializer': serializer_class.__name__,
            'fields': get_serializer_fields(serializer_class)
        }

    return None


def get_response_info(view_class, method, action_name=None):
    """Get response information for an endpoint."""
    serializer_class = getattr(view_class, 'serializer_class', None)

    if serializer_class:
        return {
            'serializer': serializer_class.__name__,
            'fields': get_serializer_fields(serializer_class)
        }

    return {'type': 'object', 'description': 'Response varies based on operation'}


def format_fields_table(fields, include_type=True):
    """Format fields as a markdown table."""
    if not fields or '_error' in fields:
        return ""

    lines = []
    if include_type:
        lines.append("| Field | Type | Required | Description |")
        lines.append("|-------|------|----------|-------------|")
    else:
        lines.append("| Field | Required | Description |")
        lines.append("|-------|----------|-------------|")

    for name, info in fields.items():
        if name.startswith('_'):
            continue

        field_type = info.get('type', 'unknown')
        required = 'Yes' if info.get('required') and not info.get('read_only') else 'No'
        desc = info.get('help_text', '')

        # Add choices to description
        if 'choices' in info:
            choices_str = ', '.join(str(c) for c in info['choices'][:5])
            if len(info['choices']) > 5:
                choices_str += '...'
            desc += f" Choices: [{choices_str}]"

        # Add read/write only markers
        if info.get('read_only'):
            desc = "(read-only) " + desc
        if info.get('write_only'):
            desc = "(write-only) " + desc

        if include_type:
            lines.append(f"| `{name}` | {field_type} | {required} | {desc} |")
        else:
            lines.append(f"| `{name}` | {required} | {desc} |")

    return "\n".join(lines)


def generate_markdown(endpoints):
    """Generate markdown documentation."""
    lines = []

    # Header
    lines.append("# JARVIS Task Management API Blueprint")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("This document provides a comprehensive overview of all API endpoints, their inputs, and outputs.")
    lines.append("")

    # Group by category
    categories = defaultdict(list)
    for endpoint in endpoints:
        category = categorize_endpoint(endpoint['path'], endpoint['name'])
        categories[category].append(endpoint)

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")
    for category in sorted(categories.keys()):
        safe_cat = category.lower().replace(' ', '-').replace('&', 'and')
        count = len(categories[category])
        lines.append(f"- [{category}](#{safe_cat}) ({count} endpoints)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Endpoints by category
    for category in sorted(categories.keys()):
        safe_cat = category.lower().replace(' ', '-').replace('&', 'and')
        lines.append(f"## {category}")
        lines.append("")

        # Summary table
        lines.append("### Quick Reference")
        lines.append("")
        lines.append("| Method | Endpoint | Description |")
        lines.append("|--------|----------|-------------|")

        for endpoint in categories[category]:
            for method in endpoint['methods']:
                desc = ''
                if endpoint['view_class']:
                    desc = inspect.getdoc(endpoint['view_class']) or ''
                    desc = desc.split('\n')[0][:50] if desc else ''

                lines.append(f"| `{method}` | `{endpoint['path']}` | {desc} |")

        lines.append("")

        # Detailed documentation
        lines.append("### Detailed Documentation")
        lines.append("")

        for endpoint in categories[category]:
            path = endpoint['path']
            view_class = endpoint['view_class']

            for method in endpoint['methods']:
                lines.append(f"#### `{method}` {path}")
                lines.append("")

                # Description
                if view_class:
                    docstring = inspect.getdoc(view_class)
                    if docstring:
                        lines.append(f"> {docstring.split(chr(10))[0]}")
                        lines.append("")

                # Action info
                action_name = endpoint['actions'].get(method.lower())
                if action_name:
                    lines.append(f"**Action:** `{action_name}`")
                    lines.append("")

                # Path parameters
                import re
                path_params = re.findall(r'<(\w+:)?(\w+)>', path)
                if path_params:
                    lines.append("**Path Parameters:**")
                    lines.append("")
                    lines.append("| Parameter | Type | Description |")
                    lines.append("|-----------|------|-------------|")
                    for param_type, param_name in path_params:
                        ptype = param_type.rstrip(':') if param_type else 'string'
                        lines.append(f"| `{param_name}` | {ptype} | Required path parameter |")
                    lines.append("")

                # Request body
                if method in ['POST', 'PUT', 'PATCH'] and view_class:
                    request_info = get_request_body_info(view_class, method, action_name)
                    if request_info and request_info.get('fields'):
                        lines.append(f"**Request Body:** `{request_info.get('serializer', 'object')}`")
                        lines.append("")
                        fields_table = format_fields_table(request_info['fields'])
                        if fields_table:
                            lines.append(fields_table)
                            lines.append("")

                # Response
                if view_class:
                    response_info = get_response_info(view_class, method, action_name)
                    if response_info and response_info.get('serializer'):
                        lines.append(f"**Response:** `{response_info['serializer']}`")
                        lines.append("")

                        # Show response fields for GET requests
                        if method == 'GET' and response_info.get('fields'):
                            fields_table = format_fields_table(response_info['fields'])
                            if fields_table:
                                lines.append(fields_table)
                                lines.append("")

                lines.append("---")
                lines.append("")

    return "\n".join(lines)


def generate_quick_reference(endpoints):
    """Generate a compact quick reference."""
    lines = []

    lines.append("# API Quick Reference")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Group by category
    categories = defaultdict(list)
    for endpoint in endpoints:
        category = categorize_endpoint(endpoint['path'], endpoint['name'])
        categories[category].append(endpoint)

    for category in sorted(categories.keys()):
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Method | Endpoint | Input | Output |")
        lines.append("|--------|----------|-------|--------|")

        for endpoint in categories[category]:
            view_class = endpoint['view_class']

            for method in endpoint['methods']:
                # Input
                inputs = []

                # Path params
                import re
                path_params = re.findall(r'<(\w+:)?(\w+)>', endpoint['path'])
                if path_params:
                    inputs.append(f"path: {', '.join(p[1] for p in path_params)}")

                # Body
                if method in ['POST', 'PUT', 'PATCH'] and view_class:
                    serializer_class = getattr(view_class, 'serializer_class', None)
                    if serializer_class:
                        inputs.append(f"body: {serializer_class.__name__}")

                input_str = '; '.join(inputs) if inputs else '-'

                # Output
                output_str = '-'
                if view_class:
                    serializer_class = getattr(view_class, 'serializer_class', None)
                    if serializer_class:
                        if method == 'GET':
                            output_str = f"{serializer_class.__name__}"
                        elif method == 'DELETE':
                            output_str = "204 No Content"
                        else:
                            output_str = f"{serializer_class.__name__}"

                lines.append(f"| `{method}` | `{endpoint['path']}` | {input_str} | {output_str} |")

        lines.append("")

    return "\n".join(lines)


def generate_serializer_docs():
    """Generate documentation for all serializers."""
    lines = []

    lines.append("# API Serializers (Data Models)")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Import all serializers
    from tasks_api import serializers as ser_module

    serializers_found = []
    for name in dir(ser_module):
        obj = getattr(ser_module, name)
        if isinstance(obj, type) and issubclass(obj, Serializer) and obj != Serializer:
            serializers_found.append((name, obj))

    # Group serializers
    groups = defaultdict(list)
    for name, serializer_class in serializers_found:
        if 'Task' in name:
            groups['Task'].append((name, serializer_class))
        elif 'Project' in name:
            groups['Project'].append((name, serializer_class))
        elif 'Section' in name:
            groups['Section'].append((name, serializer_class))
        elif 'Account' in name:
            groups['Account'].append((name, serializer_class))
        elif 'Collaboration' in name or 'Invitation' in name:
            groups['Collaboration'].append((name, serializer_class))
        else:
            groups['Other'].append((name, serializer_class))

    # Document each serializer
    for group_name in sorted(groups.keys()):
        lines.append(f"## {group_name} Serializers")
        lines.append("")

        for name, serializer_class in groups[group_name]:
            lines.append(f"### {name}")
            lines.append("")

            docstring = inspect.getdoc(serializer_class)
            if docstring:
                lines.append(f"> {docstring}")
                lines.append("")

            fields = get_serializer_fields(serializer_class)
            if fields and '_error' not in fields:
                fields_table = format_fields_table(fields)
                if fields_table:
                    lines.append(fields_table)
                    lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def main():
    """Main function to generate API documentation."""
    print("Generating API Blueprint...")
    print("-" * 40)

    try:
        # Get URL resolver
        resolver = get_resolver()

        # Extract all endpoints
        endpoints = extract_urls(resolver.url_patterns)

        # Filter out admin and schema URLs
        endpoints = [e for e in endpoints if not e['path'].startswith('/admin')
                     and not e['path'].startswith('/api/schema')
                     and not e['path'].startswith('/api/docs')
                     and not e['path'].startswith('/api/redoc')]

        print(f"Found {len(endpoints)} endpoints")

        # Generate markdown documentation
        markdown = generate_markdown(endpoints)
        md_file = BASE_DIR / 'api_blueprint.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"Full documentation saved: {md_file}")

        # Generate quick reference
        quick_ref = generate_quick_reference(endpoints)
        quick_ref_file = BASE_DIR / 'api_quick_reference.md'
        with open(quick_ref_file, 'w', encoding='utf-8') as f:
            f.write(quick_ref)
        print(f"Quick reference saved: {quick_ref_file}")

        # Generate serializer docs
        serializer_docs = generate_serializer_docs()
        serializer_file = BASE_DIR / 'api_serializers.md'
        with open(serializer_file, 'w', encoding='utf-8') as f:
            f.write(serializer_docs)
        print(f"Serializer docs saved: {serializer_file}")

        # Summary
        print("-" * 40)
        categories = defaultdict(int)
        for endpoint in endpoints:
            category = categorize_endpoint(endpoint['path'], endpoint['name'])
            categories[category] += len(endpoint['methods'])

        print("Endpoints by category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")

        print("-" * 40)

    except Exception as e:
        print(f"Error generating documentation: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == '__main__':
    main()
