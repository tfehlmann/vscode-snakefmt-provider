# Snakefmt extension for Visual Studio Code

A [Visual Studio Code](https://code.visualstudio.com/) extension that formats [Snakemake](https://snakemake.readthedocs.io/) code using [Snakefmt](https://github.com/snakemake/snakefmt). The extension ships with `snakefmt=0.10.2`. 
The bundled `snakefmt` is used if no `path` to the executable or `interpreter` is specified.

## Features

This extensions uses `snakefmt` to format your `Snakemake` code. It can also supports formatting `Python` code.
It automatically checks if your Snakemake file is formatted according to `snakefmt`.
You can disable this feature by setting `snakefmt.disableLinting = true`. This feature is disabled per default for `Python` files and can be enabled with `snakefmt.enablePythonLinting = true`.

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
| snakefmt.args             | `[]`         | Custom arguments passed to `snakefmt`. E.g `"snakefmt.args" = ["--config", "<file>"]` |
| snakefmt.config           | `""`         | Snakefmt config file. Deprecated. Use `snakefmt.args` instead. Usage `"snakefmt.config" = "<file>"` |
| snakefmt.disableLinting   | `false`         | Disable linting of snakemake files. |
| snakefmt.enablePythonLinting   | `false`    | Enable linting of python files with `snakefmt`. |
| snakefmt.path             | `[]`         | Setting to provide custom `snakefmt` executable. Example 1: `["~/global_env/snakefmt"]` Example 2: `["conda", "run", "-n", "fmt_env", "--no-capture-output", "snakefmt"]` |
| snakefmt.executable       | `""`         | Alias for `snakefmt.path`. Deprecated. Use `snakefmt.path` instead. |
| snakefmt.interpreter      | `[]`         | Path to a python interpreter to use to run the formatter server.                                                                                                                                                                                                            |
| snakefmt.importStrategy   | `useBundled` | Setting to choose where to load `snakefmt` from. `useBundled` picks snakefmt bundled with the extension. `fromEnvironment` uses `snakefmt` available in the environment.                                                                                                          |
| snakefmt.showNotification | `off`        | Setting to control when a notification is shown.                                                                                                                                                                                                                         |

## Commands

| Command                  | Description                       |
| ------------------------ | --------------------------------- |
| Snakefmt: Restart server | Force re-start the format server. |

## Logging

From the Command Palette (**View** > **Command Palette ...**), run the **Developer: Set Log Level...** command. Select **Snakefmt** from the **Extension logs** group. Then select the log level you want to set.

Alternatively, you can set the `snakefmt.trace.server` setting to `verbose` to get more detailed logs from the Snakefmt server. This can be helpful when filing bug reports.

To open the logs, click on the language status icon (`{}`) on the bottom right of the Status bar, next to the Python language mode. Locate the **Snakefmt** entry and select **Open logs**.


## Source code
Available on github: https://github.com/tfehlmann/vscode-snakefmt-provider


## Release Notes

### 0.8.0
- Update bundled `snakefmt` to `0.10.2`

### 0.7.0 (preview release)
- Update bundled `snakefmt` to `0.8.5`
- Fix "There is no formatter for Snakemake files installed" error
- Remove logging setting, switch to VSCode integrated log level

### 0.6.0
- Update bundled `snakefmt` to `0.8.1`

### 0.5.0 (preview release)
- Add support for Python 3.11
- Update bundled `snakefmt` to `0.7.0`

### 0.4.0
- Integrate 0.3.0 preview release features
- Improve linting messages

### 0.3.0 (preview release)
- Support Python formatting
- Add better linting messages and error highlighting

### 0.2.0
- Add linting support
- Support for multi-root workspace
- Add bundled `snakefmt`

### 0.1.0

Initial release

