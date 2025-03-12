-- Main entry point for AI response functionality
local M = {}

-- local config = require("ai-memory.config")
local python = require("ai-memory.response.python")
local stream = require("ai-memory.response.stream")
local ui = require("ai-memory.ui")

-- Generate AI response and write directly to file
M.generate_response = function()
    local file_path = vim.fn.expand("%:p")

    -- Save the file
    vim.cmd("write!")

    -- Show status message
    ui.status("Generating AI response...", "WarningMsg")

    -- Reset stream state
    stream.reset_state()

    -- Ensure Poetry environment is set up
    if not python.ensure_poetry_env() then
        return
    end

    -- Run Python script to generate response
    python.run_script(file_path, stream.handle_message)
end

-- Initialize Poetry environment when the module is loaded
M.init = function()
    -- Ensure Poetry environment on plugin load
    vim.defer_fn(function()
        python.ensure_poetry_env()
    end, 100)
end

return M
