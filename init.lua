-- Main entry point for the plugin
local M = {}

-- Import modules
local config = require("ai-memory.config")
local response = require("ai-memory.response")
local debug = require("ai-memory.debug")

-- Setup function that initializes the plugin
M.setup = function(opts)
  -- Initialize configuration
  config.setup(opts)

  -- Create autocommand group
  local augroup = vim.api.nvim_create_augroup("AiMemory", { clear = true })

  -- Set up keybinding when opening matching files
  vim.api.nvim_create_autocmd("BufRead", {
    group = augroup,
    pattern = config.get("file_pattern"),
    callback = function()
      vim.keymap.set(
        "n",
        config.get("keybinding"),
        response.generate_response,
        { buffer = true, desc = "Generate AI response" }
      )
    end,
  })
end

-- Expose debug functionality
M.debug_parse_history = debug.parse_history

return M
