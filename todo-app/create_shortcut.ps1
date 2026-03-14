$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Todo App.lnk")
$sc.TargetPath = "E:\ClaudeCode\todo-app\start.bat"
$sc.WorkingDirectory = "E:\ClaudeCode\todo-app"
$sc.Description = "Todo App"
$sc.Save()
