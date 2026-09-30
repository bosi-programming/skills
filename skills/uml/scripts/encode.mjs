import { deflateRawSync } from 'node:zlib'

const ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
const COMPRESSION_LEVEL = 9
const SIX_BITS = 0b111111

const encodeGroup = (first, second, third) => {
  const word = (first << 16) | (second << 8) | third
  return [18, 12, 6, 0].map((shift) => ALPHABET[(word >> shift) & SIX_BITS]).join('')
}

export const encodeBase64 = (bytes) => {
  let encoded = ''
  for (let index = 0; index < bytes.length; index += 3) {
    encoded += encodeGroup(bytes[index], bytes[index + 1] ?? 0, bytes[index + 2] ?? 0)
  }
  return encoded
}

export const decodeBase64 = (text) => {
  const bytes = []
  for (let index = 0; index < text.length; index += 4) {
    const word = [...text.slice(index, index + 4)].reduce((sum, char) => (sum << 6) | ALPHABET.indexOf(char), 0)
    bytes.push((word >> 16) & 0xff, (word >> 8) & 0xff, word & 0xff)
  }
  return Buffer.from(bytes)
}

export const encodePlantUml = (source) =>
  encodeBase64(deflateRawSync(Buffer.from(source, 'utf8'), { level: COMPRESSION_LEVEL }))
