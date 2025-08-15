# mock_emotion_producer.ps1
# PowerShell WebSocket producer (requires .NET Framework/Core)

Add-Type -AssemblyName System.Net.Http
Add-Type -AssemblyName System.Web

function Send-EmotionEvents {
    $emotions = @("joy", "calm", "surprise", "anger", "sadness")
    $sources = @("text", "voice", "face")
    
    # Using Invoke-WebRequest for each emotion event via simulated HTTP
    # Note: This is a simplified version - WebSocket would need different approach
    
    for ($i = 0; $i -lt 5; $i++) {
        $event = @{
            user_id = 1
            session_id = "session_$i"
            source = $sources | Get-Random
            emotion_label = $emotions | Get-Random
            valence = [math]::Round((Get-Random -Minimum 0 -Maximum 100) / 100, 2)
            arousal = [math]::Round((Get-Random -Minimum 0 -Maximum 100) / 100, 2)
            confidence = [math]::Round((Get-Random -Minimum 70 -Maximum 100) / 100, 2)
            raw_payload = @{
                source = "mock_powershell"
                batch = $i
            }
        } | ConvertTo-Json -Depth 3
        
        Write-Host "Would send: $event"
        Write-Host ("-" * 50)
        Start-Sleep -Seconds 1
    }
}

Send-EmotionEvents
