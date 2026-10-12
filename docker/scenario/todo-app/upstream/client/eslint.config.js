import js from '@eslint/js';
import globals from 'globals';
import reactX from 'eslint-plugin-react-x';
import hooks from 'eslint-plugin-react-hooks';
import refresh from 'eslint-plugin-react-refresh';

export default [
    { ignores: ['dist/**', 'node_modules/**', '.eslintrc.cjs'] },
    {
        files: ['**/*.{js,jsx}'],
        ...js.configs.recommended,
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            globals: globals.browser,
            parserOptions: { ecmaFeatures: { jsx: true } },
        },
        plugins: { 'react-x': reactX, 'react-hooks': hooks, 'react-refresh': refresh },
        rules: {
            ...reactX.configs.recommended.rules,
            'react-hooks/rules-of-hooks': 'error',
            'react-hooks/exhaustive-deps': 'error',
            'react-refresh/only-export-components': ['error', { allowConstantExport: true }],
        },
    },
    { files: ['**/*.test.jsx'], rules: { 'react-refresh/only-export-components': 'off' } },
];
