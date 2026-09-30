import { createServer } from 'node:http'

import { resolveSource } from './guard.mjs'
import { renderPage } from './page.mjs'

const MAX_BODY_BYTES = 1_048_576
const DIAGRAM_ROUTE = /^\/api\/diagram\/([a-z]+)$/
const LOCAL_HOSTS = ['127.0.0.1', 'localhost']
const JSON_TYPE = 'application/json'

class HttpError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

const send = (response, status, type, body) => {
  response.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' })
  response.end(body)
}

const sendJson = (response, status, value) => send(response, status, `${JSON_TYPE}; charset=utf-8`, JSON.stringify(value))

const isLocalHost = (hostHeader = '') => LOCAL_HOSTS.includes(hostHeader.replace(/:\d+$/, ''))

export const readBody = (request) =>
  new Promise((resolve, reject) => {
    const chunks = []
    let size = 0
    const collect = (chunk) => {
      size += chunk.length
      if (size <= MAX_BODY_BYTES) return chunks.push(chunk)
      request.off('data', collect)
      request.resume()
      chunks.length = 0
      reject(new HttpError(413, 'The source is too large.'))
    }
    request.on('data', collect)
    request.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')))
    request.on('error', reject)
  })

const parseSource = (text) => {
  let value
  try {
    value = JSON.parse(text)
  } catch {
    throw new HttpError(400, 'The body must be JSON.')
  }
  if (typeof value?.source !== 'string') throw new HttpError(400, 'The body must hold a "source" string.')
  return value.source
}

export const createResultCache = ({ outputDir, manifest, render, readFile }) => {
  const results = new Map()

  const drawnDiagrams = () => manifest.diagrams.filter((diagram) => diagram.file && !diagram.noBasis)

  const readSource = async (diagram) => {
    const readable = resolveSource(outputDir, manifest, diagram.type)
    if (readable.error) return { source: '', error: readable.error }
    try {
      return { source: await readFile(readable.path, 'utf8') }
    } catch (error) {
      return { source: '', error: `Could not read ${diagram.file}: ${error.message}` }
    }
  }

  const loadResult = async (diagram) => {
    if (results.has(diagram.type)) return
    const loaded = await readSource(diagram)
    results.set(diagram.type, loaded.error ? loaded : { source: loaded.source, ...(await render(loaded.source, diagram.type)) })
  }

  const all = async () => {
    await Promise.all(drawnDiagrams().map(loadResult))
    return Object.fromEntries(results)
  }

  const remember = (type, source, result) => {
    const lastSvg = results.get(type)?.svg
    results.set(type, result.svg ? { source, svg: result.svg } : { source, svg: lastSvg, error: result.error })
  }

  return { all, remember }
}

export const createSaveRoute = ({ outputDir, manifest, render, writeFile, cache }) => async (request, response, type) => {
  if (!(request.headers['content-type'] ?? '').startsWith(JSON_TYPE)) throw new HttpError(415, `Send the source as ${JSON_TYPE}.`)
  const writable = resolveSource(outputDir, manifest, type)
  if (writable.error) throw new HttpError(403, writable.error)
  const source = parseSource(await readBody(request))
  await writeFile(writable.path, source)
  const result = await render(source, type)
  cache.remember(type, source, result)
  sendJson(response, 200, result)
}

export const createUmlServer = ({ outputDir, manifest, render, readFile, writeFile, smetana, onRequest }) => {
  const cache = createResultCache({ outputDir, manifest, render, readFile })
  const saveDiagram = createSaveRoute({ outputDir, manifest, render, writeFile, cache })

  const servePage = async (response) => {
    const results = await cache.all()
    send(response, 200, 'text/html; charset=utf-8', renderPage({ manifest, results, smetana }))
  }

  const route = async (request, response) => {
    if (!isLocalHost(request.headers.host)) throw new HttpError(403, 'This server only answers on 127.0.0.1.')
    const path = new URL(request.url, 'http://127.0.0.1').pathname
    if (request.method === 'GET' && path === '/') return servePage(response)
    const match = request.method === 'POST' && path.match(DIAGRAM_ROUTE)
    if (match) return saveDiagram(request, response, match[1])
    throw new HttpError(404, 'Not found.')
  }

  return createServer((request, response) => {
    onRequest()
    route(request, response).catch((error) => {
      if (response.headersSent) return response.end()
      sendJson(response, error.status ?? 500, { error: error.message })
    })
  })
}

export const listen = (server, { host }) =>
  new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(0, host, () => {
      const { address, port } = server.address()
      resolve({ host: address, port, url: `http://${address}:${port}` })
    })
  })
