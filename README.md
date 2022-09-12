# Snakefmt extension for Visual Studio Code

A [Visual Studio Code](https://code.visualstudio.com/) extension that formats [Snakemake](https://snakemake.readthedocs.io/) code using [Snakefmt](https://github.com/snakemake/snakefmt). The extension ships with `snakefmt=0.6.1`. 
The bundled `snakefmt` is used if no `path` to the executable or `interpreter` is specified.

## Features

This extensions uses `snakefmt` to format your `Snakemake` code. 
It automatically checks if your Snakemake file is formatted according to `snakefmt`.
You can disable this feature by setting `snakefmt.disableLinting = true`.

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

## Settings

| Settings                         | Default      | Description                                                                                                                                                                                                                                                              |
| -------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| snakefmt.args             | `[]`         | Custom arguments passed to `snakefmt`. E.g `"snakefmt.args" = ["--config", "<file>"]`                                                                                                                                                                                |
| snakefmt.config           | `""`         | Snakefmt config file. Deprecated. Use `snakefmt.args` instead. Usage `"snakefmt.config" = "<file>"`                                                                                                                                                                                |
| snakefmt.disableLinting   | `false`         | Disable linting of snakemake files`                                                                                                                                                                                |
| snakefmt.trace            | `error`      | Sets the tracing level for the extension.                                                                                                                                                                                                                                |
| snakefmt.path             | `[]`         | Setting to provide custom `snakefmt` executable. Example 1: `["~/global_env/snakefmt"]` Example 2: `["conda", "run", "-n", "fmt_env", "--no-capture-output", "snakefmt"]` |
| snakefmt.executable       | `""`         | Alias for `snakefmt.path`. Deprecated. Use `snakefmt.path` instead. |
| snakefmt.interpreter      | `[]`         | Path to a python interpreter to use to run the formatter server.                                                                                                                                                                                                            |
| snakefmt.importStrategy   | `useBundled` | Setting to choose where to load `snakefmt` from. `useBundled` picks snakefmt bundled with the extension. `fromEnvironment` uses `snakefmt` available in the environment.                                                                                                          |
| snakefmt.showNotification | `off`        | Setting to control when a notification is shown.                                                                                                                                                                                                                         |

## Commands

| Command                  | Description                       |
| ------------------------ | --------------------------------- |
| Snakefmt: Restart server | Force re-start the format server. |

## Source code
Available on github: https://github.com/tfehlmann/vscode-snakefmt-provider


## Release Notes

### 0.2.0
- Add linting support
- Support for multi-root workspace
- Add bundled `snakefmt`

### 0.1.0

Initial release

