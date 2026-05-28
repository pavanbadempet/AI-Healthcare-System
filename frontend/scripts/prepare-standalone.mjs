import { cp, mkdir, rm, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, '..');

function resolveInsideProject(relativePath) {
  const target = path.resolve(projectRoot, relativePath);
  const relative = path.relative(projectRoot, target);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error(`Refusing to operate outside the frontend project: ${target}`);
  }
  return target;
}

async function copyIfPresent(sourceRelativePath, destinationRelativePath) {
  const source = resolveInsideProject(sourceRelativePath);
  const destination = resolveInsideProject(destinationRelativePath);

  try {
    await stat(source);
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return;
    }
    throw error;
  }

  await rm(destination, { recursive: true, force: true });
  await mkdir(path.dirname(destination), { recursive: true });
  await cp(source, destination, { recursive: true, force: true });
}

await copyIfPresent('.next/static', '.next/standalone/.next/static');
await copyIfPresent('public', '.next/standalone/public');
