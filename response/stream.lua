-- AI response streaming logic
local M = {}

local ui = require("ai-memory.ui")
local utils = require("ai-memory.utils")
local file_manager = require("ai-memory.response.file_manager")

-- State variables for streaming
local is_streaming = false
local ai_section_added = false
local response_text = ""

-- Reset streaming state
M.reset_state = function()
  is_streaming = false
  ai_section_added = false
  response_text = ""
end

-- Handle different types of messages from the Python script
M.handle_message = function(line, file_path)
  if line == "START_STREAM" then
    -- Start streaming, prepare to receive content
    is_streaming = true
    response_text = ""
    file_manager.prepare_ai_section(file_path)
    ai_section_added = true
  elseif line == "END_STREAM" then
    -- Stream ended, add Human: marker for the next conversation
    is_streaming = false
    file_manager.add_human_section(file_path)
    ui.notify("AI response generation completed", vim.log.levels.INFO)
  elseif line == "INIT_FILE" then
    ui.notify("New history file created", vim.log.levels.INFO)
    vim.cmd("edit!")
  elseif line == "NO_HUMAN_MESSAGE" then
    ui.notify("No human message to respond to. Please add a message to the file.", vim.log.levels.WARN)
  elseif line == "FILE_UPDATED" then
    vim.cmd("edit!")
    utils.move_cursor_after_human()
    ui.notify("File content updated with summarized question", vim.log.levels.INFO)
  elseif line:sub(1, 6) == "CHUNK:" then
    -- Process chunk content
    if is_streaming then
      -- Get chunk content and decode
      local encoded_chunk = line:sub(7)
      local chunk_content = utils.decode_chunk(encoded_chunk)

      -- Accumulate response text
      response_text = response_text .. chunk_content

      -- Ensure AI: section has been added
      if not ai_section_added then
        file_manager.prepare_ai_section(file_path)
        ai_section_added = true
      end

      -- Update file with new content
      file_manager.update_ai_response(file_path, response_text)

      -- Move cursor to end of file
      utils.move_cursor_to_end()
    end
  elseif line:sub(1, 12) == "AI_RESPONSE:" then
    -- Process complete AI response
    -- We already handle this in streaming, so no additional action needed
  end
end

return M
