from dependency_injector import containers, providers
import os
from miyoka.libs.logger import setup_logger
from miyoka.libs.obs_controller import OBSConfig
import importlib


def dynamic_import(game, klass_path, *args, **kwargs):
    print(f"importing miyoka.{game}.{klass_path}")
    ns, klass_name = klass_path.split(".")
    module = importlib.import_module(f"miyoka.{game}.{ns}")
    klass = getattr(module, klass_name)
    return klass(*args, **kwargs)


def create_obs_config(host, port, password):
    """Create OBSConfig from configuration values."""
    return OBSConfig(
        host=host or "localhost",
        port=port or 4455,
        password=password or "",
    )


config_path = os.environ.get("MIYOKA_CONFIG_PATH", "./config.yaml")


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=[config_path])

    logger = providers.Singleton(
        setup_logger,
        name=config.log.name,
        dir_path=config.log.dir_path,
        file_name=config.log.file_name,
        file_output=config.log.file_output,
        standard_output=config.log.standard_output,
        clear_everytime=config.log.clear_everytime,
        max_bytes=config.log.rotation.max_bytes,
        backup_count=config.log.rotation.backup_count,
        discord_webhook_url=config.discord.webhook_url,
        discord_min_level=config.discord.min_level,
    )

    obs_config = providers.Singleton(
        create_obs_config,
        host=config.obs.host,
        port=config.obs.port,
        password=config.obs.password,
    )

    game_window_helper = providers.Singleton(
        dynamic_import,
        game=config.game.name,
        klass_path="game_window_helper.GameWindowHelper",
        logger=logger,
        window_name=config.game.window.name,
        extra=config.game.extra,
    )

    replay_recorder = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="replay_recorder.ReplayRecorder",
        logger=logger,
        replay_search_players=config.game.players,
        replay_search_replay_ids=config.game.replay_ids,
        max_replays_per_run=config.replay_recorder.max_replays_per_run,
        stop_after_duplicate_replays=config.replay_recorder.stop_after_duplicate_replays,
        skip_recording=config.replay_recorder.skip_recording,
        separate_round=config.replay_recorder.separate_round,
        game_window_helper=game_window_helper,
        local_file_storage_dir=config.replay_recorder.local_file_storage_dir,
        obs_config=obs_config,
    )

    screen_customizer = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="screen_customizer.ScreenCustomizer",
        logger=logger,
        game_window_helper=game_window_helper,
        exit_to_desktop=config.replay_recorder.exit_to_desktop,
    )
