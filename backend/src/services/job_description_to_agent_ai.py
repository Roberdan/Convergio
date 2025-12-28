#!/usr/bin/env python3
"""
🤖 AI-Powered Job Description to Agent Generator
=================================================

Uses OpenAI to intelligently convert senior-level job descriptions 
into high-quality Convergio agent definitions with proper .md format.

Creates agents similar to amy-cfo.md format using AI to:
- Generate creative, appropriate agent names
- Create compelling agent descriptions
- Design comprehensive competencies
- Develop specialized methodologies
- Craft professional communication protocols
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
import random
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AIAgentGenerator:
    """Generates Convergio agents using OpenAI for intelligent content creation."""
    
    # Professional color palette
    AGENT_COLORS = [
        "#16A085",  # Teal (like Amy)
        "#2E86AB",  # Professional Blue
        "#A23B72",  # Executive Purple
        "#F18F01",  # Dynamic Orange
        "#8B5A3C",  # Trustworthy Brown
        "#2F4858",  # Sophisticated Navy
        "#7A306C",  # Strategic Violet
        "#03B5AA",  # Innovation Turquoise
        "#E84855",  # Leadership Coral
        "#3A506B",  # Corporate Steel
        "#5B9279",  # Growth Sage
        "#BB4430",  # Energy Burnt Orange
        "#7768AE",  # Wisdom Lavender
        "#4B8F8C",  # Balance Teal
        "#C73E1D",  # Passion Red
    ]
    
    # Tool sets by profession type
    TOOL_SETS = {
        'technical': ["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob", "WebFetch", "WebSearch"],
        'finance': ["Read", "WebFetch", "WebSearch", "Grep", "Glob"],
        'management': ["Read", "WebFetch", "WebSearch", "TodoWrite", "Grep", "Task"],
        'sales': ["Read", "WebFetch", "WebSearch", "Grep"],
        'hr': ["Read", "WebFetch", "WebSearch", "Grep"],
        'marketing': ["Read", "WebFetch", "WebSearch", "Grep", "Write"],
        'operations': ["Read", "Bash", "Grep", "Glob", "TodoWrite", "Task"],
        'strategy': ["Read", "WebFetch", "WebSearch", "Task", "TodoWrite"],
        'default': ["Read", "WebFetch", "WebSearch", "Grep", "Glob"]
    }
    
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        
        # Track generated names to avoid duplicates
        self.generated_names = set()
        self.agent_count = 0
    
    def generate_agent_from_job(self, job_file: Path) -> Optional[Dict]:
        """Generate an agent using AI from a senior job description."""
        logger.info(f"🎯 Processing: {job_file.name}")
        
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                job_content = f.read()
            
            # Parse basic metadata
            metadata = self._parse_metadata(job_content)
            
            # Generate agent using AI
            agent_data = self._generate_agent_with_ai(job_content, metadata)
            
            if not agent_data:
                logger.warning(f"  ❌ Could not generate agent from {job_file.name}")
                return None
            
            # Save agent file
            output_file = self._save_agent(agent_data['name'], agent_data['content'])
            
            return {
                'source_file': job_file.name,
                'agent_name': agent_data['name'],
                'output_file': output_file,
                'level': metadata.get('level'),
                'profession': agent_data.get('profession'),
                'discipline': agent_data.get('discipline')
            }
            
        except Exception as e:
            logger.error(f"  ❌ Error processing {job_file.name}: {str(e)}")
            return None
    
    def _parse_metadata(self, content: str) -> Dict:
        """Parse metadata from job description."""
        metadata = {}
        
        # Extract from YAML frontmatter if present
        if content.startswith('---'):
            yaml_end = content.find('---', 3)
            if yaml_end > 0:
                yaml_content = content[3:yaml_end]
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip().lower()] = value.strip()
        
        # Also extract from content
        profession_match = re.search(r'\*\*Profession:\*\*\s*(.+)', content)
        if profession_match:
            metadata['profession'] = profession_match.group(1).strip()
        
        discipline_match = re.search(r'\*\*Discipline:\*\*\s*(.+)', content)
        if discipline_match:
            metadata['discipline'] = discipline_match.group(1).strip()
        
        return metadata
    
    def _generate_agent_with_ai(self, job_content: str, metadata: Dict) -> Optional[Dict]:
        """Use OpenAI to generate a complete agent from job description."""
        
        # Read amy-cfo.md as reference
        reference_path = Path(__file__).parents[1] / "agents" / "definitions" / "amy-cfo.md"
        with open(reference_path, 'r', encoding='utf-8') as f:
            reference_agent = f.read()
        
        # Determine appropriate tools
        profession = metadata.get('profession', '').lower()
        tools = self._select_tools(profession)
        
        # Select a unique color
        color = random.choice(self.AGENT_COLORS)
        
        # Craft the prompt for OpenAI
        prompt = f"""You are an expert at creating AI agent personalities for Convergio, a sophisticated business automation platform.

I need you to create a new agent definition based on a senior-level job description. The agent should be professional, competent, and aligned with Convergio's standards.

REFERENCE AGENT FORMAT (amy-cfo.md):
{reference_agent[:int(os.getenv("REFERENCE_AGENT_TRUNCATE_LENGTH", "3000"))]}...

JOB DESCRIPTION TO CONVERT:
{job_content}

REQUIREMENTS:
1. Generate a unique, professional agent name (format: firstname-role, like "amy-cfo" or "alex-cto")
   - Use a professional first name
   - Include the role abbreviation or title
   - Make it memorable and appropriate for the role
   - Do NOT use names that have already been used: {', '.join(self.generated_names) if self.generated_names else 'none yet'}

2. Create a compelling one-line description (max 200 chars) that captures:
   - The seniority level (IC6, M6, VP, etc.)
   - The primary expertise area
   - Key value proposition

3. Structure the agent EXACTLY like amy-cfo.md with these sections:
   - Security & Ethics Framework (adapt to the role)
   - Core Identity (role-specific)
   - Core Competencies (based on job responsibilities)
   - Communication Protocols
   - Specialized Methodologies (create 3-4 role-specific methodologies)
   - Key Deliverables (5-7 concrete deliverables)
   - Advanced Applications (3 areas with 4 bullets each)
   - Success Metrics Focus (5 specific metrics with targets)
   - Integration Guidelines (how this agent works with others)
   - Global Intelligence Requirements (if applicable)

4. Maintain Convergio's professional tone:
   - Use "I" statements in the ethics section
   - Be specific about expertise areas
   - Include cultural sensitivity where relevant
   - Focus on value creation and ROI

5. Tools available for this agent: {json.dumps(tools)}
   Color for this agent: {color}

IMPORTANT: 
- Make the agent feel like a real expert in their field
- Include industry-specific terminology and methodologies
- Ensure all content is relevant to the actual job description
- Create unique, valuable content - don't just copy the reference

Please generate the COMPLETE agent definition file content, including the YAML frontmatter.
Start with the YAML frontmatter (---) and end with the complete agent description.
"""

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at creating professional AI agent personalities for enterprise software."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            generated_content = response.choices[0].message.content
            
            # Extract the agent name from the generated content
            name_match = re.search(r'^name:\s*(.+)$', generated_content, re.MULTILINE)
            if not name_match:
                logger.error("Could not extract agent name from AI response")
                return None
            
            agent_name = name_match.group(1).strip()
            
            # Ensure name is unique
            if agent_name in self.generated_names:
                # Add a number suffix to make it unique
                base_name = agent_name
                counter = 2
                while f"{base_name}-{counter}" in self.generated_names:
                    counter += 1
                agent_name = f"{base_name}-{counter}"
                # Update the name in the content
                generated_content = re.sub(
                    r'^name:\s*.+$', 
                    f'name: {agent_name}', 
                    generated_content, 
                    count=1, 
                    flags=re.MULTILINE
                )
            
            self.generated_names.add(agent_name)
            
            logger.info(f"  ✅ Generated agent: {agent_name}")
            
            return {
                'name': agent_name,
                'content': generated_content,
                'profession': metadata.get('profession'),
                'discipline': metadata.get('discipline')
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    def _select_tools(self, profession: str) -> List[str]:
        """Select appropriate tools based on profession."""
        profession_lower = profession.lower() if profession else ''
        
        # Map to tool set based on keywords
        if any(word in profession_lower for word in ['engineering', 'developer', 'software', 'technical']):
            return self.TOOL_SETS['technical']
        elif any(word in profession_lower for word in ['finance', 'accounting', 'treasury', 'tax']):
            return self.TOOL_SETS['finance']
        elif any(word in profession_lower for word in ['manager', 'director', 'lead', 'head']):
            return self.TOOL_SETS['management']
        elif 'sales' in profession_lower:
            return self.TOOL_SETS['sales']
        elif any(word in profession_lower for word in ['hr', 'human', 'people', 'talent']):
            return self.TOOL_SETS['hr']
        elif 'marketing' in profession_lower:
            return self.TOOL_SETS['marketing']
        elif 'operations' in profession_lower:
            return self.TOOL_SETS['operations']
        elif 'strategy' in profession_lower:
            return self.TOOL_SETS['strategy']
        else:
            return self.TOOL_SETS['default']
    
    def _save_agent(self, agent_name: str, content: str) -> str:
        """Save agent to .md file."""
        output_file = self.output_dir / f"{agent_name}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"  💾 Saved: {output_file.name}")
        return output_file.name
    
    def generate_all_agents(self, limit: Optional[int] = None) -> Dict:
        """Generate agents for all senior job descriptions."""
        results = {
            'processed': 0,
            'agents_created': 0,
            'agents': [],
            'summary_by_level': {},
            'errors': []
        }
        
        # Get all senior job description files
        job_files = list(self.input_dir.glob("*.md"))
        
        # Apply limit if specified
        if limit:
            job_files = job_files[:limit]
        
        logger.info(f"\n{'='*60}")
        logger.info("🚀 AI AGENT GENERATION STARTING")
        logger.info(f"{'='*60}")
        logger.info(f"📁 Source: {self.input_dir}")
        logger.info(f"📁 Output: {self.output_dir}")
        logger.info(f"📊 Files to process: {len(job_files)}")
        logger.info(f"{'='*60}\n")
        
        for i, job_file in enumerate(job_files, 1):
            logger.info(f"[{i}/{len(job_files)}] Processing {job_file.name}")
            
            agent_result = self.generate_agent_from_job(job_file)
            results['processed'] += 1
            
            if agent_result:
                results['agents_created'] += 1
                results['agents'].append(agent_result)
                
                # Track by level
                level = agent_result.get('level', 'Unknown')
                if level not in results['summary_by_level']:
                    results['summary_by_level'][level] = []
                results['summary_by_level'][level].append(agent_result['agent_name'])
            else:
                results['errors'].append(job_file.name)
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _save_results(self, results: Dict):
        """Save generation results and print summary."""
        results_file = self.output_dir / "ai_generation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 AI AGENT GENERATION COMPLETE")
        print("="*60)
        print("📊 Statistics:")
        print(f"  • Job descriptions processed: {results['processed']}")
        print(f"  • Agents successfully created: {results['agents_created']}")
        print(f"  • Generation success rate: {results['agents_created']/results['processed']*100:.1f}%")
        
        if results['summary_by_level']:
            print("\n📈 Breakdown by level:")
            for level, agents in sorted(results['summary_by_level'].items()):
                print(f"  • {level}: {len(agents)} agents")
                for agent in agents[:3]:  # Show first 3 agents
                    print(f"    - {agent}")
                if len(agents) > 3:
                    print(f"    ... and {len(agents)-3} more")
        
        if results['errors']:
            print(f"\n⚠️  Failed to process {len(results['errors'])} files:")
            for error_file in results['errors'][:5]:
                print(f"  • {error_file}")
            if len(results['errors']) > 5:
                print(f"  ... and {len(results['errors'])-5} more")
        
        print(f"\n📁 Output directory: {self.output_dir}")
        print(f"📄 Results saved to: {results_file.name}")
        print("="*60)


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate Convergio agents from senior job descriptions using AI'
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        help='Limit number of agents to generate (for testing)'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Input directory with senior job descriptions'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for generated agents'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    base_dir = Path(__file__).resolve().parents[3]  # convergio root
    input_dir = Path(args.input_dir) if args.input_dir else base_dir / "jobDescriptions" / "senior"
    output_dir = Path(args.output_dir) if args.output_dir else base_dir / "backend" / "src" / "agents" / "definitions" / "newJobs"
    
    # Validate paths
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1
    
    # Create generator and process
    try:
        generator = AIAgentGenerator(input_dir, output_dir)
        results = generator.generate_all_agents(limit=args.limit)
        return 0 if results['agents_created'] > 0 else 1
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())