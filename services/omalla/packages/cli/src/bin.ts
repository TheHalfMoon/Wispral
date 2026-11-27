#!/usr/bin/env node
import { main } from "./main.js";

main(process.argv.slice(2))
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    process.stderr.write(`omalla: ${(error as Error).message}\n`);
    process.exitCode = 1;
  });
