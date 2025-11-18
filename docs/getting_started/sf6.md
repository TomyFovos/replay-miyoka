# Getting started for Street Fighter 6

## Before you continue

- Make sure that you've finished [the setup](../getting_started.md#setup).

## Record replays

Replay Recorder is the automation for recording replays in the game.

1. Launch Street Fighter 6.
1. Right-click on the `miyoka/record-replay.ps1` file and click **Run with PowerShell**.
    Alternatively, you can open Windows Powershell and execute the following command:
    ```shell
    powershell.exe -executionpolicy bypass -file .\record-replay.ps1
    ```

NOTE:

- During the recording, you should **NOT** move your mouse or type keyboard. Otheriwse, the recording will stop.
- The recording could take a few hours to finish. Run it when you don't have a plan to use your computer e.g. run it while you sleep.

### Save replays in your computer

You can record and save replays in your computer instead of uploading the videos to google cloud storage.
To do so, set `local_file_storage` to `replay_recorder.save_to` in `config.yaml`.

The recorded replays can be found in the `replays` folder in the miyoka directory.
