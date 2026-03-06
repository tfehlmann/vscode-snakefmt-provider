# Snakefmt extension for Visual Studio Code

A [Visual Studio Code](https://code.visualstudio.com/) extension that formats [Snakemake](https://snakemake.readthedocs.io/) code using [Snakefmt](https://github.com/snakemake/snakefmt). The extension ships with `snakefmt=0.11.4`. 
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

### [`snakefmt.args`](#snakefmtargs)

Custom arguments passed to `snakefmt`. Each argument should be provided as a separate string in the array.

**Default value**: `[]`
**Type**: `string[]`

```json
"snakefmt.args": ["--config", "<file>"]
```

### [`snakefmt.disableLinting`](#snakefmtdisablelinting)

Disable linting of Snakemake files.

**Default value**: `false`
**Type**: `boolean`

```json
"snakefmt.disableLinting": true
```

### [`snakefmt.enablePythonLinting`](#snakefmtenablepythonlinting)

Enable linting of Python files with `snakefmt`.

**Default value**: `false`
**Type**: `boolean`

```json
"snakefmt.enablePythonLinting": true
```

### [`snakefmt.path`](#snakefmtpath)

Path or command to be used by the extension to run `snakefmt`. Accepts an array of a single or multiple strings. If passing a command, each argument should be provided as a separate string in the array.

> **Note**: Using this option may slow down server response time.

**Default value**: `[]`
**Type**: `string[]`

```json
// Use a custom binary
"snakefmt.path": ["~/global_env/snakefmt"]

// Use conda
"snakefmt.path": ["conda", "run", "-n", "fmt_env", "--no-capture-output", "snakefmt"]
```

### [`snakefmt.interpreter`](#snakefmtinterpreter)

Path to a Python executable that will be used to launch the formatter server and any subprocess. When set to `[]`, the extension will use the path to the selected Python interpreter.

**Default value**: `[]`
**Type**: `string[]`

```json
"snakefmt.interpreter": ["/path/to/python"]
```

### [`snakefmt.importStrategy`](#snakefmtimportstrategy)

Defines where `snakefmt` is imported from. This setting may be ignored if `snakefmt.path` is set.

- `"useBundled"`: Always use the bundled version of `snakefmt`.
- `"fromEnvironment"`: Use `snakefmt` from the environment, falling back to the bundled version if not available.

**Default value**: `"useBundled"`
**Type**: `"useBundled" | "fromEnvironment"`

```json
"snakefmt.importStrategy": "fromEnvironment"
```

### [`snakefmt.showNotifications`](#snakefmtshownotifications)

Controls when notifications are shown by this extension.

- `"off"`: All notifications are turned off, any errors or warnings are still available in the logs.
- `"onError"`: Notifications are shown only in the case of an error.
- `"onWarning"`: Notifications are shown for errors and warnings.
- `"always"`: Notifications are shown for anything that the server chooses to show.

**Default value**: `"off"`
**Type**: `"off" | "onError" | "onWarning" | "always"`

```json
"snakefmt.showNotifications": "onError"
```

### [`snakefmt.trace.server`](#snakefmttraceserver)

Controls the level of trace logging for communication between VS Code and the Snakefmt language server. Useful when filing bug reports.

- `"off"`: No trace logging.
- `"messages"`: Log messages sent between client and server.
- `"verbose"`: Log messages and their content.

**Default value**: `"off"`
**Type**: `"off" | "messages" | "verbose"`

```json
"snakefmt.trace.server": "verbose"
```

### Deprecated settings

#### [`snakefmt.config`](#snakefmtconfig)

> **Deprecated**: Use `snakefmt.args` with `["--config", "<file>"]` instead.

Snakefmt config file.

**Default value**: `""`
**Type**: `string`

#### [`snakefmt.executable`](#snakefmtexecutable)

> **Deprecated**: Use `snakefmt.path` instead.

Alias for `snakefmt.path`.

**Default value**: `""`
**Type**: `string`

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

### 0.9.0
- Update bundled `snakefmt` to `0.11.4`
- Require Python 3.11+ (previously 3.8)
- Add automated publishing to VS Code Marketplace and Open VSX
- Update CI to Node 20, Python 3.11+, latest GitHub Action versions
- Migrate to ESLint 10 flat config
- Update all npm and Python dependencies

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

