-- Configuration management for AI Memory plugin
local M = {}

-- Default configuration
local default_config = {
  file_pattern = "*.md",
  python_path = vim.fn.stdpath("config") .. "/lua/ai-memory/python/ai_memory.py",
  keybinding = "<leader>ai",
}

-- Current configuration
M.config = {}

-- Initialize configuration with user options
M.setup = function(opts)
  opts = opts or {}
  M.config = vim.tbl_deep_extend("force", default_config, opts)
end

-- Get configuration value
M.get = function(key)
  return M.config[key]
end

return M
