// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below

// This line should always be right on top.
// tslint:disable:no-any
if ((Reflect as any).metadata === undefined) {
  require('reflect-metadata');
}

import * as vscode from 'vscode';

import cp = require('child_process');
import path = require('path');
import { getBinPath } from './snakefmtPath';

import { getTextEditsFromPatch } from './editor';
import { fstat, existsSync } from 'fs';

export let outputChannel = vscode.window.createOutputChannel('snakefmt');

function getPlatformString() {
  switch (process.platform) {
    case 'win32': return 'windows';
    case 'linux': return 'linux';
    case 'darwin': return 'osx';
  }

  return 'unknown';
}

export class SnakemakeDocumentFormattingEditProvider implements vscode.DocumentFormattingEditProvider, vscode.DocumentRangeFormattingEditProvider {
  private defaultConfigure = {
    executable: 'snakefmt',
    config: '${workspaceFolder}/pyproject.toml'
  };

  public provideDocumentFormattingEdits(document: vscode.TextDocument, options: vscode.FormattingOptions, token: vscode.CancellationToken): Thenable<vscode.TextEdit[]> {
    return this.doFormatDocument(document, null, options, token);
  }

  public provideDocumentRangeFormattingEdits(document: vscode.TextDocument, range: vscode.Range, options: vscode.FormattingOptions, token: vscode.CancellationToken): Thenable<vscode.TextEdit[]> {
    return this.doFormatDocument(document, range, options, token);
  }

  /// Get execute name in snakefmt.executable, if not found, use default value
  /// If configure has changed, it will get the new value
  private getExecutablePath() {
    let platform = getPlatformString();
    let config = vscode.workspace.getConfiguration('snakefmt');

    let platformExecPath = config.get<string>('executable.' + platform);
    let defaultExecPath = config.get<string>('executable');
    let execPath = platformExecPath || defaultExecPath;

    if (!execPath) {
      return this.defaultConfigure.executable;
    }

    let root = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.path : '';

    let wsfolder = this.getWorkspaceFolder() || '';
    // replace placeholders, if present
    return execPath
      .replace(/\${workspaceRoot}/g, root)
      .replace(/\${workspaceFolder}/g, wsfolder)
      .replace(/\${cwd}/g, process.cwd())
      .replace(/\${env\.([^}]+)}/g, (_substring: string, ...args: any[]): string => {
        if (args[0]) {
          return process.env[args[0]] || '';
        } else {
          return '';
        }
      });
  }

  private getWorkspaceFolder(): string | undefined {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      return undefined;
    }

    if (!vscode.workspace.workspaceFolders) {
      return undefined;
    }

    const currentDocumentUri = editor.document.uri;
    let workspacePath = vscode.workspace.getWorkspaceFolder(currentDocumentUri);
    if (!workspacePath) {
      const fallbackWorkspace = vscode.workspace.workspaceFolders[0];
      vscode.window.showWarningMessage(`Unable to deduce the location of snakefmt executable for file outside the workspace - expanding \${workspaceFolder} to '${fallbackWorkspace.name}' path`);
      workspacePath = fallbackWorkspace;
    }
    return workspacePath.uri.path;
  }

  private doFormatDocument(document: vscode.TextDocument, range: vscode.Range | null, _options: vscode.FormattingOptions | null, token: vscode.CancellationToken | null): Thenable<vscode.TextEdit[]> {
    return new Promise((resolve, reject) => {
      let formatCommandBinPath = getBinPath(this.getExecutablePath());
      let codeContent = document.getText();

      if (range) {
        let offset = document.offsetAt(range.start);
        let length = document.offsetAt(range.end) - offset;
        codeContent = codeContent.substr(offset, length);
      }

      let eol = document.eol === vscode.EndOfLine.CRLF ? '\n': '\r\n';
      if(!codeContent.endsWith(eol)){
        codeContent += eol;
      }

      let workingPath = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.path : '';
      if (!document.isUntitled) {
        workingPath = path.dirname(document.fileName);
      }

      let config = vscode.workspace.getConfiguration('snakefmt');
      let cfg_file = config.get<string>('config');

      let args = ["--compact-diff", "-"];
      if(cfg_file && existsSync(cfg_file)) {
        args.push("--config");
        args.push(cfg_file);
      }
      const proc = cp.execFile(formatCommandBinPath, args, {windowsHide: true, maxBuffer: 1024*1024*1024}, (error, stdout, stderr) => {
        try {
          if (error !== null && error.code !== 0 && stderr.length !== 0) {
            outputChannel.show();
            outputChannel.clear();
            outputChannel.appendLine(stderr);
            if(error.message.startsWith("Command failed:")) {
              vscode.window.showInformationMessage('The \'' + formatCommandBinPath + '\' command is not available.  Please check your snakefmt.executable user setting and ensure it is installed.');
              return resolve(undefined);
            }
            return reject('Cannot format due to syntax errors.');
          }

          if (error !== null && error.code !== 0) {
            return reject();
          }

          return resolve(getTextEditsFromPatch(codeContent, stdout, range));
        } catch (e) {
          reject(e);
        }
      });

      if(proc.stdin !== null) {
        proc.stdin.write(codeContent);
        proc.stdin.end();
      }

      if (token) {
        token.onCancellationRequested(() => {
          proc.kill();
          reject('Cancelation requested');
        });
      }
    });
  }

  public formatDocument(document: vscode.TextDocument): Thenable<vscode.TextEdit[]> {
    return this.doFormatDocument(document, null, null, null);
  }
}


// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  let formatter = new SnakemakeDocumentFormattingEditProvider();
  let SNAKEMAKE_MODE: vscode.DocumentSelector = { scheme: 'file', language: 'snakemake' };
  context.subscriptions.push(vscode.languages.registerDocumentRangeFormattingEditProvider(SNAKEMAKE_MODE, formatter));
  context.subscriptions.push(vscode.languages.registerDocumentFormattingEditProvider(SNAKEMAKE_MODE, formatter));
}

// this method is called when your extension is deactivated
export function deactivate() { }
