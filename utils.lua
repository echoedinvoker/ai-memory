-- Utility functions for AI Memory plugin
local M = {}

-- Decode function: replace <NEWLINE> markers with actual newlines
M.decode_chunk = function(encoded_text)
  return encoded_text:gsub("<NEWLINE>", "\n")
end

-- Find the position of the last occurrence of a pattern in text
M.find_last_pattern = function(text, pattern)
  local positions = {}
  local start_pos = 1
  
  while true do
    local pos = text:find(pattern, start_pos)
    if not pos then break end
    table.insert(positions, pos)
    start_pos = pos + 1
  end
  
  return positions[#positions]
end

-- Reload the current buffer while preserving cursor position
M.reload_buffer = function()
  local cursor = vim.api.nvim_win_get_cursor(0)
  vim.cmd("edit!")
  vim.schedule(function()
    local new_line_count = vim.api.nvim_buf_line_count(0)
    vim.api.nvim_win_set_cursor(0, { math.min(cursor[1], new_line_count), cursor[2] })
  end)
end

-- Move cursor to the end of the buffer
M.move_cursor_to_end = function()
  vim.schedule(function()
    local line_count = vim.api.nvim_buf_line_count(0)
    vim.api.nvim_win_set_cursor(0, { line_count, 0 })
  end)
end

-- Move cursor to the line after the last "Human:" marker
M.move_cursor_after_human = function()
  vim.schedule(function()
    local line_count = vim.api.nvim_buf_line_count(0)
    for i = line_count, 1, -1 do
      local line = vim.api.nvim_buf_get_lines(0, i - 1, i, false)[1]
      if line == "Human:" then
        vim.api.nvim_win_set_cursor(0, { i + 1, 0 })
        break
      end
    end
  end)
end

return M
