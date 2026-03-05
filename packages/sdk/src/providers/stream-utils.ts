/**
 * Reads a ReadableStream<Uint8Array> line-by-line.
 * Handles partial chunks and trailing newlines.
 */
export async function* readLines(
  body: ReadableStream<Uint8Array>,
): AsyncIterable<string> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (line.trim().length > 0) {
          yield line;
        }
      }
    }

    if (buffer.trim().length > 0) {
      yield buffer;
    }
  } finally {
    reader.releaseLock();
  }
}
