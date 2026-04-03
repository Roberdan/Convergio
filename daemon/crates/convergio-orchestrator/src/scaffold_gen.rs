// Language-specific file generators for project scaffolding.

use crate::scaffold::{License, ScaffoldFile};
use crate::scaffold_templates as tpl;

pub struct Vars<'a> {
    pub name: &'a str,
    pub description: &'a str,
    pub license_spdx: &'a str,
    pub year: &'a str,
    pub author: &'a str,
    pub owner: &'a str,
}

pub fn replace(template: &str, v: &Vars) -> String {
    template
        .replace("{name}", v.name)
        .replace("{description}", v.description)
        .replace("{license_spdx}", v.license_spdx)
        .replace("{year}", v.year)
        .replace("{author}", v.author)
        .replace("{owner}", v.owner)
}

pub fn common_files(v: &Vars, lic: License) -> Vec<ScaffoldFile> {
    let license_text = match lic {
        License::Mit => tpl::LICENSE_MIT,
        License::Apache2 => tpl::LICENSE_APACHE2,
        License::Gpl3 => tpl::LICENSE_GPL3,
    };
    vec![
        ScaffoldFile {
            path: "CLAUDE.md".into(),
            content: replace(tpl::CLAUDE_MD, v),
        },
        ScaffoldFile {
            path: "README.md".into(),
            content: replace(tpl::README_MD, v),
        },
        ScaffoldFile {
            path: "LICENSE".into(),
            content: replace(license_text, v),
        },
        ScaffoldFile {
            path: "CODEOWNERS".into(),
            content: replace(tpl::CODEOWNERS, v),
        },
    ]
}

pub fn append_rust(files: &mut Vec<ScaffoldFile>, v: &Vars) -> String {
    files.push(ScaffoldFile {
        path: "Cargo.toml".into(),
        content: replace(tpl::RUST_CARGO_TOML, v),
    });
    files.push(ScaffoldFile {
        path: "src/main.rs".into(),
        content: replace(tpl::RUST_MAIN_RS, v),
    });
    files.push(ScaffoldFile {
        path: ".gitignore".into(),
        content: tpl::GITIGNORE_RUST.into(),
    });
    files.push(ScaffoldFile {
        path: ".github/workflows/ci.yml".into(),
        content: tpl::RUST_CI_YML.into(),
    });
    tpl::RUST_CI_YML.into()
}

pub fn append_typescript(files: &mut Vec<ScaffoldFile>, v: &Vars) -> String {
    files.push(ScaffoldFile {
        path: "package.json".into(),
        content: replace(tpl::TS_PACKAGE_JSON, v),
    });
    files.push(ScaffoldFile {
        path: "tsconfig.json".into(),
        content: tpl::TS_TSCONFIG.into(),
    });
    files.push(ScaffoldFile {
        path: "src/index.ts".into(),
        content: replace(tpl::TS_INDEX, v),
    });
    files.push(ScaffoldFile {
        path: ".gitignore".into(),
        content: tpl::GITIGNORE_TS.into(),
    });
    files.push(ScaffoldFile {
        path: ".github/workflows/ci.yml".into(),
        content: tpl::TS_CI_YML.into(),
    });
    tpl::TS_CI_YML.into()
}

pub fn append_python(files: &mut Vec<ScaffoldFile>, v: &Vars) -> String {
    files.push(ScaffoldFile {
        path: "pyproject.toml".into(),
        content: replace(tpl::PY_PYPROJECT, v),
    });
    files.push(ScaffoldFile {
        path: "src/__init__.py".into(),
        content: replace(tpl::PY_INIT, v),
    });
    files.push(ScaffoldFile {
        path: ".gitignore".into(),
        content: tpl::GITIGNORE_PYTHON.into(),
    });
    files.push(ScaffoldFile {
        path: ".github/workflows/ci.yml".into(),
        content: tpl::PY_CI_YML.into(),
    });
    tpl::PY_CI_YML.into()
}

pub fn license_spdx(lic: License) -> &'static str {
    match lic {
        License::Mit => "MIT",
        License::Apache2 => "Apache-2.0",
        License::Gpl3 => "GPL-3.0-only",
    }
}
