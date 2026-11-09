import {openSync, readSync, closeSync} from 'node:fs';
import {Rejection} from './errors.mjs';
export function readLocal(path, limit) {
  let fd;
  try {
    fd = openSync(path, 'r');
    const bytes = Buffer.alloc(limit + 1);
    let length = 0, count;
    while (length < bytes.length && (count = readSync(fd, bytes, length, bytes.length - length, null))) length += count;
    if (length > limit) throw new Rejection('file_too_large');
    return bytes.subarray(0, length);
  } catch (e) { if (e instanceof Rejection) throw e; throw new Rejection('file_unavailable'); }
  finally { if (fd !== undefined) closeSync(fd); }
}
