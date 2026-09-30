import { isAbsolute, relative, resolve } from 'node:path'

import { MANIFEST_FILE } from './manifest.mjs'

const SOURCE_EXTENSION = '.puml'

const isInside = (folder, path) => {
  const fromFolder = relative(folder, path)
  return fromFolder !== '' && !fromFolder.startsWith('..') && !isAbsolute(fromFolder)
}

export const resolveWritable = (outputDir, manifest, type) => {
  const diagram = manifest.diagrams.find((entry) => entry.type === type)
  if (!diagram?.file) return { error: `${MANIFEST_FILE} names no file for ${type}.` }
  if (!diagram.file.endsWith(SOURCE_EXTENSION)) return { error: `${type} file ${diagram.file} is not a ${SOURCE_EXTENSION} file.` }
  const folder = resolve(outputDir)
  const path = resolve(folder, diagram.file)
  if (!isInside(folder, path)) return { error: `${type} file ${diagram.file} is outside ${outputDir}.` }
  return { path }
}
