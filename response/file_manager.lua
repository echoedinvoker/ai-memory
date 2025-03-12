-- File content management for AI responses
local M = {}

local utils = require("ai-memory.utils")

-- Prepare file for AI response by adding AI: section if needed
M.prepare_ai_section = function(file_path)
  -- Get current file content
  local lines = vim.fn.readfile(file_path)
  local content = table.concat(lines, "\n")

  -- Check if the file already has the latest AI: marker
  local human_pattern = "(Human:|H:)[^\n]*\n"
  local last_human_pos = content:find(human_pattern .. "[^\n]*$")

  if last_human_pos then
    -- Found the last Human: section
    if not content:sub(last_human_pos):match("\n\nAI:") then
      -- If no AI: marker exists after the last Human: section, add one
      local new_content = content .. "\n\nAI:\n"
      vim.fn.writefile(vim.split(new_content, "\n"), file_path)
    end
  else
    -- If no Human: section found, append directly
    local new_content = content .. "\n\nAI:\n"
    vim.fn.writefile(vim.split(new_content, "\n"), file_path)
  end

  -- Reload the file
  vim.cmd("edit!")
end

-- Add Human: section for next conversation
M.add_human_section = function(file_path)
  -- Get current file content
  local lines = vim.fn.readfile(file_path)
  local content = table.concat(lines, "\n")

  -- Add new Human: section
  local new_content = content .. "\n\nHuman:\n"
  vim.fn.writefile(vim.split(new_content, "\n"), file_path)

  -- Reload file
  vim.cmd("edit!")

  -- Move cursor to after the new Human: marker
  utils.move_cursor_after_human()
end

-- Update file with AI response content
M.update_ai_response = function(file_path, response_text)
  -- Get current file content
  local lines = vim.fn.readfile(file_path)
  local content = table.concat(lines, "\n")

  -- Find the last AI: section
  local ai_sections = {}
  local ai_pattern = "(AI:)"
  local start_pos = 1

  -- Find all AI: marker positions
  while true do
    local ai_pos = content:find(ai_pattern, start_pos)
    if not ai_pos then
      break
    end
    table.insert(ai_sections, ai_pos)
    start_pos = ai_pos + 1
  end

  -- Use the position of the last AI: marker
  local last_ai_pos = ai_sections[#ai_sections]

  if last_ai_pos then
    -- Update content after the last AI: marker, preserving newlines
    local before_ai = content:sub(1, last_ai_pos + 2) -- +2 for "AI:"

    -- Convert response text to line array, preserving newlines
    local response_lines = vim.split(response_text, "\n", true)

    -- Build new content
    local new_content_lines = vim.split(before_ai, "\n")

    -- Add response lines
    for _, resp_line in ipairs(response_lines) do
      table.insert(new_content_lines, resp_line)
    end

    -- Write to file
    vim.fn.writefile(new_content_lines, file_path)
  else
    -- If no AI: section found, add one
    local new_content = content .. "\n\nAI:\n" .. response_text
    vim.fn.writefile(vim.split(new_content, "\n", true), file_path)
  end

  -- Reload file
  vim.cmd("edit!")
end

return M
