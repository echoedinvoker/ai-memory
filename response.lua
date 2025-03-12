-- AI 回應生成邏輯模組
local M = {}

-- 引入依賴模組
local config = require("ai-memory.config")
local utils = require("ai-memory.utils")
local ui = require("ai-memory.ui")

-- 串流狀態管理
local state = {
  is_streaming = false,
  ai_section_added = false,
  response_text = "",
}

-- 重置狀態
local function reset_state()
  state.is_streaming = false
  state.ai_section_added = false
  state.response_text = ""
end

-- 獲取插件目錄路徑
local function get_plugin_dir()
  local source = debug.getinfo(1, "S").source
  local file_path = source:sub(2)           -- 移除 '@' 前綴
  return vim.fn.fnamemodify(file_path, ":h") -- 獲取目錄
end

-- 讀取文件內容
local function read_file(file_path)
  local lines = vim.fn.readfile(file_path)
  return table.concat(lines, "\n")
end

-- 寫入文件內容
local function write_file(file_path, content)
  vim.fn.writefile(vim.split(content, "\n", true), file_path)
end

-- 重新加載文件並保持游標位置
local function reload_file()
  vim.cmd("edit!")
end

-- 添加 AI 標記到文件
local function add_ai_marker(file_path)
  local content = read_file(file_path)

  -- 檢查文件是否已有最新的 AI: 標記
  local human_pattern = "(Human:|H:)[^\n]*\n"
  local last_human_pos = content:find(human_pattern .. "[^\n]*$")

  if last_human_pos then
    -- 找到最後一個 Human: 部分
    if not content:sub(last_human_pos):match("\n\nAI:") then
      -- 如果最後一個 Human: 部分後沒有 AI: 標記，添加一個
      local new_content = content .. "\n\nAI:\n"
      write_file(file_path, new_content)
      state.ai_section_added = true
    else
      -- AI: 標記已存在
      state.ai_section_added = true
    end
  else
    -- 如果沒有找到 Human: 部分，直接附加
    local new_content = content .. "\n\nAI:\n"
    write_file(file_path, new_content)
    state.ai_section_added = true
  end

  reload_file()
end

-- 添加 Human 標記到文件
local function add_human_marker(file_path)
  local content = read_file(file_path)
  local new_content = content .. "\n\nHuman:\n"
  write_file(file_path, new_content)
  reload_file()

  -- 移動游標到新的 Human: 標記之後
  utils.move_cursor_after_human()
end

-- 更新 AI 回應內容
local function update_ai_response(file_path, response_text)
  local content = read_file(file_path)

  -- 找到最後一個 AI: 部分
  local ai_sections = {}
  local ai_pattern = "(AI:)"
  local start_pos = 1

  -- 找到所有 AI: 標記位置
  while true do
    local ai_pos = content:find(ai_pattern, start_pos)
    if not ai_pos then
      break
    end
    table.insert(ai_sections, ai_pos)
    start_pos = ai_pos + 1
  end

  -- 使用最後一個 AI: 標記的位置
  local last_ai_pos = ai_sections[#ai_sections]

  if last_ai_pos then
    -- 更新最後一個 AI: 標記後的內容，保留換行符
    local before_ai = content:sub(1, last_ai_pos + 2) -- +2 表示 "AI:"

    -- 將回應文本轉換為行數組，保留換行符
    local response_lines = vim.split(response_text, "\n", true)

    -- 構建新內容
    local new_content_lines = vim.split(before_ai, "\n")

    -- 添加回應行
    for _, resp_line in ipairs(response_lines) do
      table.insert(new_content_lines, resp_line)
    end

    -- 寫入文件
    vim.fn.writefile(new_content_lines, file_path)
  else
    -- 如果沒有找到 AI: 部分，添加一個
    local new_content = content .. "\n\nAI:\n" .. response_text
    write_file(file_path, new_content)
  end

  reload_file()

  -- 嘗試將游標位置恢復到文件末尾
  utils.move_cursor_to_end()
end

-- 處理開始串流消息
local function handle_start_stream(file_path)
  state.is_streaming = true
  state.response_text = ""
  add_ai_marker(file_path)
end

-- 處理結束串流消息
local function handle_end_stream(file_path)
  state.is_streaming = false
  add_human_marker(file_path)
  ui.notify("AI 回應生成完成", vim.log.levels.INFO)
end

-- 處理串流塊消息
local function handle_chunk(line, file_path)
  if state.is_streaming then
    -- 獲取塊內容並解碼
    local encoded_chunk = line:sub(7)
    local chunk_content = utils.decode_chunk(encoded_chunk)

    -- 累積回應文本
    state.response_text = state.response_text .. chunk_content

    -- 確保 AI: 部分已添加
    if not state.ai_section_added then
      add_ai_marker(file_path)
    end

    -- 更新 AI 回應內容
    update_ai_response(file_path, state.response_text)
  end
end

-- 處理來自 Python 腳本的不同類型消息
local function handle_message(line, file_path)
  if line == "START_STREAM" then
    handle_start_stream(file_path)
  elseif line == "END_STREAM" then
    handle_end_stream(file_path)
  elseif line == "INIT_FILE" then
    ui.notify("新歷史文件已創建", vim.log.levels.INFO)
    reload_file()
  elseif line == "NO_HUMAN_MESSAGE" then
    ui.notify("沒有人類消息可回應。請在文件中添加一條消息。", vim.log.levels.WARN)
  elseif line == "FILE_UPDATED" then
    reload_file()
    utils.move_cursor_after_human()
    ui.notify("文件內容已用摘要問題更新", vim.log.levels.INFO)
  elseif line:sub(1, 6) == "CHUNK:" then
    handle_chunk(line, file_path)
  elseif line:sub(1, 12) == "AI_RESPONSE:" then
    -- 處理完整的 AI 回應
    -- 我們已經在串流中處理了這個，所以不需要額外的操作
  end
end

-- 生成 AI 回應並直接寫入文件
M.generate_response = function()
  local file_path = vim.fn.expand("%:p")

  -- 保存文件
  vim.cmd("write!")

  -- 顯示狀態消息
  ui.status("正在生成 AI 回應...", "WarningMsg")

  -- 重置狀態變數
  reset_state()

  -- 獲取插件目錄
  local plugin_dir = get_plugin_dir()

  -- 構建 Poetry 命令來運行 Python 腳本
  local python_script = config.get("python_path")
  local cmd = "cd "
      .. vim.fn.shellescape(plugin_dir)
      .. " && poetry run python -m python.ai_memory "
      .. vim.fn.shellescape(file_path)

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
        ui.notify("錯誤: " .. vim.inspect(data), vim.log.levels.ERROR)
      end
    end,
    on_exit = function(_, exit_code, _)
      if exit_code ~= 0 then
        ui.notify("處理失敗，退出代碼: " .. exit_code, vim.log.levels.ERROR)
      end
    end,
    stdout_buffered = false,
  })

  if job_id <= 0 then
    ui.notify("無法啟動 Python 進程", vim.log.levels.ERROR)
  end
end

-- 確保 Poetry 環境已設置
M.ensure_poetry_env = function()
  local plugin_dir = get_plugin_dir()

  -- 檢查是否安裝了 Poetry
  local poetry_check = vim.fn.system("which poetry")
  if vim.v.shell_error ~= 0 then
    ui.notify("未找到 Poetry。請先安裝 Poetry。", vim.log.levels.ERROR)
    return false
  end

  -- 檢查 Poetry 環境是否存在
  local poetry_env_check = vim.fn.system("cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry env info")
  if vim.v.shell_error ~= 0 then
    ui.notify("正在設置 Poetry 環境...", vim.log.levels.INFO)

    -- 如果 pyproject.toml 不存在，初始化 Poetry 項目
    if vim.fn.filereadable(plugin_dir .. "/pyproject.toml") == 0 then
      local init_cmd = "cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry init --no-interaction"
      vim.fn.system(init_cmd)

      if vim.v.shell_error ~= 0 then
        ui.notify("無法初始化 Poetry 項目", vim.log.levels.ERROR)
        return false
      end
    end

    -- 安裝依賴
    local install_cmd = "cd " .. vim.fn.shellescape(plugin_dir) .. " && poetry install"
    vim.fn.system(install_cmd)

    if vim.v.shell_error ~= 0 then
      ui.notify("無法安裝 Poetry 依賴", vim.log.levels.ERROR)
      return false
    end

    ui.notify("Poetry 環境設置成功", vim.log.levels.INFO)
  end

  return true
end

-- 在模組加載時初始化 Poetry 環境
M.init = function()
  -- 在插件加載時確保 Poetry 環境
  vim.defer_fn(function()
    M.ensure_poetry_env()
  end, 100)
end

return M
