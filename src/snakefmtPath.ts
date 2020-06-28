'use strict';

import fs = require('fs');
import path = require('path');

let binPathCache: { [bin: string]: string } = {};

export function getBinPath(binname: string) {
  if (binPathCache[binname]) {
    return binPathCache[binname];
  }

  // snakefmt.executable has a valid absolute path
  if (fs.existsSync(binname)) {
      binPathCache[binname] = binname;
      return binname;
  }

  if (process.env['PATH']) {
      let pathparts = process.env['PATH'].split(path.delimiter);
      for (let i = 0; i < pathparts.length; i++) {
        let binpath = path.join(pathparts[i], binname);
        if (fs.existsSync(binpath)) {
            binPathCache[binname] = binpath;
            return binpath;
        }
      }
  }

  // Else return the binary name directly (this will likely always fail downstream)
  binPathCache[binname] = binname;
  return binname;
}
