Write-Host "Setting up Miyoka..."

if (Test-Path "./config.yaml") {
    Remove-Item "./config.yaml"
}

Write-Host "Creating config file..."
Copy-Item -Path "./config.yaml.example" -Destination "./config.yaml"

$game_name = Read-Host "Enter your fighting game name.  Supported games: [sf6]"

if ($game_name -eq "sf6") {
    $game_window_name = "Street Fighter 6"
    $original_language = Read-Host "Enter the game language (en/jp)"
    if ($original_language -ne "jp") {
        $original_language = "en"
    }
    $original_quality = "Normal"
    $original_display_mode = "Windowed"
}

Write-Host @"
===========================================================================
Setup complete!
===========================================================================

Next steps:

1. Edit config.yaml and set your player information:
   - game.players[].name: Your display name
   - game.players[].id: Your player ID in the game
   - game.players[].pattern: Your in-game name pattern

2. (Optional) Change replay_recorder.local_file_storage_dir to customize
   where replays are saved.

3. Run record-replay.ps1 to start recording replays.

Note: Do NOT share config.yaml with anyone if it contains personal information.
"@


