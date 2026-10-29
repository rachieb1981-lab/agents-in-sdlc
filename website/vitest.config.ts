import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
  },
  resolve: {
    alias: {
      'astro:content': 'astro/content/config',
      'astro:schema': 'astro/zod',
    },
  },
});
