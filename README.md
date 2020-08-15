# Snakefmt extension for Visual Studio code

A [Visual Studio Code](https://code.visualstudio.com/) extension that formats [Snakemake](https://snakemake.readthedocs.io/) code using [Snakefmt](https://github.com/snakemake/snakefmt). It can be configured with a config file.

## Features

This extensions uses snakefmt to format your snakemake code. 

Files or code chunks can be formatted on-demand by right clicking in the document and
selecting "Format Document", or by using the associated keyboard shortcut
(usually Ctrl+⇧+F on Windows, Ctrl+⇧+I on Linux, and ⇧+⌥+F on macOS).

To automatically format a file on save, add the following to your
vscode settings.json file:

```json
{
    "editor.formatOnSave": true
}
```

## Requirements

[Snakefmt](https://github.com/snakemake/snakefmt) needs to be installed. If it is not installed in a standard location you can specify the location of the executable in your vscode settings.json file:
```json
{
    "snakefmt.executable": "/absolute/path/to/snakefmt"
}
```

Placeholders can also be used in the `snakefmt.executable` value.
The following placeholders are supported:

- `${workspaceRoot}` - replaced by the absolute path of the current vscode workspace root.
- `${workspaceFolder}` - replaced by the absolute path of the current vscode workspace. In case of outside-workspace files `${workspaceFolder}` expands to the absolute path of the first available workspace.
- `${cwd}` - replaced by the current working directory of vscode.
- `${env.VAR}` - replaced by the environment variable $VAR, e.g. `${env.HOME}` will be replaced by `$HOME`, your home directory.

For example:
- `${env.HOME}/miniconda3/envs/snakeenv/bin/snakefmt` - use a snakefmt version installed over conda in an environment named `snakeenv`.

## Source code
Available on github: https://github.com/tfehlmann/vscode-snakefmt-provider


## Extension Settings

Include if your extension adds any VS Code settings through the `contributes.configuration` extension point.

For example:

This extension contributes the following settings:

* `snakefmt.executable`: path to snakefmt executable
* `snakefmt.config`: optional absolute path to snakefmt config file (per default `${workspaceFolder}/pyproject.toml`, if existing)


## Release Notes

### 0.1.0

Initial release

