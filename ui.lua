-- UI-related functions for AI Memory plugin
local M = {}

-- Show a notification message
M.notify = function(message, level)
  vim.notify(message, level or vim.log.levels.INFO)
end

-- Show a status message in the command line
M.status = function(message, highlight)
  vim.api.nvim_echo({ { message, highlight or "Normal" } }, false, {})
end

return M
