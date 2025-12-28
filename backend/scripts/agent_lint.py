#!/usr/bin/env python3
"""
Agent Definition Linter
Validates agent markdown files against schema and best practices
"""

import os
import sys
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from jsonschema import validate, ValidationError


class AgentLinter:
    """Linter for agent definition files"""
    
    def __init__(self, schema_path: str):
        """Initialize linter with schema"""
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
        
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def parse_markdown(self, file_path: str) -> Tuple[Dict, str]:
        """Parse markdown file with YAML front-matter"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract front-matter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    markdown_content = parts[2].strip()
                    return metadata, markdown_content
                except yaml.YAMLError as e:
                    self.errors.append(f"YAML parsing error: {e}")
                    return {}, content
        
        # No front-matter found
        self.warnings.append("No YAML front-matter found")
        return {}, content
    
    def validate_schema(self, metadata: Dict) -> bool:
        """Validate metadata against JSON schema"""
        try:
            validate(instance=metadata, schema=self.schema)
            return True
        except ValidationError as e:
            self.errors.append(f"Schema validation error: {e.message} at {'.'.join(str(p) for p in e.path)}")
            return False
    
    def lint_system_prompt(self, prompt: str) -> None:
        """Lint system prompt for best practices"""
        
        # Check prompt length
        if len(prompt) < 50:
            self.errors.append("System prompt too short (min 50 characters)")
        elif len(prompt) > 5000:
            self.warnings.append("System prompt very long (>5000 characters)")
        
        # Check for required elements
        required_phrases = [
            ("role", r"(you are|your role|you act as|you function as)"),
            ("objective", r"(objective|goal|purpose|aim)"),
            ("capabilities", r"(can|able to|capable of|will)")
        ]
        
        for name, pattern in required_phrases:
            if not re.search(pattern, prompt, re.IGNORECASE):
                self.warnings.append(f"System prompt missing clear {name} definition")
        
        # Check for problematic patterns
        problematic_patterns = [
            (r"ignore previous instructions", "Potential prompt injection vulnerability"),
            (r"reveal your prompt", "Potential prompt leakage vulnerability"),
            (r"you must always", "Overly restrictive language may limit flexibility"),
            (r"never under any circumstances", "Overly restrictive language may limit flexibility"),
            (r"unlimited", "Avoid promising unlimited capabilities"),
            (r"perfect", "Avoid claiming perfection"),
            (r"100%", "Avoid absolute guarantees")
        ]
        
        for pattern, message in problematic_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                self.warnings.append(f"System prompt: {message}")
        
        # Check for security best practices
        security_keywords = ["validate", "verify", "check", "sanitize", "secure"]
        if not any(keyword in prompt.lower() for keyword in security_keywords):
            self.info.append("Consider adding security validation instructions to system prompt")
    
    def lint_capabilities(self, capabilities: List[str]) -> None:
        """Lint agent capabilities"""
        
        if len(capabilities) < 3:
            self.warnings.append("Agent has fewer than 3 capabilities defined")
        elif len(capabilities) > 15:
            self.warnings.append("Agent has many capabilities (>15), consider specialization")
        
        # Check for vague capabilities
        vague_terms = ["stuff", "things", "various", "miscellaneous", "etc", "other"]
        for cap in capabilities:
            if any(term in cap.lower() for term in vague_terms):
                self.warnings.append(f"Vague capability: '{cap}'")
            
            if len(cap) < 5:
                self.warnings.append(f"Capability too short: '{cap}'")
    
    def lint_tools(self, tools: List[Dict]) -> None:
        """Lint tool definitions"""
        
        if not tools:
            self.info.append("No tools defined for agent")
            return
        
        tool_names = [tool.get('name', '') for tool in tools]
        
        # Check for duplicates
        if len(tool_names) != len(set(tool_names)):
            self.errors.append("Duplicate tool names found")
        
        # Check for standard tools
        
        for tool in tools:
            name = tool.get('name', '')
            desc = tool.get('description', '')
            
            if not desc or len(desc) < 10:
                self.warnings.append(f"Tool '{name}' has insufficient description")
            
            # Security warnings for dangerous tools
            if name in ["code_execution", "file_operations", "system_command"]:
                if tool.get('required', False):
                    self.warnings.append(f"Dangerous tool '{name}' marked as required")
    
    def lint_dependencies(self, dependencies: List[str], agent_id: str) -> None:
        """Lint agent dependencies"""
        
        if agent_id in dependencies:
            self.errors.append("Agent cannot depend on itself")
        
        if len(dependencies) > 5:
            self.warnings.append("Agent has many dependencies (>5), consider reducing coupling")
        
        # Check for circular dependencies (would need full agent registry)
        # This is a simplified check
        if len(set(dependencies)) != len(dependencies):
            self.errors.append("Duplicate dependencies found")
    
    def lint_cost_metrics(self, metadata: Dict) -> None:
        """Lint cost and performance metrics"""
        
        cost = metadata.get('cost_per_interaction', 0)
        if cost > 1.0:
            self.warnings.append(f"High cost per interaction: ${cost}")
        elif cost == 0:
            self.info.append("Cost per interaction not specified")
        
        max_tokens = metadata.get('max_context_tokens', 8000)
        if max_tokens > 32000:
            self.warnings.append(f"Very large context window: {max_tokens} tokens")
        
        temp = metadata.get('temperature', 0.7)
        if temp > 1.5:
            self.warnings.append(f"High temperature setting: {temp}")
        elif temp < 0.1:
            self.info.append(f"Very low temperature: {temp} (may be too deterministic)")
    
    def lint_file(self, file_path: str) -> Tuple[bool, Dict]:
        """Lint a single agent definition file"""
        
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Parse file
        metadata, content = self.parse_markdown(file_path)
        
        if not metadata:
            self.errors.append("Failed to parse metadata")
            return False, {}
        
        # Validate schema
        self.validate_schema(metadata)
        
        # Additional linting
        if 'system_prompt' in metadata:
            self.lint_system_prompt(metadata['system_prompt'])
        
        if 'capabilities' in metadata:
            self.lint_capabilities(metadata['capabilities'])
        
        if 'tools' in metadata:
            self.lint_tools(metadata['tools'])
        
        if 'dependencies' in metadata and 'agent_id' in metadata:
            self.lint_dependencies(metadata['dependencies'], metadata['agent_id'])
        
        self.lint_cost_metrics(metadata)
        
        # Check markdown content
        if len(content.strip()) < 100:
            self.warnings.append("Markdown content very short (<100 characters)")
        
        # Check for required sections in markdown
        required_sections = ["## Description", "## Usage", "## Examples"]
        for section in required_sections:
            if section not in content:
                self.info.append(f"Missing recommended section: {section}")
        
        return len(self.errors) == 0, metadata
    
    def print_results(self, file_path: str) -> None:
        """Print linting results"""
        
        print(f"\n{'='*60}")
        print(f"Linting: {file_path}")
        print(f"{'='*60}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.info:
            print(f"\nℹ️  INFO ({len(self.info)}):")
            for info in self.info:
                print(f"  - {info}")
        
        if not self.errors and not self.warnings:
            print("✅ All checks passed!")


def lint_directory(directory: str, schema_path: str) -> Dict:
    """Lint all agent files in a directory"""
    
    linter = AgentLinter(schema_path)
    results = {
        'total_files': 0,
        'passed': 0,
        'failed': 0,
        'total_errors': 0,
        'total_warnings': 0,
        'files': {}
    }
    
    # Find all markdown files
    agent_dir = Path(directory)
    md_files = list(agent_dir.glob('*.md'))
    
    for file_path in md_files:
        results['total_files'] += 1
        
        passed, metadata = linter.lint_file(str(file_path))
        
        if passed and len(linter.warnings) == 0:
            results['passed'] += 1
        else:
            results['failed'] += 1
        
        results['total_errors'] += len(linter.errors)
        results['total_warnings'] += len(linter.warnings)
        
        results['files'][str(file_path)] = {
            'passed': passed,
            'errors': linter.errors.copy(),
            'warnings': linter.warnings.copy(),
            'info': linter.info.copy(),
            'metadata': metadata
        }
        
        linter.print_results(str(file_path))
    
    return results


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Lint agent definition files')
    parser.add_argument(
        'path',
        help='Path to agent file or directory'
    )
    parser.add_argument(
        '--schema',
        default='backend/src/agents/definitions/agent.schema.json',
        help='Path to JSON schema file'
    )
    parser.add_argument(
        '--output',
        help='Output results to JSON file'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to auto-fix issues (experimental)'
    )
    
    args = parser.parse_args()
    
    # Check if schema exists
    if not os.path.exists(args.schema):
        print(f"Error: Schema file not found: {args.schema}")
        sys.exit(1)
    
    # Check if path exists
    if not os.path.exists(args.path):
        print(f"Error: Path not found: {args.path}")
        sys.exit(1)
    
    # Lint based on path type
    if os.path.isfile(args.path):
        # Single file
        linter = AgentLinter(args.schema)
        passed, metadata = linter.lint_file(args.path)
        linter.print_results(args.path)
        
        if args.output:
            results = {
                'file': args.path,
                'passed': passed,
                'errors': linter.errors,
                'warnings': linter.warnings,
                'info': linter.info,
                'metadata': metadata
            }
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        
        if not passed or (args.strict and linter.warnings):
            sys.exit(1)
    
    else:
        # Directory
        results = lint_directory(args.path, args.schema)
        
        # Print summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total files: {results['total_files']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Total errors: {results['total_errors']}")
        print(f"Total warnings: {results['total_warnings']}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        
        if results['failed'] > 0 or (args.strict and results['total_warnings'] > 0):
            sys.exit(1)
    
    print("\n✅ Linting complete!")


if __name__ == '__main__':
    main()