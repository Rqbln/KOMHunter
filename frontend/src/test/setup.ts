/**
 * Bun test preload: register happy-dom globals (window, document,
 * localStorage, ...) so browser-dependent code runs under `bun test`.
 */

import { GlobalRegistrator } from "@happy-dom/global-registrator";

GlobalRegistrator.register();
