import { MANIFEST_FILE } from './manifest.mjs'

const REPO_SOURCE = '.'

const reuse = () => ({ sources: 'reuse', reason: null })

const write = (reason) => ({ sources: 'write', reason })

const describeOrigin = ({ origin, source }) =>
  origin === 'description' ? `the description "${source}"` : `the code in ${source}`

const askedOrigin = ({ mode, target }) =>
  mode === 'description' ? { origin: 'description', source: target } : { origin: 'code', source: mode === 'path' ? target : REPO_SOURCE }

const sameOrigin = (wanted, held, resolvePath) => {
  if (wanted.origin !== held.origin) return false
  if (wanted.origin === 'description') return wanted.source === held.source
  return resolvePath(wanted.source) === resolvePath(held.source)
}

const sameDiagrams = (wanted, held) => wanted.length === held.length && wanted.every((type) => held.includes(type))

export const planSources = ({ invocation, manifest, resolvePath }) => {
  if (invocation.regenerate) return write('--regenerate was given.')
  if (manifest.state === 'missing') return write(`${MANIFEST_FILE} is missing.`)
  if (manifest.state !== 'ok') return write(`${MANIFEST_FILE} is unreadable: ${manifest.error}`)
  const held = manifest.manifest.diagrams.map((diagram) => diagram.type)
  if (!sameDiagrams(invocation.diagrams, held)) {
    return write(`${MANIFEST_FILE} holds ${held.join(', ')}, but this run asks for ${invocation.diagrams.join(', ')}.`)
  }
  const wanted = askedOrigin(invocation)
  if (!sameOrigin(wanted, manifest.manifest, resolvePath)) {
    return write(`${MANIFEST_FILE} was drawn from ${describeOrigin(manifest.manifest)}, but this run asks for ${describeOrigin(wanted)}.`)
  }
  return reuse()
}
