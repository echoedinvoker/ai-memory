-- AI response generation logic
local M = {}

local config = require("ai-memory.config")
local utils = require("ai-memory.utils")
local ui = require("ai-memory.ui")

-- State variables for streaming
local is_streaming = false
local ai_section_added = false
local response_text = ""

-- Get the plugin directory path
local function get_plugin_dir()
    local source = debug.getinfo(1, "S").source
    local file_path = source:sub(2)  -- Remove the '@' prefix
    return vim.fn.fnamemodify(file_path, ":h")  -- Get directory
end

-- Handle different types of messages from the Python script
local function handle_message(line, file_path)
    -- 原有的 handle_message 函數內容保持不變
    if line == "START_STREAM" then
        -- Start streaming, prepare to receive content
        is_streaming = true
        response_text = ""

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
                ai_section_added = true
            else
                -- AI: marker already exists
                ai_section_added = true
            end
        else
            -- If no Human: section found, append directly
            local new_content = content .. "\n\nAI:\n"
            vim.fn.writefile(vim.split(new_content, "\n"), file_path)
            ai_section_added = true
        end

        -- Reload the file
        vim.cmd("edit!")
    elseif line == "END_STREAM" then
        -- Stream ended, add Human: marker for the next conversation
        is_streaming = false

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

        -- Show success message
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
                -- Get current file content
                local lines = vim.fn.readfile(file_path)
                local content = table.concat(lines, "\n")

                -- Add AI: section
                local new_content = content .. "\n\nAI:\n"
                vim.fn.writefile(vim.split(new_content, "\n"), file_path)
                ai_section_added = true

                -- Reload file
                vim.cmd("edit!")
            end

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

            -- Reload file but keep cursor position
            local cursor = vim.api.nvim_win_get_cursor(0)
            vim.cmd("edit!")

            -- Try to restore cursor position to end of file
            utils.move_cursor_to_end()
        end
    elseif line:sub(1, 12) == "AI_RESPONSE:" then
        -- Process complete AI response
        -- We already handle this in streaming, so no additional action needed
    end
end

-- Generate AI response and write directly to file
M.generate_response = function()
    local file_path = vim.fn.expand("%:p")

    -- Save the file
    vim.cmd("write!")

    -- Show status message
    ui.status("Generating AI response...", "WarningMsg")

    -- Reset state variables
    is_streaming = false
    ai_section_added = false
    response_text = ""

    -- Get plugin directory
    local plugin_dir = get_plugin_dir()
    
    -- Build Poetry command to run the Python script
    local python_script = config.get("python_path")
    -- local cmd = "cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry run python " .. python_script .. " " .. vim.fn.shellescape(file_path)
    local cmd = "cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry run python -m python.ai_memory " .. vim.fn.shellescape(file_path)

    local job_id = vim.fn.jobstart(cmd, {
        on_stdout = function(_, data, _)
            if data then
                for _, line in ipairs(data) do
                    handle_message(line, file_path)
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

-- Initialize Poetry environment when the module is loaded
M.init = function()
    -- Ensure Poetry environment on plugin load
    vim.defer_fn(function()
        M.ensure_poetry_env()
    end, 100)
end

return M
