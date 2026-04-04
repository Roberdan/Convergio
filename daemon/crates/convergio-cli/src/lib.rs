//! convergio-cli — cvg CLI, pure HTTP client.
//!
//! Zero internal imports. Talks to the daemon exclusively via HTTP API.

// Core infrastructure
pub mod cli_error;
pub mod cli_http;
pub mod message_error;
pub mod paths;
pub mod transpiler;

// Command enum + dispatch
pub mod cli_commands;
pub mod dispatch;

// Command modules — each defines subcommand enums + handlers
pub mod cli_agent;
pub mod cli_agent_format;
pub mod cli_agent_history;
mod cli_agents;
pub mod cli_api_list;
pub mod cli_ask;
pub mod cli_audit;
pub mod cli_audit_project;
pub mod cli_bus;
pub mod cli_bus_ask;
pub mod cli_bus_org;
pub mod cli_bus_watch;
pub mod cli_capability;
pub mod cli_channel;
pub mod cli_chat;
pub mod cli_cheatsheet;
pub mod cli_checkpoint;
pub mod cli_cleanup;
pub mod cli_create_org;
pub mod cli_delegation;
pub mod cli_domain;
pub mod cli_kb;
pub mod cli_kernel;
pub mod cli_launch;
pub mod cli_lock;
pub mod cli_memory;
pub mod cli_mesh_join;
pub mod cli_ops;
pub mod cli_org;
pub mod cli_org_show;
pub mod cli_plan;
pub mod cli_plan_handlers;
pub mod cli_plan_show;
pub mod cli_plan_template;
pub mod cli_plan_tree_fmt;
pub mod cli_project;
pub mod cli_project_handlers;
pub mod cli_project_init;
pub mod cli_project_init_templates;
pub mod cli_project_tree;
pub mod cli_reap;
pub mod cli_repo;
pub mod cli_review;
pub mod cli_run;
pub mod cli_setup;
pub mod cli_setup_steps;
pub mod cli_skill;
pub mod cli_skill_disable;
pub mod cli_skill_enable;
pub mod cli_skill_transpile;
pub mod cli_skill_validate;
pub mod cli_skill_validators;
pub mod cli_status;
pub mod cli_task;
pub mod cli_task_approve;
pub mod cli_task_format;
pub mod cli_voice;
pub mod cli_wave;
pub mod cli_wave_handlers;
pub mod cli_who;
pub mod cli_workspace;
