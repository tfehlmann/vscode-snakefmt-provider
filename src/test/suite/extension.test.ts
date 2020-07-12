'use strict';

import * as fs from 'fs-extra';
import * as path from 'path';

import * as assert from 'assert';

import * as vscode from 'vscode';
import {SnakemakeDocumentFormattingEditProvider} from '../../extension';

const filesToFormat = ["toFormat1.smk"];

function compareFiles(expectedContent: string, actualContent: string) {
    const expectedLines = expectedContent.split(/\r?\n/);
    const actualLines = actualContent.split(/\r?\n/);

    for (let i = 0; i < Math.min(expectedLines.length, actualLines.length); i += 1) {
        const e = expectedLines[i];
        const a = actualLines[i];
        assert.equal(e, a, `Difference at line ${i}`);
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
	fileToFormat: string
) {
	const textDocument = await vscode.workspace.openTextDocument(fileToFormat);
	const textEditor = await vscode.window.showTextDocument(textDocument);

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
			fs.copySync(path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file), 
						path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file.replace(".smk", "Result.smk")),
						{ overwrite: true });
        });
	});


	suiteTeardown(async () => {
        filesToFormat.forEach((file) => {
            if (fs.existsSync(path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file.replace(".smk", "Result.smk")))) {
                fs.unlinkSync(path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', file.replace(".smk", "Result.smk")));
            }
        });
    });

	test('Default formatting', async () => {
		const fileToFormat = path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', 'toFormat1Result.smk');
		const fileFormatted = path.join(__dirname, '..', '..', '..', 'src', 'test', 'data', 'formatted1.smk');
		
		const formattedContent = fs.readFileSync(fileFormatted).toString();
		await testFormatting(formattedContent, fileToFormat);
	});
});
