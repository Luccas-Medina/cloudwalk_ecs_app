# PowerShell WebSocket Test Script
$uri = "ws://localhost:8000/ws/emotions?token=dev_ingest_token_please_change"

# Create WebSocket client
Add-Type -AssemblyName System.Net.WebSockets
$ws = New-Object System.Net.WebSockets.ClientWebSocket

# Connect
$cts = New-Object System.Threading.CancellationTokenSource
$task = $ws.ConnectAsync([System.Uri]::new($uri), $cts.Token)
$task.Wait()

Write-Host "Connected to WebSocket!"
Write-Host "Connection State: $($ws.State)"

# Send test emotion data
$testMessage = @{
    user_id = 1
    emotion_label = "joy"
    valence = 0.8
    arousal = 0.6
    confidence = 0.9
    source = "test"
    raw_payload = @{ test = "data" }
} | ConvertTo-Json

$bytes = [System.Text.Encoding]::UTF8.GetBytes($testMessage)
$buffer = New-Object System.ArraySegment[byte] -ArgumentList $bytes
$sendTask = $ws.SendAsync($buffer, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $cts.Token)
$sendTask.Wait()

Write-Host "Message sent: $testMessage"

# Close connection
$ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "Test complete", $cts.Token).Wait()
Write-Host "Connection closed"
