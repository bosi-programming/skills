import { encodePlantUml } from './encode.mjs'
import { LOCAL_SERVER, chooseLayout } from './layout.mjs'
import { injectTheme } from './theme.mjs'

export const NO_JAVA =
  'Java was not found. uml.plantumlServer is local, which renders through the PlantUML jar and needs a Java runtime. Install Java, or set uml.plantumlServer to the URL of a PlantUML server.'

export const MISSING_JAR =
  'The PlantUML jar was not found. Run download-jar to fetch it, or set uml.plantumlJar to its path.'

const RENDER_FAILED = 'PlantUML could not render this diagram'
const SVG_START = '<svg'

const stripProlog = (svg) => {
  const start = svg.indexOf(SVG_START)
  return start === -1 ? svg : svg.slice(start)
}

const ENTITIES = Object.freeze({ '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&apos;': "'", '&amp;': '&' })

const decodeEntities = (text) => text.replace(/&(lt|gt|quot|#39|apos|amp);/g, (entity) => ENTITIES[entity])

const ERROR_LINE = /error/i

const svgTexts = (svg) =>
  [...svg.matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map((match) => decodeEntities(match[1]).trim()).filter(Boolean)

const svgText = (svg) => {
  const texts = svgTexts(svg)
  const errorAt = texts.findLastIndex((text) => ERROR_LINE.test(text))
  if (errorAt === -1) return texts.at(-1) ?? ''
  const offending = texts[errorAt - 1]
  return offending ? `${texts[errorAt]} at "${offending}"` : texts[errorAt]
}

const failure = (detail) => ({ error: detail ? `${RENDER_FAILED}: ${detail}` : `${RENDER_FAILED}.` })

const collect = (stream) => {
  const chunks = []
  stream.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
  return () => Buffer.concat(chunks).toString('utf8')
}

const javaArgs = (jar, dotPath) => [
  '-jar',
  jar,
  '-tsvg',
  '-pipe',
  '-charset',
  'UTF-8',
  ...(dotPath ? ['-graphvizdot', dotPath] : []),
]

export const renderLocal = (source, { jar, dotPath, spawn }) => {
  if (!jar) return Promise.resolve({ error: MISSING_JAR })
  return new Promise((resolve) => {
    const child = spawn('java', javaArgs(jar, dotPath))
    const stdout = collect(child.stdout)
    const stderr = collect(child.stderr)
    child.on('error', (error) => resolve(error.code === 'ENOENT' ? { error: NO_JAVA } : failure(error.message)))
    child.on('close', (code) => {
      if (code === 0) return resolve({ svg: stripProlog(stdout()) })
      resolve(failure(stderr().trim() || svgText(stdout())))
    })
    child.stdin.end(source)
  })
}

const serverUrl = (server, source) => `${server.replace(/\/+$/, '')}/svg/${encodePlantUml(source)}`

export const renderRemote = async (source, { server, fetch }) => {
  let response
  try {
    response = await fetch(serverUrl(server, source))
  } catch (error) {
    return {
      error: `Could not reach the PlantUML server at ${server} (${error.message}). Check the URL in uml.plantumlServer, or set it to local.`,
    }
  }
  const body = await response.text()
  if (!response.ok) return failure(svgText(body) || `HTTP ${response.status}`)
  return { svg: stripProlog(body) }
}

export const createRenderer = ({ server, jar, dotPath, spawn, fetch }) => {
  const smetana = chooseLayout({ dotPath, server }) === 'smetana'
  return (source, type) => {
    const themed = injectTheme(source, type, { smetana })
    if (server === LOCAL_SERVER) return renderLocal(themed, { jar, dotPath, spawn })
    return renderRemote(themed, { server, fetch })
  }
}
