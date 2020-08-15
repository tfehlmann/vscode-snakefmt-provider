'use strict';

import * as fs from 'fs-extra';
import * as path from 'path';

import * as assert from 'assert';

import * as vscode from 'vscode';
import {SnakemakeDocumentFormattingEditProvider} from '../../extension';

const filesToFormat = [
	{input: "toFormat1.smk", output: "formatted1.smk", config: "", name: "Formatting without config file"},
	{input: "toFormat2.smk", output: "formatted2.smk", config: "config.toml", name: "Formatting with custom config file"},
	{input: "toFormat3.smk", output: "formatted3.smk", config: "pyproject.toml", name: "Formatting with default config file"},
];

function compareFiles(expectedContent: string, actualContent: string) {
    const expectedLines = expectedContent.split(/\r?\n/);
    const actualLines = actualContent.split(/\r?\n/);

    for (let i = 0; i < Math.min(expectedLines.length, actualLines.length); i += 1) {
        const e = expectedLines[i];
        const a = actualLines[i];
        assert.equal(a, e, `Difference at line ${i+1}`);
    }

    assert.equal(
		actualLines.length,
		expectedLines.length,
        expectedLines.length > actualLines.length
            ? 'Actual contains more lines than expected'
            : 'Expected contains more lines than the actual'
    );
}

async function testFormatting(
	formattedContents: string,
	fileToFormat: string,
	configFile: string | null
) {
	const textDocument = await vscode.workspace.openTextDocument(fileToFormat);
	const textEditor = await vscode.window.showTextDocument(textDocument);
	const settings =  vscode.workspace.getConfiguration("snakefmt")
	vscode.workspace.updateWorkspaceFolders(0, 0, {uri: vscode.Uri.file(path.dirname(fileToFormat))})
	await settings.update("config", configFile, vscode.ConfigurationTarget.Global)
	
	const edits = await new SnakemakeDocumentFormattingEditProvider().formatDocument(textDocument);
	await textEditor.edit((editBuilder) => {
		edits.forEach((edit) => editBuilder.replace(edit.range, edit.newText));
	});
	compareFiles(formattedContents, textEditor.document.getText());
}

suite('Extension Test Suite', () => {
	vscode.window.showInformationMessage('Start all tests.');

	suiteSetup(async function () {
		filesToFormat.forEach((file) => {
			fs.copySync(path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file.input), 
						path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file.input.replace(".smk", "Result.smk")),
						{ overwrite: true });
        });
	});


	suiteTeardown(async () => {
        filesToFormat.forEach((file) => {
			if (fs.existsSync(path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file.input.replace(".smk", "Result.smk")))) {
				fs.unlinkSync(path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file.input.replace(".smk", "Result.smk")));
			}
        });
    });

	for(let e of filesToFormat){
		test(e.name, async () => {
			const fileToFormat = path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', e.input.replace(".smk", "Result.smk"));
			const fileFormatted = path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', e.output);
			
			const formattedContent = fs.readFileSync(fileFormatted).toString();
			await testFormatting(formattedContent, fileToFormat, e.config ? path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', e.config): null);
		});
	}
});
