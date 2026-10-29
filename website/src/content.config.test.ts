import { describe, it, expect } from 'vitest';
import { collections } from './content.config';

describe('collections', () => {
  it('defines the docs collection', () => {
    expect(collections.docs).toBeDefined();
  });

  it('configures the glob loader for docs with correct parameters', () => {
    const docCollection = collections.docs;
    expect('loader' in docCollection).toBe(true);
    if ('loader' in docCollection) {
      const loader = docCollection.loader as any;
      expect(loader).toBeDefined();
      expect(loader.name).toBe('glob-loader');
    }
  });

  it('validates valid frontmatter with default starlight fields and without optional authors', () => {
    const docCollection = collections.docs;
    const schemaFn = docCollection.schema;
    expect(schemaFn).toBeDefined();
    if (!schemaFn) return;

    const schema = typeof schemaFn === 'function'
      ? schemaFn({ image: () => {} } as any)
      : schemaFn;

    const validFrontmatter = {
      title: 'Introduction to Copilot',
      description: 'A guide to getting started with Copilot.',
    };

    const result = schema.safeParse(validFrontmatter);
    expect(result.success).toBe(true);
  });

  it('validates valid frontmatter with optional authors array', () => {
    const docCollection = collections.docs;
    const schemaFn = docCollection.schema;
    expect(schemaFn).toBeDefined();
    if (!schemaFn) return;

    const schema = typeof schemaFn === 'function'
      ? schemaFn({ image: () => {} } as any)
      : schemaFn;

    const validFrontmatterWithAuthors = {
      title: 'Advanced Agentic Workflows',
      authors: ['Alice Developer', 'Bob Architect'],
    };

    const result = schema.safeParse(validFrontmatterWithAuthors);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.authors).toEqual(['Alice Developer', 'Bob Architect']);
    }
  });

  it('fails validation when authors is not an array of strings', () => {
    const docCollection = collections.docs;
    const schemaFn = docCollection.schema;
    expect(schemaFn).toBeDefined();
    if (!schemaFn) return;

    const schema = typeof schemaFn === 'function'
      ? schemaFn({ image: () => {} } as any)
      : schemaFn;

    const invalidFrontmatter = {
      title: 'Invalid Authors Field',
      authors: 'Single Author Name',
    };

    const result = schema.safeParse(invalidFrontmatter);
    expect(result.success).toBe(false);
  });
});
