const { execSync } = require("node:child_process");

function getPlanTasks(planId) {
  const dbPath = `${process.env.HOME}/.claude/data/dashboard.db`;
  const sql = `SELECT id, task_id, IFNULL(model, ''), IFNULL(executor_agent, ''), IFNULL(effort_level, 0) FROM tasks WHERE plan_id = ${Number(planId)} ORDER BY id;`;
  const output = execSync(`sqlite3 -tabs "${dbPath}" "${sql}"`, { encoding: "utf8" });
  return output
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      const [id, taskId, model, executorAgent, effortLevel] = line.split("\t");
      return { id: Number(id), taskId, model, executorAgent, effortLevel: Number(effortLevel) };
    });
}

describe("plan task routing", () => {
  test("plan 193 tasks are model-assigned and routed to copilot with valid effort", () => {
    const tasks = getPlanTasks(193);
    const missingModel = tasks.filter((task) => !task.model);
    const nonCopilotTasks = tasks.filter((task) => task.executorAgent !== "copilot");
    const invalidEffort = tasks.filter((task) => ![1, 2, 3].includes(task.effortLevel));

    expect(missingModel).toEqual([]);
    expect(nonCopilotTasks).toEqual([]);
    expect(invalidEffort).toEqual([]);
  });
});
