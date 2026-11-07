import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import globals from 'globals';

export default tseslint.config(
  {
    ignores: ['dist/**', 'dist-electron/**', 'release/**', 'node_modules/**', 'screen/**', 'TGBot/**', 'Mod/**']
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      globals: { ...globals.browser },
      parserOptions: { ecmaVersion: 2022, sourceType: 'module' }
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }
      ],
      'no-empty': ['error', { allowEmptyCatch: true }]
    }
  },
  {
    files: ['electron/**/*.ts', 'tests/**/*.ts', 'vite.config.ts'],
    languageOptions: {
      globals: { ...globals.node },
      parserOptions: { ecmaVersion: 2022, sourceType: 'module' }
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }
      ],
      'no-empty': ['error', { allowEmptyCatch: true }]
    }
  },
  {
    files: ['eslint.config.mjs'],
    languageOptions: { globals: { ...globals.node } }
  }
);
