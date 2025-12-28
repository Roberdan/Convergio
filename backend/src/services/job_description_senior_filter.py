#!/usr/bin/env python3
"""
🎯 Senior Level Job Description Filter
=======================================

Extracts only senior-level content from job descriptions and creates
separate files for each senior level with filtered content.

Senior Levels:
- IC6+ (Individual Contributor - highest level)
- M6+ (Manager - highest level)  
- GM, VP, SVP, EVP (Executive levels)
- C-suite (CEO, CTO, CFO, etc.)
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SeniorLevelExtractor:
    """Extracts and filters content for senior-level positions only."""
    
    # Define what constitutes a senior level
    SENIOR_THRESHOLDS = {
        'IC': 6,  # IC6 and above
        'M': 6,   # M6 and above (you can adjust to M5 if needed)
    }
    
    # Executive levels are always senior
    EXECUTIVE_LEVELS = {'GM', 'VP', 'SVP', 'EVP', 'CEO', 'CTO', 'CFO', 'COO', 'CPO', 'CHRO', 'CIO'}
    
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_file(self, file_path: Path) -> List[Dict]:
        """Process a single job description file and extract senior levels."""
        logger.info(f"Processing: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract basic info
        profession = self._extract_field(content, r'\*\*Profession:\*\*\s*(.+)')
        discipline = self._extract_field(content, r'\*\*Discipline:\*\*\s*(.+)')
        discipline_def = self._extract_section(content, 'Discipline Definition')
        
        # Find all levels mentioned in the file
        all_levels = self._find_all_levels(content)
        senior_levels = self._filter_senior_levels(all_levels)
        
        if not senior_levels:
            logger.info(f"  No senior levels found in {file_path.name}")
            return []
        
        logger.info(f"  Found senior levels: {senior_levels}")
        
        # Create separate file for each senior level
        results = []
        for level in senior_levels:
            filtered_content = self._filter_content_for_level(
                content, level, profession, discipline, discipline_def
            )
            
            if filtered_content:
                output_file = self._save_filtered_content(
                    file_path.stem, level, filtered_content
                )
                results.append({
                    'source_file': file_path.name,
                    'level': level,
                    'output_file': output_file,
                    'profession': profession,
                    'discipline': discipline
                })
        
        return results
    
    def _find_all_levels(self, content: str) -> Set[str]:
        """Find all job levels mentioned in the content."""
        levels = set()
        
        # Find IC levels (IC1, IC2, etc.)
        ic_matches = re.findall(r'\bIC(\d+)\b', content)
        for num in ic_matches:
            levels.add(f'IC{num}')
        
        # Find M levels (M1, M2, etc.)
        m_matches = re.findall(r'\bM(\d+)\b', content)
        for num in m_matches:
            levels.add(f'M{num}')
        
        # Find executive levels
        for exec_level in self.EXECUTIVE_LEVELS:
            if re.search(r'\b' + exec_level + r'\b', content, re.IGNORECASE):
                levels.add(exec_level)
        
        return levels
    
    def _filter_senior_levels(self, all_levels: Set[str]) -> List[str]:
        """Filter to keep only senior levels."""
        senior = []
        
        # Check IC levels
        ic_levels = [level for level in all_levels if level.startswith('IC')]
        if ic_levels:
            # Get the highest IC level(s) that meet threshold
            ic_nums = [(level, int(level[2:])) for level in ic_levels]
            max_ic = max(ic_nums, key=lambda x: x[1])[1]
            if max_ic >= self.SENIOR_THRESHOLDS['IC']:
                # Add only the highest IC level
                senior.append(f'IC{max_ic}')
        
        # Check M levels
        m_levels = [level for level in all_levels if level.startswith('M') and level[1:].isdigit()]
        if m_levels:
            # Get the highest M level(s) that meet threshold
            m_nums = [(level, int(level[1:])) for level in m_levels]
            max_m = max(m_nums, key=lambda x: x[1])[1]
            if max_m >= self.SENIOR_THRESHOLDS['M']:
                # Add only the highest M level
                senior.append(f'M{max_m}')
        
        # Add executive levels
        for exec_level in all_levels:
            if exec_level in self.EXECUTIVE_LEVELS:
                senior.append(exec_level)
        
        return sorted(senior)
    
    def _filter_content_for_level(self, content: str, level: str, 
                                  profession: str, discipline: str, 
                                  discipline_def: str) -> str:
        """Extract only content relevant to a specific level."""
        
        filtered_parts = []
        
        # Add header
        filtered_parts.append(f"# Career Stage Profile - {level} Only")
        filtered_parts.append("")
        filtered_parts.append(f"## **Profession:** {profession}")
        filtered_parts.append("")
        filtered_parts.append(f"## **Discipline:** {discipline}")
        filtered_parts.append("")
        filtered_parts.append("### **Discipline Definition**")
        filtered_parts.append("")
        filtered_parts.append(discipline_def)
        filtered_parts.append("")
        
        # Extract role summary for this level
        role_summary = self._extract_role_summary(content, level)
        if role_summary:
            filtered_parts.append("### **Role Summary**")
            filtered_parts.append("")
            filtered_parts.append(role_summary)
            filtered_parts.append("")
        
        # Extract responsibilities for this level
        if level.startswith('IC'):
            responsibilities = self._extract_ic_responsibilities(content, level)
            if responsibilities:
                filtered_parts.append("### **Key Responsibilities**")
                filtered_parts.append("")
                filtered_parts.append(responsibilities)
                filtered_parts.append("")
        elif level.startswith('M'):
            responsibilities = self._extract_manager_responsibilities(content, level)
            if responsibilities:
                filtered_parts.append("### **Key Responsibilities**")
                filtered_parts.append("")
                filtered_parts.append(responsibilities)
                filtered_parts.append("")
        
        # Extract skills for this level
        skills = self._extract_skills_for_level(content, level)
        if skills:
            filtered_parts.append("### **Skills & Capabilities**")
            filtered_parts.append("")
            filtered_parts.append(skills)
            filtered_parts.append("")
        
        return "\n".join(filtered_parts)
    
    def _extract_field(self, content: str, pattern: str) -> str:
        """Extract a simple field value."""
        match = re.search(pattern, content)
        return match.group(1).strip() if match else "Unknown"
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section of content."""
        pattern = rf'### \*\*{section_name}\*\*\s*\n+(.*?)(?=\n###|\n\n\||$)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_role_summary(self, content: str, level: str) -> str:
        """Extract the role summary for a specific level."""
        # Look for role summaries table
        pattern = r'\| \*\*Role\*\* \| \*\*Role Summary\*\* \|(.*?)(?=\n\n###|\n\n\||$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            table_content = match.group(0)
            # Find the row for this specific level
            level_pattern = rf'\| \*\*.*?{re.escape(level)}.*?\*\* \| (.*?) \|'
            level_match = re.search(level_pattern, table_content)
            if level_match:
                return level_match.group(1).strip()
        
        return ""
    
    def _extract_ic_responsibilities(self, content: str, level: str) -> str:
        """Extract IC responsibilities for a specific level."""
        # Find the IC responsibilities table
        pattern = r'### \*\*Key Responsibilities \(Individual Contributor\)\*\*.*?\n(.*?)(?=\n###|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return ""
        
        table_content = match.group(1)
        
        # Parse the table to extract only the column for this level
        lines = table_content.split('\n')
        header_line = None
        level_column = -1
        
        # Find header and identify column for this level
        for i, line in enumerate(lines):
            if level in line and '|' in line:
                # This might be the header
                cells = [cell.strip() for cell in line.split('|')]
                for j, cell in enumerate(cells):
                    if level in cell:
                        level_column = j
                        header_line = i
                        break
                if level_column >= 0:
                    break
        
        if level_column < 0:
            return ""
        
        # Extract content from the level's column
        responsibilities = []
        current_topic = ""
        
        for line in lines[header_line + 2:]:  # Skip header and separator
            if not line.strip() or line.strip() == '|':
                continue
            
            cells = line.split('|')
            if len(cells) > level_column:
                # First cell is usually the topic area
                if len(cells) > 1 and cells[1].strip() and '**' in cells[1]:
                    current_topic = cells[1].strip()
                
                # Get the content for this level
                if level_column < len(cells):
                    content = cells[level_column].strip()
                    if content and content != '-':
                        if current_topic and current_topic not in str(responsibilities):
                            responsibilities.append(f"\n**{current_topic}**\n")
                        responsibilities.append(content)
        
        return "\n".join(responsibilities) if responsibilities else ""
    
    def _extract_manager_responsibilities(self, content: str, level: str) -> str:
        """Extract Manager responsibilities for a specific level."""
        # Find the Manager responsibilities table
        pattern = r'### \*\*Key Responsibilities \(Manager\)\*\*.*?\n(.*?)(?=\n###|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return ""
        
        table_content = match.group(1)
        
        # Parse the table similar to IC responsibilities
        lines = table_content.split('\n')
        header_line = None
        level_column = -1
        
        # Find header and identify column for this level
        for i, line in enumerate(lines):
            if level in line and '|' in line:
                cells = [cell.strip() for cell in line.split('|')]
                for j, cell in enumerate(cells):
                    if level in cell:
                        level_column = j
                        header_line = i
                        break
                if level_column >= 0:
                    break
        
        if level_column < 0:
            return ""
        
        # Extract content from the level's column
        responsibilities = []
        current_topic = ""
        
        for line in lines[header_line + 2:]:  # Skip header and separator
            if not line.strip() or line.strip() == '|':
                continue
            
            cells = line.split('|')
            if len(cells) > level_column:
                # First cell is usually the topic area
                if len(cells) > 1 and cells[1].strip() and '**' in cells[1]:
                    current_topic = cells[1].strip()
                
                # Get the content for this level
                if level_column < len(cells):
                    content = cells[level_column].strip()
                    if content and content != '-':
                        if current_topic and current_topic not in str(responsibilities):
                            responsibilities.append(f"\n**{current_topic}**\n")
                        responsibilities.append(content)
        
        return "\n".join(responsibilities) if responsibilities else ""
    
    def _extract_skills_for_level(self, content: str, level: str) -> str:
        """Extract skills relevant to a specific level."""
        # Find skills section
        pattern = r'### \*\*Skills & Capabilities\*\*.*?\n(.*?)(?=\n##|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return ""
        
        skills_content = match.group(1)
        
        # Look for a table with level-specific skills
        if '|' in skills_content and level in skills_content:
            # Parse table to find level column
            lines = skills_content.split('\n')
            level_column = -1
            
            for line in lines:
                if level in line and '|' in line:
                    cells = [cell.strip() for cell in line.split('|')]
                    for j, cell in enumerate(cells):
                        if level in cell:
                            level_column = j
                            break
                    break
            
            if level_column >= 0:
                skills = []
                for line in lines:
                    if '|' in line and '---' not in line:
                        cells = line.split('|')
                        if len(cells) > level_column:
                            # Check if this level requires the skill (usually marked with 1 or 2)
                            skill_level = cells[level_column].strip()
                            if skill_level in ['1', '2']:
                                # Get skill name from earlier columns
                                if len(cells) > 3:
                                    skill_name = cells[3].strip()  # Usually skill name column
                                    if skill_name and '**' in skill_name:
                                        skills.append(f"- {skill_name} (Priority: {skill_level})")
                
                if skills:
                    return "\n".join(skills[:15])  # Limit to top 15 skills
        
        # If no table or level-specific content, return a note
        return "Skills specific to this level - see full job description for details"
    
    def _save_filtered_content(self, base_name: str, level: str, content: str) -> str:
        """Save the filtered content to a file."""
        # Create filename with level suffix
        output_filename = f"{base_name}_{level}.md"
        output_path = self.output_dir / output_filename
        
        # Add metadata header
        header = f"""---
Generated: {datetime.now().isoformat()}
Source: {base_name}.md
Level: {level}
Type: Senior Position
---

"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header + content)
        
        logger.info(f"  Saved: {output_filename}")
        return output_filename
    
    def process_all_files(self) -> Dict:
        """Process all job description files."""
        results = {
            'processed': 0,
            'senior_files_created': 0,
            'files': [],
            'summary_by_level': {}
        }
        
        md_files = list(self.input_dir.glob("*.md"))
        logger.info(f"\nProcessing {len(md_files)} job description files...")
        logger.info("="*60)
        
        for file_path in md_files:
            file_results = self.process_file(file_path)
            results['processed'] += 1
            
            for result in file_results:
                results['senior_files_created'] += 1
                results['files'].append(result)
                
                # Track summary by level
                level = result['level']
                if level not in results['summary_by_level']:
                    results['summary_by_level'][level] = []
                results['summary_by_level'][level].append(result['source_file'])
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _save_results(self, results: Dict):
        """Save processing results."""
        results_file = self.output_dir / "extraction_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SENIOR LEVEL EXTRACTION COMPLETE")
        print("="*60)
        print(f"Files processed: {results['processed']}")
        print(f"Senior position files created: {results['senior_files_created']}")
        print("\nBreakdown by level:")
        for level, files in sorted(results['summary_by_level'].items()):
            print(f"  {level}: {len(files)} files")
        print(f"\nOutput directory: {self.output_dir}")
        print("="*60)


def main():
    """Main execution function."""
    # Setup paths
    base_dir = Path(__file__).resolve().parents[3]  # convergio root
    input_dir = base_dir / "jobDescriptions" / "md"
    output_dir = base_dir / "jobDescriptions" / "senior"
    
    # Create extractor and process
    extractor = SeniorLevelExtractor(input_dir, output_dir)
    results = extractor.process_all_files()
    
    return 0 if results['senior_files_created'] > 0 else 1


if __name__ == "__main__":
    exit(main())