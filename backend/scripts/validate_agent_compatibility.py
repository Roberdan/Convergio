#!/usr/bin/env python3
"""
Agent Compatibility Validation Script
Validates all agent .md files for Microsoft Agent Framework compatibility
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class AgentValidation:
    """Validation result for a single agent"""
    file_name: str
    agent_name: str = ""
    description: str = ""
    tools: List[str] = field(default_factory=list)
    color: str = ""

    # Validation flags
    has_valid_frontmatter: bool = False
    has_name: bool = False
    has_description: bool = False
    has_tools_array: bool = False
    has_color: bool = False
    has_persona: bool = False
    has_security_framework: bool = False

    # Content analysis
    content_length: int = 0
    has_autogen_references: bool = False
    autogen_patterns: List[str] = field(default_factory=list)

    # Issues
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_compatible(self) -> bool:
        """Check if agent is fully compatible"""
        return (
            self.has_valid_frontmatter and
            self.has_name and
            self.has_description and
            self.has_persona and
            not self.has_autogen_references and
            len(self.issues) == 0
        )

    @property
    def compatibility_status(self) -> str:
        """Get compatibility status"""
        if self.is_compatible:
            return "✅ COMPATIBLE"
        elif len(self.issues) == 0 and len(self.warnings) <= 2:
            return "⚠️  MINOR ISSUES"
        elif len(self.issues) > 0:
            return "❌ INCOMPATIBLE"
        else:
            return "⚠️  NEEDS REVIEW"


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter from markdown"""
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)
        return frontmatter, body
    except yaml.YAMLError:
        return {}, content


def check_autogen_patterns(content: str) -> Tuple[bool, List[str]]:
    """Check for AutoGen-specific patterns that need migration"""
    autogen_patterns = [
        (r'\bAssistantAgent\b', 'AssistantAgent class'),
        (r'\bUserProxyAgent\b', 'UserProxyAgent class'),
        (r'\bGroupChat\b', 'GroupChat class'),
        (r'\bGroupChatManager\b', 'GroupChatManager class'),
        (r'\bFunctionTool\b', 'FunctionTool class'),
        (r'\bregister_function\b', 'register_function method'),
        (r'\bConversableAgent\b', 'ConversableAgent class'),
        (r'autogen\.', 'autogen module reference'),
        (r'\bllm_config\b', 'llm_config parameter'),
        (r'\bcode_execution_config\b', 'code_execution_config parameter'),
    ]

    found_patterns = []
    for pattern, description in autogen_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found_patterns.append(description)

    return len(found_patterns) > 0, found_patterns


def validate_agent_file(file_path: Path) -> AgentValidation:
    """Validate a single agent markdown file"""
    validation = AgentValidation(file_name=file_path.name)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        validation.content_length = len(content)

        # Extract frontmatter
        frontmatter, body = extract_frontmatter(content)

        if frontmatter:
            validation.has_valid_frontmatter = True

            # Check required fields
            if 'name' in frontmatter:
                validation.has_name = True
                validation.agent_name = frontmatter['name']
            else:
                validation.issues.append("Missing 'name' field in frontmatter")

            if 'description' in frontmatter:
                validation.has_description = True
                validation.description = frontmatter['description']
            else:
                validation.issues.append("Missing 'description' field in frontmatter")

            if 'tools' in frontmatter:
                validation.has_tools_array = True
                if isinstance(frontmatter['tools'], list):
                    validation.tools = frontmatter['tools']
                else:
                    validation.warnings.append("'tools' field is not a list")
            else:
                validation.warnings.append("Missing 'tools' field in frontmatter")

            if 'color' in frontmatter:
                validation.has_color = True
                validation.color = frontmatter['color']
            else:
                validation.warnings.append("Missing 'color' field in frontmatter")
        else:
            validation.issues.append("No valid YAML frontmatter found")

        # Check body content
        if body:
            # Check for persona/identity section
            if re.search(r'(You are|PERSONA|Core Identity)', body, re.IGNORECASE):
                validation.has_persona = True
            else:
                validation.issues.append("No clear persona/identity section found")

            # Check for security framework
            if re.search(r'Security.*Framework|Ethics.*Framework', body, re.IGNORECASE):
                validation.has_security_framework = True

            # Check for AutoGen patterns
            has_autogen, patterns = check_autogen_patterns(body)
            validation.has_autogen_references = has_autogen
            validation.autogen_patterns = patterns

            if has_autogen:
                validation.issues.append(f"Contains AutoGen-specific patterns: {', '.join(patterns)}")

        # Check if content is too short
        if validation.content_length < 500:
            validation.warnings.append("Agent definition seems too short (< 500 chars)")

    except Exception as e:
        validation.issues.append(f"Error reading file: {str(e)}")

    return validation


def generate_compatibility_report(
    validations: List[AgentValidation],
    output_path: Path
) -> None:
    """Generate comprehensive compatibility report"""

    # Sort by status
    compatible = [v for v in validations if v.is_compatible]
    minor_issues = [v for v in validations if v.compatibility_status == "⚠️  MINOR ISSUES"]
    incompatible = [v for v in validations if v.compatibility_status == "❌ INCOMPATIBLE"]
    needs_review = [v for v in validations if v.compatibility_status == "⚠️  NEEDS REVIEW"]

    report = []
    report.append("# Agent Compatibility Report")
    report.append("")
    report.append("**Microsoft Agent Framework Compatibility Analysis**")
    report.append("")
    report.append(f"**Generated:** {Path(__file__).name}")
    report.append(f"**Total Agents Analyzed:** {len(validations)}")
    report.append("")

    # Summary
    report.append("## Executive Summary")
    report.append("")
    report.append(f"- ✅ **Fully Compatible:** {len(compatible)} agents")
    report.append(f"- ⚠️  **Minor Issues:** {len(minor_issues)} agents")
    report.append(f"- ⚠️  **Needs Review:** {len(needs_review)} agents")
    report.append(f"- ❌ **Incompatible:** {len(incompatible)} agents")
    report.append("")
    report.append(f"**Compatibility Rate:** {len(compatible) / len(validations) * 100:.1f}%")
    report.append("")

    # Detailed Analysis
    report.append("## Compatibility Analysis")
    report.append("")

    # Section 1: Compatible Agents
    if compatible:
        report.append("### ✅ Fully Compatible Agents")
        report.append("")
        report.append(f"**{len(compatible)} agents** are fully compatible with Microsoft Agent Framework:")
        report.append("")
        for v in sorted(compatible, key=lambda x: x.agent_name):
            report.append(f"- **{v.agent_name}** (`{v.file_name}`)")
            report.append(f"  - Description: {v.description[:80]}...")
            report.append(f"  - Tools: {len(v.tools)} defined")
            report.append("")

    # Section 2: Minor Issues
    if minor_issues:
        report.append("### ⚠️  Agents with Minor Issues")
        report.append("")
        report.append(f"**{len(minor_issues)} agents** have minor issues that can be easily fixed:")
        report.append("")
        for v in sorted(minor_issues, key=lambda x: x.agent_name):
            report.append(f"#### {v.agent_name} (`{v.file_name}`)")
            report.append("")
            if v.warnings:
                report.append("**Warnings:**")
                for warning in v.warnings:
                    report.append(f"- {warning}")
                report.append("")

    # Section 3: Needs Review
    if needs_review:
        report.append("### ⚠️  Agents Needing Review")
        report.append("")
        report.append(f"**{len(needs_review)} agents** need careful review:")
        report.append("")
        for v in sorted(needs_review, key=lambda x: x.agent_name):
            report.append(f"#### {v.agent_name} (`{v.file_name}`)")
            report.append("")
            if v.issues:
                report.append("**Issues:**")
                for issue in v.issues:
                    report.append(f"- {issue}")
                report.append("")
            if v.warnings:
                report.append("**Warnings:**")
                for warning in v.warnings:
                    report.append(f"- {warning}")
                report.append("")

    # Section 4: Incompatible Agents
    if incompatible:
        report.append("### ❌ Incompatible Agents")
        report.append("")
        report.append(f"**{len(incompatible)} agents** have critical compatibility issues:")
        report.append("")
        for v in sorted(incompatible, key=lambda x: x.agent_name):
            report.append(f"#### {v.agent_name} (`{v.file_name}`)")
            report.append("")
            report.append(f"**Status:** {v.compatibility_status}")
            report.append("")
            if v.issues:
                report.append("**Critical Issues:**")
                for issue in v.issues:
                    report.append(f"- {issue}")
                report.append("")
            if v.autogen_patterns:
                report.append("**AutoGen Patterns Found:**")
                for pattern in v.autogen_patterns:
                    report.append(f"- {pattern}")
                report.append("")

    # Technical Details
    report.append("## Technical Analysis")
    report.append("")

    # Frontmatter validation
    report.append("### Frontmatter Validation")
    report.append("")
    valid_frontmatter = sum(1 for v in validations if v.has_valid_frontmatter)
    report.append(f"- **Valid YAML Frontmatter:** {valid_frontmatter}/{len(validations)}")
    report.append(f"- **Has 'name' field:** {sum(1 for v in validations if v.has_name)}/{len(validations)}")
    report.append(f"- **Has 'description' field:** {sum(1 for v in validations if v.has_description)}/{len(validations)}")
    report.append(f"- **Has 'tools' array:** {sum(1 for v in validations if v.has_tools_array)}/{len(validations)}")
    report.append(f"- **Has 'color' field:** {sum(1 for v in validations if v.has_color)}/{len(validations)}")
    report.append("")

    # Content validation
    report.append("### Content Validation")
    report.append("")
    report.append(f"- **Has Persona/Identity:** {sum(1 for v in validations if v.has_persona)}/{len(validations)}")
    report.append(f"- **Has Security Framework:** {sum(1 for v in validations if v.has_security_framework)}/{len(validations)}")
    report.append(f"- **AutoGen References Found:** {sum(1 for v in validations if v.has_autogen_references)}/{len(validations)}")
    report.append("")

    # Tools analysis
    report.append("### Tools Analysis")
    report.append("")
    all_tools = defaultdict(int)
    for v in validations:
        for tool in v.tools:
            all_tools[tool] += 1

    report.append("**Most Common Tools:**")
    for tool, count in sorted(all_tools.items(), key=lambda x: x[1], reverse=True)[:15]:
        report.append(f"- `{tool}`: used by {count} agents")
    report.append("")

    # Migration Recommendations
    report.append("## Migration Recommendations")
    report.append("")
    report.append("### Immediate Actions")
    report.append("")

    if incompatible:
        report.append("1. **Fix Incompatible Agents:**")
        for v in incompatible:
            report.append(f"   - Review `{v.file_name}` - {', '.join(v.issues[:2])}")
        report.append("")

    if minor_issues:
        report.append("2. **Address Minor Issues:**")
        report.append(f"   - {len(minor_issues)} agents need minor updates")
        report.append("")

    report.append("### Framework Compatibility")
    report.append("")
    report.append("**Microsoft Agent Framework Requirements:**")
    report.append("")
    report.append("- ✅ **ChatAgent Creation:**")
    report.append("  ```python")
    report.append("  agent = chat_client.create_agent(")
    report.append("      name=metadata.key,")
    report.append("      instructions=instructions,  # Full markdown content")
    report.append("      tools=tools  # List of @ai_function decorated functions")
    report.append("  )")
    report.append("  ```")
    report.append("")
    report.append("- ✅ **Supported Elements:**")
    report.append("  - YAML frontmatter with name, description, tools, color")
    report.append("  - Markdown-formatted instructions/persona")
    report.append("  - Tool references as string array")
    report.append("  - Multi-turn conversations by default")
    report.append("")
    report.append("- ❌ **NOT Supported (AutoGen-specific):**")
    report.append("  - `AssistantAgent`, `UserProxyAgent` classes")
    report.append("  - `llm_config` dictionaries")
    report.append("  - `GroupChat`, `GroupChatManager` classes")
    report.append("  - `FunctionTool` wrapper classes")
    report.append("  - `register_function` methods")
    report.append("")

    # Conclusion
    report.append("## Conclusion")
    report.append("")

    if len(compatible) >= len(validations) * 0.8:
        report.append(f"✅ **{len(compatible)}/{len(validations)} agents ({len(compatible)/len(validations)*100:.1f}%) are already compatible** with Microsoft Agent Framework.")
        report.append("")
        report.append("The agent definitions follow a clean, framework-agnostic structure that maps well to ChatAgent:")
        report.append("- YAML frontmatter provides metadata")
        report.append("- Markdown content serves as instructions")
        report.append("- Tool references are declarative")
        report.append("")
        if minor_issues or incompatible:
            report.append(f"Minor updates needed for {len(minor_issues) + len(incompatible)} agents to ensure full compatibility.")
    else:
        report.append(f"⚠️  **{len(incompatible) + len(needs_review)} agents need attention** before full migration.")
        report.append("")
        report.append("Review and update incompatible agents to remove AutoGen-specific patterns.")

    report.append("")
    report.append("---")
    report.append("")
    report.append("*This report was generated automatically. Review all agents manually before migration.*")

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))


def main():
    """Main validation function"""
    # Find agents directory
    backend_dir = Path(__file__).parent.parent
    agents_dir = backend_dir / "src" / "agents" / "definitions"

    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return

    print(f"📂 Analyzing agents in: {agents_dir}")
    print("")

    # Find all .md files
    agent_files = list(agents_dir.glob("*.md"))
    print(f"Found {len(agent_files)} agent files")
    print("")

    # Validate each agent
    validations = []
    for agent_file in sorted(agent_files):
        print(f"Validating {agent_file.name}...", end=" ")
        validation = validate_agent_file(agent_file)
        validations.append(validation)
        print(validation.compatibility_status)

    print("")
    print("=" * 70)
    print("")

    # Generate report
    output_path = backend_dir.parent / "docs" / "AGENT_COMPATIBILITY_REPORT.md"
    output_path.parent.mkdir(exist_ok=True)

    print("📝 Generating compatibility report...")
    generate_compatibility_report(validations, output_path)

    print(f"✅ Report generated: {output_path}")
    print("")

    # Summary
    compatible = sum(1 for v in validations if v.is_compatible)
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Agents:         {len(validations)}")
    print(f"✅ Compatible:        {compatible}")
    print(f"❌ Incompatible:      {len(validations) - compatible}")
    print(f"Compatibility Rate:   {compatible / len(validations) * 100:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
