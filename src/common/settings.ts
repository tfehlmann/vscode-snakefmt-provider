// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { ConfigurationChangeEvent, ConfigurationScope, WorkspaceConfiguration, WorkspaceFolder } from 'vscode';
import { getInterpreterDetails } from './python';
import { getConfiguration, getWorkspaceFolders } from './vscodeapi';
import { traceInfo, traceLog, traceWarn } from './logging';
import { get } from 'http';

export interface ISettings {
    cwd: string;
    workspace: string;
    config: string;
    disableLinting: boolean;
    enablePythonLinting: boolean;
    args: string[];
    path: string[];
    executable: string;
    interpreter: string[];
    importStrategy: string;
    showNotifications: string;
}

export function getExtensionSettings(namespace: string, includeInterpreter?: boolean): Promise<ISettings[]> {
    return Promise.all(getWorkspaceFolders().map((w) => getWorkspaceSettings(namespace, w, includeInterpreter)));
}

function resolveVariables(
    value: string[],
    workspace?: WorkspaceFolder,
    interpreter?: string[],
    env?: NodeJS.ProcessEnv,
): string[] {
    const substitutions = new Map<string, string>();
    const home = process.env.HOME || process.env.USERPROFILE;
    if (home) {
        substitutions.set('${userHome}', home);
    }
    if (workspace) {
        substitutions.set('${workspaceFolder}', workspace.uri.fsPath);
    }
    substitutions.set('${cwd}', process.cwd());
    getWorkspaceFolders().forEach((w) => {
        substitutions.set('${workspaceFolder:' + w.name + '}', w.uri.fsPath);
    });

    env = env || process.env;
    if (env) {
        for (const [key, value] of Object.entries(env)) {
            if (value) {
                substitutions.set('${env:' + key + '}', value);
            }
        }
    }

    const modifiedValue = [];
    for (const v of value) {
        if (interpreter && v === '${interpreter}') {
            modifiedValue.push(...interpreter);
        } else {
            modifiedValue.push(v);
        }
    }

    return modifiedValue.map((s) => {
        for (const [key, value] of substitutions) {
            s = s.replace(key, value);
        }
        return s;
    });
}

function getCwd(config: WorkspaceConfiguration, workspace: WorkspaceFolder): string {
    const cwd = config.get<string>('cwd', workspace.uri.fsPath);
    return resolveVariables([cwd], workspace)[0];
}

export function getInterpreterFromSetting(namespace: string, scope?: ConfigurationScope) {
    const config = getConfiguration(namespace, scope);
    return config.get<string[]>('interpreter');
}

export async function getWorkspaceSettings(
    namespace: string,
    workspace: WorkspaceFolder,
    includeInterpreter?: boolean,
): Promise<ISettings> {
    const config = getConfiguration(namespace, workspace.uri);

    let interpreter: string[] = [];
    if (includeInterpreter) {
        interpreter = getInterpreterFromSetting(namespace, workspace) ?? [];
        if (interpreter.length === 0) {
            traceLog(`No interpreter found from setting ${namespace}.interpreter`);
            traceLog(`Getting interpreter from ms-python.python extension for workspace ${workspace.uri.fsPath}`);
            interpreter = (await getInterpreterDetails(workspace.uri)).path ?? [];
            if (interpreter.length > 0) {
                traceLog(
                    `Interpreter from ms-python.python extension for ${workspace.uri.fsPath}:`,
                    `${interpreter.join(' ')}`,
                );
            }
        } else {
            traceLog(`Interpreter from setting ${namespace}.interpreter: ${interpreter.join(' ')}`);
        }

        if (interpreter.length === 0) {
            traceLog(`No interpreter found for ${workspace.uri.fsPath} in settings or from ms-python.python extension`);
        }
    }

    const workspaceSetting = {
        cwd: getCwd(config, workspace),
        workspace: workspace.uri.toString(),
        args: resolveVariables(config.get<string[]>('args', []), workspace),
        config: config.get<string>(`config`, ''),
        disableLinting: config.get<boolean>(`disableLinting`, false),
        enablePythonLinting: config.get<boolean>(`enablePythonLinting`, false),
        path: resolveVariables(config.get<string[]>('path', []), workspace, interpreter),
        executable: config.get<string>(`executable`, ''),
        interpreter: resolveVariables(interpreter, workspace),
        importStrategy: config.get<string>('importStrategy', 'useBundled'),
        showNotifications: config.get<string>('showNotifications', 'off'),
    };
    return workspaceSetting;
}

function getGlobalValue<T>(config: WorkspaceConfiguration, key: string): T | undefined {
    const inspect = config.inspect<T>(key);
    return inspect?.globalValue ?? inspect?.defaultValue;
}

export async function getGlobalSettings(namespace: string, includeInterpreter?: boolean): Promise<ISettings> {
    const config = getConfiguration(namespace);

    let interpreter: string[] = [];
    if (includeInterpreter) {
        interpreter = getGlobalValue<string[]>(config, 'interpreter') ?? [];
        if (interpreter === undefined || interpreter.length === 0) {
            interpreter = (await getInterpreterDetails()).path ?? [];
        }
    }

    const setting = {
        cwd: process.cwd(),
        workspace: process.cwd(),
        args: getGlobalValue<string[]>(config, 'args') ?? [],
        path: getGlobalValue<string[]>(config, 'path') ?? [],
        interpreter: interpreter ?? [],
        importStrategy: getGlobalValue<string>(config, 'importStrategy') ?? 'useBundled',
        showNotifications: getGlobalValue<string>(config, 'showNotifications') ?? 'off',
        config: getGlobalValue<string>(config, 'config') ?? '',
        disableLinting: getGlobalValue<boolean>(config, 'disableLinting') ?? false,
        enablePythonLinting: getGlobalValue<boolean>(config, 'enablePythonLinting') ?? false,
        executable: getGlobalValue<string>(config, 'executable') ?? '',
    };
    return setting;
}

export function checkIfConfigurationChanged(e: ConfigurationChangeEvent, namespace: string): boolean {
    const settings = [
        `${namespace}.args`,
        `${namespace}.config`,
        `${namespace}.disableLinting`,
        `${namespace}.enablePythonLinting`,
        `${namespace}.path`,
        `${namespace}.executable`,
        `${namespace}.interpreter`,
        `${namespace}.importStrategy`,
        `${namespace}.showNotifications`,
    ];
    const changed = settings.map((s) => e.affectsConfiguration(s));
    return changed.includes(true);
}
