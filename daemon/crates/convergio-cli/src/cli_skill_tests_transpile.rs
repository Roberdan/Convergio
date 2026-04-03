use super::*;

#[test]
fn transpile_claude_creates_file() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("test-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_valid_skill(&skill_dir);
    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let md = fs::read_to_string(skill_dir.join("SKILL.md")).unwrap();
    let out_dir = tmp.path().join("out");
    fs::create_dir(&out_dir).unwrap();
    let path = crate::cli_skill_transpile::transpile_claude(&yaml, &md, &out_dir).unwrap();
    assert!(path.exists());
    let content = fs::read_to_string(&path).unwrap();
    assert!(content.contains("---\nname: my-skill"));
    assert!(content.contains("<!-- v1.0.0 -->"));
}

#[test]
fn transpile_copilot_creates_agent_md() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("test-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_valid_skill(&skill_dir);
    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let md = fs::read_to_string(skill_dir.join("SKILL.md")).unwrap();
    let out_dir = tmp.path().join("out");
    fs::create_dir(&out_dir).unwrap();
    let path = crate::cli_skill_transpile::transpile_copilot(&yaml, &md, &out_dir).unwrap();
    assert!(path.exists());
    assert!(path.to_string_lossy().ends_with(".agent.md"));
    let content = fs::read_to_string(&path).unwrap();
    assert!(content.contains("# My-skill"));
}

#[test]
fn transpile_generic_creates_system_prompt() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("test-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_valid_skill(&skill_dir);
    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let md = fs::read_to_string(skill_dir.join("SKILL.md")).unwrap();
    let out_dir = tmp.path().join("out");
    fs::create_dir(&out_dir).unwrap();
    let path = crate::cli_skill_transpile::transpile_generic(&yaml, &md, &out_dir).unwrap();
    assert!(path.exists());
    assert!(path.to_string_lossy().ends_with(".system-prompt.txt"));
    let content = fs::read_to_string(&path).unwrap();
    assert!(content.contains("You are my-skill"));
    assert!(content.contains("## Instructions"));
}
