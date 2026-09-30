import { ALPHABET } from './encode.mjs'

export const decodeBase64 = (text) => {
  const bytes = []
  for (let index = 0; index < text.length; index += 4) {
    const word = [...text.slice(index, index + 4)].reduce((sum, char) => (sum << 6) | ALPHABET.indexOf(char), 0)
    bytes.push((word >> 16) & 0xff, (word >> 8) & 0xff, word & 0xff)
  }
  return Buffer.from(bytes)
}
