#!/usr/bin/env python3
"""
🤖 Job Description to Agent Converter
======================================

This service analyzes job descriptions in markdown format,
extracts senior-level positions, and creates new agents for Convergio.

Senior Level Hierarchy:
- IC6+ (Individual Contributor 6 and above)
- M6+ (Manager 6 and above)
- GM (General Manager)
- VP (Vice President)
- CEO/CTO/CFO (C-level executives)
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SeniorityDetector:
    """Detects and extracts senior-level positions from job descriptions."""
    
    # Define seniority levels in order (higher index = more senior)
    SENIORITY_HIERARCHY = {
        'IC': {'min_level': 6, 'title': 'Individual Contributor'},
        'M': {'min_level': 6, 'title': 'Manager'},
        'GM': {'min_level': 0, 'title': 'General Manager'},
        'VP': {'min_level': 0, 'title': 'Vice President'},
        'SVP': {'min_level': 0, 'title': 'Senior Vice President'},
        'EVP': {'min_level': 0, 'title': 'Executive Vice President'},
        'CEO': {'min_level': 0, 'title': 'Chief Executive Officer'},
        'CTO': {'min_level': 0, 'title': 'Chief Technology Officer'},
        'CFO': {'min_level': 0, 'title': 'Chief Financial Officer'},
        'COO': {'min_level': 0, 'title': 'Chief Operating Officer'},
        'CPO': {'min_level': 0, 'title': 'Chief Product Officer'},
    }
    
    @classmethod
    def is_senior_level(cls, text: str) -> Tuple[bool, List[str]]:
        """
        Check if the text contains senior-level positions.
        Returns (is_senior, list_of_levels_found)
        """
        senior_levels_found = []
        text_upper = text.upper()
        
        # Check for C-level executives
        for exec_level in ['CEO', 'CTO', 'CFO', 'COO', 'CPO']:
            if exec_level in text_upper:
                senior_levels_found.append(exec_level)
        
        # Check for VP levels
        if 'VP' in text_upper or 'VICE PRESIDENT' in text_upper:
            if 'EVP' in text_upper or 'EXECUTIVE VICE PRESIDENT' in text_upper:
                senior_levels_found.append('EVP')
            elif 'SVP' in text_upper or 'SENIOR VICE PRESIDENT' in text_upper:
                senior_levels_found.append('SVP')
            else:
                senior_levels_found.append('VP')
        
        # Check for GM
        if 'GM' in text_upper or 'GENERAL MANAGER' in text_upper:
            senior_levels_found.append('GM')
        
        # Check for IC and M levels with numbers
        # Pattern: IC6, IC7, IC8, M6, M7, M8, etc.
        ic_pattern = r'\bIC(\d+)\b'
        m_pattern = r'\bM(\d+)\b'
        
        ic_matches = re.findall(ic_pattern, text_upper)
        for level in ic_matches:
            if int(level) >= 6:
                senior_levels_found.append(f'IC{level}')
        
        m_matches = re.findall(m_pattern, text_upper)
        for level in m_matches:
            if int(level) >= 6:
                senior_levels_found.append(f'M{level}')
        
        return len(senior_levels_found) > 0, senior_levels_found


class JobDescriptionParser:
    """Parses job description markdown files and extracts relevant information."""
    
    def __init__(self, input_dir: Path, senior_dir: Path):
        self.input_dir = Path(input_dir)
        self.senior_dir = Path(senior_dir)
        self.senior_dir.mkdir(parents=True, exist_ok=True)
        self.seniority_detector = SeniorityDetector()
    
    def parse_file(self, file_path: Path) -> Optional[Dict]:
        """Parse a single markdown file and extract job information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it's a senior position
            is_senior, levels_found = self.seniority_detector.is_senior_level(content)
            
            if not is_senior:
                logger.debug(f"Skipping {file_path.name} - not a senior position")
                return None
            
            # Extract key information
            job_info = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'senior_levels': levels_found,
                'profession': self._extract_profession(content),
                'discipline': self._extract_discipline(content),
                'role_summary': self._extract_role_summary(content),
                'key_responsibilities': self._extract_responsibilities(content),
                'skills': self._extract_skills(content),
                'content': content  # Keep full content for senior file generation
            }
            
            logger.info(f"Found senior position in {file_path.name}: {levels_found}")
            return job_info
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    def _extract_profession(self, content: str) -> str:
        """Extract profession from markdown content."""
        match = re.search(r'\*\*Profession:\*\*\s*(.+)', content)
        if match:
            return match.group(1).strip()
        return "Unknown"
    
    def _extract_discipline(self, content: str) -> str:
        """Extract discipline from markdown content."""
        match = re.search(r'\*\*Discipline:\*\*\s*(.+)', content)
        if match:
            return match.group(1).strip()
        return "Unknown"
    
    def _extract_role_summary(self, content: str) -> str:
        """Extract role summary from markdown content."""
        # Look for role summary section
        match = re.search(r'\*\*Role Summary\*\*\s*\|?\s*(.+?)(?:\n\n|\|)', content, re.DOTALL)
        if match:
            summary = match.group(1).strip()
            # Clean up the summary
            summary = re.sub(r'\s+', ' ', summary)
            return summary[:500]  # Limit to 500 chars
        return ""
    
    def _extract_responsibilities(self, content: str) -> List[str]:
        """Extract key responsibilities from markdown content."""
        responsibilities = []
        # Look for bullet points in responsibilities section
        resp_section = re.search(r'Key Responsibilities.*?\n(.*?)(?:\n\n|\#)', content, re.DOTALL)
        if resp_section:
            bullets = re.findall(r'\*\s+(.+)', resp_section.group(1))
            responsibilities = [b.strip() for b in bullets[:5]]  # Top 5 responsibilities
        return responsibilities
    
    def _extract_skills(self, content: str) -> List[str]:
        """Extract key skills from markdown content."""
        skills = []
        # Look for skills section
        skills_section = re.search(r'Skills.*?\n(.*?)(?:\n\n|\#|$)', content, re.DOTALL)
        if skills_section:
            # Extract skill names from table or list
            skill_matches = re.findall(r'\*\*([^*]+)\*\*', skills_section.group(1))
            skills = [s.strip() for s in skill_matches[:10]]  # Top 10 skills
        return skills
    
    def process_all_files(self) -> List[Dict]:
        """Process all markdown files in the input directory."""
        senior_jobs = []
        md_files = list(self.input_dir.glob("*.md"))
        
        logger.info(f"Processing {len(md_files)} job description files...")
        
        for file_path in md_files:
            job_info = self.parse_file(file_path)
            if job_info:
                senior_jobs.append(job_info)
                self._save_senior_file(job_info)
        
        logger.info(f"Found {len(senior_jobs)} senior positions")
        return senior_jobs
    
    def _save_senior_file(self, job_info: Dict):
        """Save the senior job description to the senior directory."""
        output_path = self.senior_dir / job_info['file_name']
        
        # Add a header indicating it's a senior position
        header = f"""# SENIOR POSITION - {', '.join(job_info['senior_levels'])}
# Profession: {job_info['profession']}
# Discipline: {job_info['discipline']}
# Generated: {datetime.now().isoformat()}

---

"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header + job_info['content'])
        
        logger.info(f"Saved senior job description: {output_path.name}")


class AgentGenerator:
    """Generates Convergio agent definitions from job descriptions."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_agent(self, job_info: Dict) -> Dict:
        """Create an agent definition from job information."""
        # Generate a unique agent name based on profession and discipline
        base_name = self._generate_agent_name(job_info)
        
        # Determine tier based on seniority level
        tier = self._determine_tier(job_info['senior_levels'])
        
        # Create agent definition in Convergio format
        agent_def = {
            'name': base_name,
            'role': f"{job_info['profession']} - {job_info['discipline']}",
            'tier': tier,
            'expertise': job_info['skills'][:5] if job_info['skills'] else [],
            'description': job_info['role_summary'] or f"Senior {job_info['discipline']} professional",
            'responsibilities': job_info['key_responsibilities'][:3] if job_info['key_responsibilities'] else [],
            'senior_levels': job_info['senior_levels'],
            'source_file': job_info['file_name'],
            'created_at': datetime.now().isoformat()
        }
        
        # Add system prompt for the agent
        agent_def['system_prompt'] = self._generate_system_prompt(agent_def)
        
        return agent_def
    
    def _generate_agent_name(self, job_info: Dict) -> str:
        """Generate a unique agent name."""
        # Clean and format the name
        profession = job_info['profession'].replace(' ', '').replace('-', '')
        discipline = job_info['discipline'].replace(' ', '').replace('-', '')
        
        # Take first letters or abbreviate
        if len(profession) > 10:
            profession = ''.join([word[0].upper() for word in job_info['profession'].split()])
        if len(discipline) > 10:
            discipline = ''.join([word[0].upper() for word in job_info['discipline'].split()])
        
        # Add highest senior level
        level = job_info['senior_levels'][0] if job_info['senior_levels'] else 'SR'
        
        name = f"{profession}_{discipline}_{level}"
        return name
    
    def _determine_tier(self, senior_levels: List[str]) -> int:
        """Determine agent tier based on seniority levels."""
        # Tier 1: C-level
        if any(level in ['CEO', 'CTO', 'CFO', 'COO', 'CPO'] for level in senior_levels):
            return 1
        # Tier 2: VP level
        elif any('VP' in level for level in senior_levels):
            return 2
        # Tier 3: GM and M8+
        elif 'GM' in senior_levels or any('M8' in level or 'M9' in level for level in senior_levels):
            return 3
        # Tier 4: M6-M7 and IC8+
        elif any('M6' in level or 'M7' in level or 'IC8' in level or 'IC9' in level 
                for level in senior_levels):
            return 4
        # Tier 5: IC6-IC7
        else:
            return 5
    
    def _generate_system_prompt(self, agent_def: Dict) -> str:
        """Generate a system prompt for the agent."""
        prompt = f"""You are {agent_def['name']}, a senior {agent_def['role']} at Convergio.
        
Your expertise includes: {', '.join(agent_def['expertise'])}.

Your key responsibilities:
{chr(10).join([f"- {resp}" for resp in agent_def['responsibilities']])}

You are a {agent_def['tier']} tier expert with {', '.join(agent_def['senior_levels'])} level experience.
Provide strategic insights and leadership guidance based on your extensive experience.
Focus on high-level strategy, organizational transformation, and cross-functional alignment."""
        
        return prompt
    
    def save_agent(self, agent_def: Dict):
        """Save agent definition to a Python file in Convergio format."""
        file_name = f"{agent_def['name'].lower()}.py"
        file_path = self.output_dir / file_name

        # Generate Python code for the agent
        code = f'''"""
{agent_def['name']} - {agent_def['role']}
Generated from: {agent_def['source_file']}
Created: {agent_def['created_at']}
"""

# Using modern AutoGen 0.7.x agent classes
from autogen_agentchat.agents import AssistantAgent
from typing import Dict, Any

class {agent_def['name']}:
    """
    {agent_def['description']}
    
    Senior Levels: {', '.join(agent_def['senior_levels'])}
    Tier: {agent_def['tier']}
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        self.name = "{agent_def['name']}"
        self.role = "{agent_def['role']}"
        self.tier = {agent_def['tier']}
        self.expertise = {agent_def['expertise']}
        
        self.agent = AssistantAgent(
            name=self.name,
            system_message="""{agent_def['system_prompt']}""",
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=False
        )
    
    def get_agent(self):
        """Return the AssistantAgent instance."""
        return self.agent

# Agent metadata for dynamic loading
AGENT_METADATA = {{
    "name": "{agent_def['name']}",
    "role": "{agent_def['role']}",
    "tier": {agent_def['tier']},
    "expertise": {agent_def['expertise']},
    "senior_levels": {agent_def['senior_levels']},
    "source": "{agent_def['source_file']}"
}}
'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Created agent: {file_name}")
        
        # Also save metadata as YAML for Ali's orchestration
        self._save_agent_metadata(agent_def)
    
    def _save_agent_metadata(self, agent_def: Dict):
        """Save agent metadata as YAML for orchestration."""
        yaml_file = self.output_dir / f"{agent_def['name'].lower()}.yaml"
        
        metadata = {
            'name': agent_def['name'],
            'role': agent_def['role'],
            'tier': agent_def['tier'],
            'expertise': agent_def['expertise'],
            'senior_levels': agent_def['senior_levels'],
            'responsibilities': agent_def['responsibilities'],
            'source_file': agent_def['source_file'],
            'created_at': agent_def['created_at']
        }
        
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        logger.info(f"Saved metadata: {yaml_file.name}")


class JobDescription2Agent:
    """Main orchestrator for converting job descriptions to agents."""
    
    def __init__(self):
        # Setup paths
        self.base_dir = Path(__file__).resolve().parents[3]  # convergio root
        self.job_desc_dir = self.base_dir / "jobDescriptions" / "md"
        self.senior_dir = self.base_dir / "jobDescriptions" / "senior"
        self.agents_dir = self.base_dir / "backend" / "src" / "agents" / "definitions" / "newJobs"
        
        # Initialize components
        self.parser = JobDescriptionParser(self.job_desc_dir, self.senior_dir)
        self.generator = AgentGenerator(self.agents_dir)
        
        logger.info("JobDescription2Agent initialized")
        logger.info(f"Input: {self.job_desc_dir}")
        logger.info(f"Senior output: {self.senior_dir}")
        logger.info(f"Agents output: {self.agents_dir}")
    
    def run(self) -> Dict:
        """Run the complete conversion process."""
        logger.info("="*60)
        logger.info("Starting JobDescription2Agent conversion...")
        logger.info("="*60)
        
        results = {
            'start_time': datetime.now().isoformat(),
            'senior_jobs_found': 0,
            'agents_created': 0,
            'errors': [],
            'agents': []
        }
        
        try:
            # Step 1: Parse job descriptions and extract senior positions
            logger.info("\n📄 Step 1: Parsing job descriptions...")
            senior_jobs = self.parser.process_all_files()
            results['senior_jobs_found'] = len(senior_jobs)
            
            # Step 2: Generate agents from senior positions
            logger.info(f"\n🤖 Step 2: Generating {len(senior_jobs)} agents...")
            for job_info in senior_jobs:
                try:
                    agent_def = self.generator.create_agent(job_info)
                    self.generator.save_agent(agent_def)
                    results['agents'].append(agent_def['name'])
                    results['agents_created'] += 1
                except Exception as e:
                    error_msg = f"Failed to create agent from {job_info['file_name']}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Step 3: Create integration manifest
            logger.info("\n🔗 Step 3: Creating integration manifest...")
            self._create_integration_manifest(results['agents'])
            
        except Exception as e:
            error_msg = f"Fatal error: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Save results
        self._save_results(results)
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _create_integration_manifest(self, agent_names: List[str]):
        """Create a manifest file for integrating new agents."""
        manifest_path = self.agents_dir / "manifest.json"
        
        manifest = {
            'created_at': datetime.now().isoformat(),
            'agents': agent_names,
            'count': len(agent_names),
            'status': 'pending_integration',
            'integration_steps': [
                'Load agent definitions',
                'Register with Ali orchestrator',
                'Update agent database',
                'Verify agent availability'
            ]
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Created integration manifest: {manifest_path}")
    
    def _save_results(self, results: Dict):
        """Save conversion results to a file."""
        results_path = self.senior_dir / "conversion_results.json"
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results: {results_path}")
    
    def _print_summary(self, results: Dict):
        """Print a summary of the conversion process."""
        print("\n" + "="*60)
        print("🎉 JobDescription2Agent Conversion Complete!")
        print("="*60)
        print("📊 Summary:")
        print(f"  • Job descriptions analyzed: {len(list(self.job_desc_dir.glob('*.md')))}")
        print(f"  • Senior positions found: {results['senior_jobs_found']}")
        print(f"  • Agents created: {results['agents_created']}")
        print(f"  • Errors: {len(results['errors'])}")
        print("\n📁 Output locations:")
        print(f"  • Senior job descriptions: {self.senior_dir}")
        print(f"  • New agents: {self.agents_dir}")
        print("\n✅ Next steps:")
        print(f"  1. Review generated agents in {self.agents_dir}")
        print("  2. Run integration script to add agents to Convergio")
        print("  3. Verify agents with Ali orchestrator")
        print("="*60)


if __name__ == "__main__":
    # Run the conversion
    converter = JobDescription2Agent()
    results = converter.run()
    
    # Exit with appropriate code
    exit(0 if results['agents_created'] > 0 else 1)