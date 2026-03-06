import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
    { ignores: ['out/**', 'dist/**', '**/*.d.ts'] },
    eslint.configs.recommended,
    ...tseslint.configs.recommended,
    {
        rules: {
            '@typescript-eslint/naming-convention': 'warn',
            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/no-unused-vars': 'warn',
            curly: 'warn',
            eqeqeq: 'warn',
            'no-throw-literal': 'warn',
        },
    },
];
