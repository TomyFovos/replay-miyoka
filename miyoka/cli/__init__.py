"""
Miyoka CLI - Command Line Interface for Replay Miyoka.
"""
import click
import os
import sys

# Ensure UTF-8 encoding for Python
os.environ.setdefault("PYTHONUTF8", "1")


@click.group()
@click.version_option(version="0.2.0", prog_name="miyoka")
@click.option(
    "--config", "-c",
    envvar="MIYOKA_CONFIG_PATH",
    default="./config.yaml",
    help="Path to config.yaml file"
)
@click.pass_context
def cli(ctx, config):
    """
    Miyoka - Automated replay recording tool for fighting games.
    
    Use 'miyoka COMMAND --help' for more information about each command.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    os.environ["MIYOKA_CONFIG_PATH"] = config


@cli.command()
@click.option(
    "--no-launch-game", 
    is_flag=True, 
    help="Skip automatic game launch"
)
@click.option(
    "--no-launch-obs", 
    is_flag=True, 
    help="Skip automatic OBS launch"
)
@click.option(
    "--no-stop-obs", 
    is_flag=True, 
    help="Do not stop OBS after recording"
)
@click.option(
    "--no-stop-game", 
    is_flag=True, 
    help="Do not stop game after recording"
)
@click.pass_context
def record(ctx, no_launch_game, no_launch_obs, no_stop_obs, no_stop_game):
    """
    Record game replays automatically.
    
    This command will:
    1. Launch the game (if not already running)
    2. Launch OBS (if not already running)
    3. Navigate to replay center and record replays
    4. Save recordings to local storage
    5. Optionally stop OBS and game when complete
    """
    click.echo("Starting replay recording...")
    
    from miyoka.container import Container
    from miyoka.libs.obs_controller import OBSController, OBSProcessController, OBSConfig
    from miyoka.libs.game_launcher import create_game_launcher
    
    container = Container()
    logger = container.logger()
    config = container.config()
    
    try:
        # Get game configuration
        game_name = config.get("game", {}).get("name", "sf6")
        game_config = config.get("game", {})
        launch_config = game_config.get("launch", {})
        
        # Initialize game launcher
        game_launcher = create_game_launcher(
            logger=logger,
            game_name=game_name,
            method=launch_config.get("method", "direct"),
            exe_path=launch_config.get("exe_path"),
            steam_app_id=launch_config.get("steam_app_id"),
            window_title=game_config.get("window", {}).get("name", "Street Fighter 6"),
            startup_wait_seconds=launch_config.get("startup_wait_seconds", 60.0),
        )
        
        # Launch game if needed
        if not no_launch_game:
            click.echo("Checking game status...")
            if not game_launcher.is_running():
                click.echo("Launching game...")
                if not game_launcher.launch():
                    click.echo("Failed to launch game. Exiting.", err=True)
                    sys.exit(1)
            else:
                click.echo("Game is already running.")
        
        # Initialize OBS
        obs_config = config.get("obs", {})
        obs_controller = OBSController(
            logger=logger,
            config=OBSConfig(
                host=obs_config.get("websocket", {}).get("host", "localhost"),
                port=obs_config.get("websocket", {}).get("port", 4455),
                password=obs_config.get("websocket", {}).get("password"),
            )
        )
        obs_process = OBSProcessController(
            logger=logger,
            obs_path=obs_config.get("exe_path")
        )
        
        # Launch OBS if needed
        if not no_launch_obs:
            click.echo("Checking OBS status...")
            if not obs_process.is_running():
                click.echo("Launching OBS...")
                if not obs_process.start():
                    click.echo("Failed to launch OBS. Exiting.", err=True)
                    sys.exit(1)
            else:
                click.echo("OBS is already running.")
        
        # Focus game window
        click.echo("Focusing game window...")
        game_launcher.focus()
        game_launcher.move_to_origin()
        
        # Wire container and run replay recorder
        container.wire(modules=["miyoka.replay-recorder"])
        
        from miyoka.libs.replay_recorder import ReplayRecorder
        from dependency_injector.wiring import inject, Provide
        
        @inject
        def run_recorder(
            replay_recorder: ReplayRecorder = Provide[Container.replay_recorder],
        ):
            replay_recorder.run()
        
        click.echo("Starting replay recording process...")
        run_recorder()
        
        click.echo("Replay recording completed.")
        
    except Exception as e:
        logger.error(f"Error during recording: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    
    finally:
        # Cleanup
        if not no_stop_obs:
            click.echo("Stopping OBS...")
            obs_process.stop()
        
        if not no_stop_game:
            # Game exit is handled by the game itself via exit_to_desktop setting
            pass
    
    click.echo("Done!")


@cli.command()
@click.pass_context
def setup(ctx):
    """
    Interactive setup wizard for Miyoka configuration.
    
    This will create a config.yaml file with your settings.
    """
    import shutil
    from pathlib import Path
    
    config_path = Path(ctx.obj["config_path"])
    example_path = Path("./config.yaml.example")
    
    click.echo("=" * 60)
    click.echo("Miyoka Setup Wizard")
    click.echo("=" * 60)
    click.echo()
    
    # Check if config already exists
    if config_path.exists():
        if not click.confirm(f"Config file already exists at {config_path}. Overwrite?"):
            click.echo("Setup cancelled.")
            return
        config_path.unlink()
    
    # Copy example config
    if example_path.exists():
        shutil.copy(example_path, config_path)
        click.echo(f"Created config file: {config_path}")
    else:
        click.echo("Warning: config.yaml.example not found. Creating minimal config.", err=True)
    
    click.echo()
    
    # Get game settings
    game_name = click.prompt(
        "Enter your fighting game name",
        type=click.Choice(["sf6"]),
        default="sf6"
    )
    
    if game_name == "sf6":
        window_name = "Street Fighter 6"
        steam_app_id = "1364780"
    
    # Get language
    language = click.prompt(
        "Enter the game language",
        type=click.Choice(["en", "jp"]),
        default="en"
    )
    
    # Get launch method
    launch_method = click.prompt(
        "How do you want to launch the game?",
        type=click.Choice(["direct", "steam"]),
        default="direct"
    )
    
    exe_path = None
    if launch_method == "direct":
        exe_path = click.prompt(
            "Enter the path to game executable",
            default=""
        )
        if not exe_path:
            exe_path = None
    
    # Get player ID
    player_id = click.prompt(
        "Enter your player ID (for replay search)",
        default=""
    )
    
    click.echo()
    click.echo("=" * 60)
    click.echo("Setup complete!")
    click.echo("=" * 60)
    click.echo()
    click.echo("Next steps:")
    click.echo(f"1. Edit {config_path} to fine-tune your settings")
    click.echo("2. Run 'miyoka record' to start recording replays")
    click.echo()
    click.echo("Note: Do NOT share config.yaml if it contains personal information.")


@cli.command()
@click.option(
    "--output", "-o",
    default="screenshot.jpeg",
    help="Output file path"
)
@click.pass_context
def screenshot(ctx, output):
    """
    Take a screenshot of the game window.
    
    Useful for debugging and creating template images.
    """
    click.echo("Taking screenshot...")
    
    from miyoka.container import Container
    
    container = Container()
    container.wire(modules=[__name__])
    
    from miyoka.libs.game_window_helper import GameWindowHelper
    from dependency_injector.wiring import inject, Provide
    
    @inject
    def take_screenshot(
        game_window_helper: GameWindowHelper = Provide[Container.game_window_helper],
    ):
        game_window_helper.wait_until_game_launched()
        game_window_helper.wait_until_game_focused()
        game_window_helper.update_game_window_size()
        game_window_helper.init_camera()
        
        frame = game_window_helper.grab_frame()
        game_window_helper.save_image(frame, output)
        
        click.echo(f"Screenshot saved to: {output}")
    
    try:
        take_screenshot()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--interval", "-i",
    type=float,
    default=12.0,
    help="Interval between recordings in hours"
)
@click.option(
    "--install", 
    is_flag=True, 
    help="Install systemd timer (Linux only)"
)
@click.option(
    "--uninstall", 
    is_flag=True, 
    help="Uninstall systemd timer (Linux only)"
)
@click.option(
    "--status", 
    is_flag=True, 
    help="Show scheduler status"
)
@click.pass_context
def scheduler(ctx, interval, install, uninstall, status):
    """
    Manage scheduled replay recording.
    
    On Linux, this uses systemd timer for scheduling.
    """
    import platform
    
    if platform.system() != "Linux":
        click.echo("Scheduler is currently only supported on Linux.", err=True)
        click.echo("On Windows, please use Task Scheduler manually.")
        sys.exit(1)
    
    from miyoka.libs.scheduler import SystemdScheduler
    
    config_path = ctx.obj["config_path"]
    scheduler_manager = SystemdScheduler(config_path=config_path)
    
    if status:
        scheduler_manager.show_status()
    elif install:
        click.echo(f"Installing systemd timer with {interval} hour interval...")
        if scheduler_manager.install(interval_hours=interval):
            click.echo("Scheduler installed successfully!")
            click.echo("Use 'miyoka scheduler --status' to check status.")
        else:
            click.echo("Failed to install scheduler.", err=True)
            sys.exit(1)
    elif uninstall:
        click.echo("Uninstalling systemd timer...")
        if scheduler_manager.uninstall():
            click.echo("Scheduler uninstalled successfully!")
        else:
            click.echo("Failed to uninstall scheduler.", err=True)
            sys.exit(1)
    else:
        click.echo("Use --install, --uninstall, or --status")
        click.echo("Example: miyoka scheduler --install --interval 12")


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    import platform
    
    click.echo("Miyoka - Automated Replay Recording Tool")
    click.echo()
    click.echo(f"Version: 0.2.0")
    click.echo(f"Platform: {platform.system()} {platform.release()}")
    click.echo(f"Python: {platform.python_version()}")
    
    # Check available features
    click.echo()
    click.echo("Available features:")
    
    # Check platform support
    try:
        from miyoka.libs.platform import get_platform
        plat = get_platform()
        click.echo(f"  Platform support: {plat} ✓")
    except Exception as e:
        click.echo(f"  Platform support: Error - {e}")
    
    # Check OBS support
    try:
        import obsws_python
        click.echo("  OBS WebSocket: Available ✓")
    except ImportError:
        click.echo("  OBS WebSocket: Not installed (pip install obsws-python)")
    
    # Check Linux-specific tools
    if platform.system() == "Linux":
        import shutil
        if shutil.which("xdotool"):
            click.echo("  xdotool: Available ✓")
        else:
            click.echo("  xdotool: Not installed (sudo apt install xdotool)")


def main():
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
