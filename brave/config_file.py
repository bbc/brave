import yaml
import brave.config
import tempfile


def as_yaml(session):
    '''
    Get the current config, as a YAML string.
    This can then be used to start another Brave with the same configuration.
    '''
    config = brave.config.raw()

    for block_type in ['inputs', 'outputs', 'overlays', 'mixers']:
        if block_type in config:
            del(config[block_type])
        collection = getattr(session, block_type)
        if len(collection) > 0:
            config[block_type] = []
            for name, block in collection.items():
                config[block_type].append(block.summarise(for_config_file=True))
    return yaml.dump(config)


def as_yaml_file(session):
    '''
    Returns the current config, as a temporary YAML file.
    '''
    config_as_yaml = as_yaml(session)
    fp = tempfile.NamedTemporaryFile(delete=False)
    fp.write(config_as_yaml.encode())
    fp.close()
    return fp.name
