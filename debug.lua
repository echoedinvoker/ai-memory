-- Debug functionality for AI Memory plugin
local M = {}

local config = require("ai-memory.config")

-- Debug function to parse history file
M.parse_history = function()
  local file_path = vim.fn.expand("%:p")

  -- Save the file
  vim.cmd("write!")

  -- Create temporary Python script
  local temp_script = os.tmpname() .. ".py"
  local script_content = [[
import sys
sys.path.append("]] .. vim.fn.fnamemodify(config.get("python_path"), ":h") .. [[")
from ai_memory import parse_history_file
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

file_path = "]] .. file_path .. [["
messages = parse_history_file(file_path)

print(f"Processing file: {file_path}")
print("Parsed messages:")
for i, msg in enumerate(messages):
    print(f"[{i}] {type(msg).__name__}: {msg.content[:100]}...")
  ]]

  -- Write temporary script
  vim.fn.writefile(vim.split(script_content, "\n"), temp_script)

  -- Execute script in terminal
  vim.cmd("botright split | terminal python3 " .. temp_script)

  -- Set terminal buffer options
  vim.cmd("setlocal nonumber")
  vim.cmd("setlocal signcolumn=no")

  -- Delete temporary script after execution
  vim.defer_fn(function()
    os.remove(temp_script)
  end, 5000)
end

return M
