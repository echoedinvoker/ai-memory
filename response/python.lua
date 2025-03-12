-- Python script execution and Poetry environment management
local M = {}

local config = require("ai-memory.config")
local ui = require("ai-memory.ui")

-- Get the plugin directory path
local function get_plugin_dir()
  local source = debug.getinfo(1, "S").source
  local file_path = source:sub(2)               -- Remove the '@' prefix
  return vim.fn.fnamemodify(file_path, ":h:h:h") -- Get directory (go up 3 levels)
end

-- Run Python script to generate AI response
M.run_script = function(file_path, message_handler)
  -- Get plugin directory
  local plugin_dir = get_plugin_dir()

  -- Build Poetry command to run the Python script
  local python_script = config.get("python_path")
  local cmd = "cd "
      .. vim.fn.shellescape(plugin_dir)
      .. " && poetry run python -m python.ai_memory "
      .. vim.fn.shellescape(file_path)

  local job_id = vim.fn.jobstart(cmd, {
    on_stdout = function(_, data, _)
      if data then
        for _, line in ipairs(data) do
          message_handler(line, file_path)
        end
      end
    end,
    on_stderr = function(_, data, _)
      if data and #data > 1 then
        ui.notify("Error: " .. vim.inspect(data), vim.log.levels.ERROR)
      end
    end,
    on_exit = function(_, exit_code, _)
      if exit_code ~= 0 then
        ui.notify("Processing failed, exit code: " .. exit_code, vim.log.levels.ERROR)
      end
    end,
    stdout_buffered = false,
  })

  if job_id <= 0 then
    ui.notify("Failed to start Python process", vim.log.levels.ERROR)
  end
end

-- Function to ensure Poetry environment is set up
M.ensure_poetry_env = function()
  local plugin_dir = get_plugin_dir()

  -- Check if Poetry is installed
  local poetry_check = vim.fn.system("which poetry")
  if vim.v.shell_error ~= 0 then
    ui.notify("Poetry not found. Please install Poetry first.", vim.log.levels.ERROR)
    return false
  end

  -- Check if Poetry environment exists
  local poetry_env_check = vim.fn.system("cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry env info")
  if vim.v.shell_error ~= 0 then
    ui.notify("Setting up Poetry environment...", vim.log.levels.INFO)

    -- Initialize Poetry project if pyproject.toml doesn't exist
    if vim.fn.filereadable(plugin_dir .. "/pyproject.toml") == 0 then
      local init_cmd = "cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry init --no-interaction"
      vim.fn.system(init_cmd)

      if vim.v.shell_error ~= 0 then
        ui.notify("Failed to initialize Poetry project", vim.log.levels.ERROR)
        return false
      end
    end

    -- Install dependencies
    local install_cmd = "cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry install"
    vim.fn.system(install_cmd)

    if vim.v.shell_error ~= 0 then
      ui.notify("Failed to install Poetry dependencies", vim.log.levels.ERROR)
      return false
    end

    ui.notify("Poetry environment set up successfully", vim.log.levels.INFO)
  end

  return true
end

return M
